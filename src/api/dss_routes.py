from datetime import date

from fastapi import APIRouter, HTTPException, Query

from src.dss import evidence, service
from src.dss.models import AllocationRequest, SensitivityRequest, ShelfRequest, WhatIfRequest
from src.dss.scoring import score_profile
from .db import snapshot
from .models import Store

router = APIRouter(prefix='/api/v1/dss', tags=['DSS'])


def execute(function, request):
    try:
        with snapshot() as connection:
            data = function(connection, request)
        from .app import envelope
        return envelope(data, warnings=evidence.WARNINGS)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    except RuntimeError:
        raise HTTPException(503, 'Solver could not certify an optimum within the runtime limit') from None


@router.post('/allocate')
def allocate(request: AllocationRequest):
    return execute(lambda c, r: service.allocate(c, r, r.scenario), request)


@router.post('/shelf-life')
def shelf_life(request: ShelfRequest):
    return execute(service.shelf_life, request)


@router.post('/what-if')
def what_if(request: WhatIfRequest):
    return execute(service.what_if, request)


@router.post('/sensitivity')
def sensitivity(request: SensitivityRequest):
    return execute(service.what_if, request)


@router.get('/risk')
def risk(store: Store, as_of: date, history_start: date | None = None,
         late_threshold_days: float = Query(5, gt=0, le=365),
         low_star_max: int = Query(2, ge=1, le=3),
         limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0, le=100000)):
    if history_start and history_start > as_of:
        raise HTTPException(422, 'history_start must be <= as_of')
    from src.dss.models import RiskWeights
    from .app import envelope
    with snapshot() as c:
        profiles = evidence.profiles(c, store, as_of, history_start, late_threshold_days, low_star_max)
        rows = [{**profile, **score_profile(profile, profiles.get((key, None)), RiskWeights(), 20)}
                for (key, province),profile in profiles.items() if province is not None]
    rows.sort(key=lambda r: (-(r['risk_score'] if r['risk_score'] is not None else -1), r['warehouse_key'], r['route_province']))
    return envelope(rows[offset:offset+limit], total_groups=len(rows), limit=limit, offset=offset, warnings=evidence.WARNINGS)
