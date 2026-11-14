from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal['Bánh', 'Kẹo', 'Ngũ cốc', 'Quà tặng']
Status = Literal['COMPLETED', 'DELIVERED', 'CANCELED', 'PROCESSING', 'UNPAID', 'RETURNED', 'UNKNOWN']
Store = Literal['bibica_official_store', 'quasure_specialized_store', 'bibica_tiktok_shop']


class Filters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start_date: date | None = None
    end_date: date | None = None
    source: Literal['shopee_bibica', 'shopee_quasure', 'tiktok_bibica'] | None = None
    store: Store | None = None
    channel: Literal['SHOPEE', 'TIKTOK'] | None = None
    category: Category | None = None
    warehouse_key: int | None = Field(default=None, gt=0)
    warehouse_region: Literal['Hà Nội', 'Hồ Chí Minh'] | None = None
    province: str | None = Field(default=None, min_length=1, max_length=80)
    product_key: int | None = Field(default=None, gt=0)
    status: Status | None = None

    @model_validator(mode='after')
    def ordered_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError('start_date must be <= end_date')
        return self


class PageFilters(Filters):
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0, le=100000)


class ProductFilters(PageFilters):
    search: str = Field('', max_length=150)
    sort: Literal['key', 'orders', 'units', 'item_value'] = 'key'
