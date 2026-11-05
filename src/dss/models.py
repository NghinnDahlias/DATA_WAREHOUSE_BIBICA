from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from DW.etl.geography import normalize_province
from src.api.models import Store


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Item(Input):
    product_key: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100000)


class Demand(Input):
    order_ref: str = Field(pattern=r'^[A-Za-z][A-Za-z0-9_-]{0,39}$')
    province: str = Field(min_length=1, max_length=80)
    items: list[Item] = Field(min_length=1, max_length=20)

    @model_validator(mode='after')
    def canonical_inputs(self):
        self.province = normalize_province(self.province)['customer_province']
        if self.province == 'Unknown':
            raise ValueError('Province must be recognized by the observed spelling dictionary')
        if len({i.product_key for i in self.items}) != len(self.items):
            raise ValueError('Combine repeated product keys within an order')
        return self


class Stock(Input):
    warehouse_key: int = Field(gt=0)
    product_key: int = Field(gt=0)
    units: int = Field(ge=0, le=10000000)
    remaining_shelf_days: float | None = Field(default=None, ge=0, le=3650)
    stock_scope: Literal['ECOMMERCE', 'WHOLESALE', 'UNVERIFIED'] = 'UNVERIFIED'


class BreakfastException(Input):
    warehouse_key: int = Field(gt=0)
    product_key: int = Field(gt=0)
    reason: Literal['HN_STOCKOUT_TRANSFER', 'APPROVED_ECOMMERCE_EXCEPTION']
    evidence_ref: str = Field(min_length=3, max_length=120, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]+$')
    ecommerce_stock_confirmed: Literal[True]


class RiskWeights(Input):
    cancellation: float = Field(.4, ge=0, le=1)
    late_delivery: float = Field(.4, ge=0, le=1)
    low_review: float = Field(.2, ge=0, le=1)

    @model_validator(mode='after')
    def nonzero_weights(self):
        if self.cancellation + self.late_delivery + self.low_review <= 0:
            raise ValueError('At least one risk weight must be positive')
        return self


class Scenario(Input):
    label: str = Field('Kịch bản', min_length=1, max_length=80)
    stock_mode: Literal['required', 'assume_available'] = 'required'
    stocks: list[Stock] = Field(default_factory=list, max_length=2000)
    capacity_orders: dict[int, int] = Field(default_factory=dict)
    extra_delay_days: dict[int, float] = Field(default_factory=dict)
    max_delivery_days: float = Field(7, gt=0, le=365)
    late_threshold_days: float = Field(5, gt=0, le=365)
    min_remaining_days: float = Field(1, ge=0, le=365)
    max_risk_score: float = Field(100, ge=0, le=100)
    min_route_samples: int = Field(20, ge=1, le=10000)
    prior_strength: float = Field(20, ge=0, le=10000)
    risk_weight: float = Field(.7, ge=0, le=1)
    risk_weights: RiskWeights = Field(default_factory=RiskWeights)
    low_star_max: int = Field(2, ge=1, le=3)
    breakfast_exceptions: list[BreakfastException] = Field(default_factory=list, max_length=1000)
    breakfast_product_keys: list[int] = Field(default_factory=list, max_length=1000)

    @model_validator(mode='after')
    def resource_limits(self):
        pairs = [(s.warehouse_key, s.product_key) for s in self.stocks]
        if len(pairs) != len(set(pairs)):
            raise ValueError('One stock scenario per warehouse/product pair')
        if any(k <= 0 or v < 0 or v > 100000 for k, v in self.capacity_orders.items()):
            raise ValueError('Warehouse capacity must be a nonnegative order count')
        if any(k <= 0 or v < 0 or v > 90 for k, v in self.extra_delay_days.items()):
            raise ValueError('Scenario delay must be in [0,90] days')
        pairs = [(e.warehouse_key, e.product_key) for e in self.breakfast_exceptions]
        if len(pairs) != len(set(pairs)):
            raise ValueError('One breakfast exception per warehouse/product pair')
        if any(k <= 0 for k in self.breakfast_product_keys) or len(set(self.breakfast_product_keys)) != len(self.breakfast_product_keys):
            raise ValueError('Breakfast product keys must be unique positive keys')
        return self


class DecisionCohort(Input):
    store: Store
    as_of: date
    history_start: date | None = None
    orders: list[Demand] = Field(min_length=1, max_length=50)

    @model_validator(mode='after')
    def unique_requests(self):
        if self.history_start and self.history_start > self.as_of:
            raise ValueError('history_start must be <= as_of')
        if len({o.order_ref for o in self.orders}) != len(self.orders):
            raise ValueError('order_ref must be unique within the batch')
        return self


class AllocationRequest(DecisionCohort):
    scenario: Scenario = Field(default_factory=Scenario)


class WhatIfRequest(DecisionCohort):
    baseline: Scenario = Field(default_factory=Scenario)
    alternative: Scenario


class SensitivityRequest(DecisionCohort):
    baseline: Scenario = Field(default_factory=Scenario)
    alternatives: list[Scenario] = Field(min_length=1, max_length=8)


class ShelfRequest(Input):
    store: Store
    product_key: int = Field(gt=0)
    warehouse_key: int = Field(gt=0)
    province: str = Field(min_length=1, max_length=80)
    as_of: date
    remaining_shelf_days: float = Field(ge=0, le=3650)
    min_remaining_days: float = Field(1, ge=0, le=365)
    extra_delay_days: float = Field(0, ge=0, le=90)
    min_route_samples: int = Field(20, ge=1, le=10000)
