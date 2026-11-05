"""Run with python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001."""
from decimal import Decimal
from typing import Annotated, Literal

import psycopg
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .db import snapshot
from .kpi_contract import VERSION, contract
from .models import Filters, PageFilters, ProductFilters
from . import repository

app = FastAPI(title='Bibica DW & DSS API', version='2.0.0', description='Galaxy PostgreSQL riêng của repo. Tiền VND, giờ Việt Nam.')
FilterQuery = Annotated[Filters, Query()]


def envelope(data, **meta):
    return jsonable_encoder({'data': data, 'meta': {'kpi_contract': VERSION, 'timezone': 'Asia/Ho_Chi_Minh',
        'money_encoding': 'decimal string VND', **meta}}, custom_encoder={Decimal: str})


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    # Do not echo arbitrary request values (which may contain private text).
    return JSONResponse(status_code=422, content={'detail': [{'loc': list(e['loc']), 'type': e['type']} for e in exc.errors()]})


@app.exception_handler(psycopg.Error)
async def unavailable(request: Request, exc: psycopg.Error):
    return JSONResponse(status_code=503, content={'detail': 'Database unavailable, busy or schema not initialized'})


@app.get('/health')
def health():
    with snapshot() as c:
        row = c.execute("SELECT current_database() database,to_regclass('analytics.v_orders') IS NOT NULL ready").fetchone()
    if not row['ready']:
        raise HTTPException(503, 'Run repository ETL or scripts/migrate_api.py first')
    return envelope(row)


@app.get('/api/v1/kpi-contract')
def kpi_contract():
    return envelope(contract())


@app.get('/api/v1/meta')
def meta():
    with snapshot() as c:
        return envelope(repository.metadata(c), warnings=['Ngày quan sát không chứng minh xuất đủ ngày.',
            'Kho scoped theo shop. Tỉnh khách độc lập. Không suy sáp nhập hành chính.'])


@app.get('/api/v1/overview/kpis')
def kpis(filters: FilterQuery):
    with snapshot() as c:
        data = repository.kpis(c, filters)
    shopee_only = filters.source in ['shopee_bibica','shopee_quasure'] or filters.store in ['bibica_official_store','quasure_specialized_store']
    return envelope(data, filters=filters.model_dump(mode='json'), warnings=contract()['policies'],
        metric_availability={'review_metrics': 'UNAVAILABLE_NO_SHOPEE_RATING_SOURCE' if shopee_only else 'TIKTOK_OBSERVED_REVIEWS_ONLY',
                             'zero_observed_review_count_does_not_mean_zero_complaints':True})


@app.get('/api/v1/analytics/{dimension}')
def analytics(dimension: Literal['source', 'store', 'status', 'month', 'category', 'province', 'warehouse', 'warehouse_region', 'product'],
              filters: Annotated[PageFilters, Query()]):
    with snapshot() as c:
        rows = repository.breakdown(c, filters, dimension, filters.limit, filters.offset)
    return envelope(rows, dimension=dimension, grain=repository.BREAKDOWNS[dimension][0], limit=filters.limit, offset=filters.offset,
        warnings=['Distinct orders giữa category/kho/SKU có thể chồng lấp. Không cộng các nhóm.',
                  'Giá trị item khác tiền đơn. Không phân bổ order payable cho kho/category.'])


@app.get('/api/v1/products')
def products(filters: Annotated[ProductFilters, Query()]):
    with snapshot() as c:
        rows = repository.products(c, filters, filters.limit, filters.offset, filters.search)
    return envelope(rows, limit=filters.limit, offset=filters.offset)


@app.get('/api/v1/quality')
def quality():
    with snapshot() as c:
        data = {
            'sources': c.execute('SELECT source_code,sha256,parser_version,row_count FROM ops.source_current ORDER BY 1').fetchall(),
            'quarantine': c.execute('SELECT source_code,reason,count(*) records FROM ops.quarantine GROUP BY 1,2 ORDER BY 1,2').fetchall(),
            'last_run': c.execute('SELECT status,started_at,ended_at,counts FROM ops.etl_run ORDER BY started_at DESC LIMIT 1').fetchone(),
        }
    return envelope(data)


@app.get('/api/v1/operations/delivery')
def delivery(filters: FilterQuery):
    with snapshot() as c:
        rows = repository.delivery(c, filters)
    return envelope(rows, warnings=['Shopee completion time là proxy. TikTok Delivered Time là ghi nhận giao. Không gộp các nguồn thành SLA vận chuyển.'])


from .dss_routes import router as dss_router
app.include_router(dss_router)
