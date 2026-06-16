"""Pydantic v2 schemas for the pipeline forecast endpoint."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.deal import DealStage


class ForecastPeriod(BaseModel):
    start: date
    end: date


class StageTotal(BaseModel):
    stage: DealStage
    deal_count: int
    total_value: Decimal
    probability: float
    weighted_value: Decimal


class ClosedWonTotal(BaseModel):
    deal_count: int
    total_value: Decimal


class ForecastResponse(BaseModel):
    period: ForecastPeriod
    open_pipeline: list[StageTotal]
    closed_won: ClosedWonTotal
    total_weighted_forecast: Decimal
