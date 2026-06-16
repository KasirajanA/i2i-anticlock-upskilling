from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class WidgetItem(BaseModel):
    key: str
    label: str
    value: float | int
    unit: str | None = None


class DashboardResponse(BaseModel):
    widgets: list[WidgetItem]
    generated_at: datetime


class StageBreakdownItem(BaseModel):
    stage: str
    count: int
    total_value: Decimal


class RepRevenue(BaseModel):
    owner_id: int
    owner_name: str
    revenue: Decimal


class SalesReportResponse(BaseModel):
    stage_breakdown: list[StageBreakdownItem]
    won_count: int
    lost_count: int
    avg_deal_value: Decimal | None
    top_reps: list[RepRevenue]
    filters_applied: ReportFiltersApplied
    cached_until: datetime | None = None


class StatusBreakdownItem(BaseModel):
    status: str
    count: int


class PriorityBreakdownItem(BaseModel):
    priority: str
    count: int


class PerAgentCount(BaseModel):
    assignee_id: int | None
    assignee_name: str
    count: int


class SupportReportResponse(BaseModel):
    status_breakdown: list[StatusBreakdownItem]
    priority_breakdown: list[PriorityBreakdownItem]
    avg_resolution_hours: float | None
    sla_breach_rate: float | None
    per_agent: list[PerAgentCount]
    filters_applied: ReportFiltersApplied
    cached_until: datetime | None = None


class StatusValueItem(BaseModel):
    status: str
    count: int
    total_value: Decimal


class UpcomingRenewal(BaseModel):
    contract_id: int
    ref_id: str
    account_name: str
    value: Decimal
    expiry_date: date
    days_remaining: int


class AccountValue(BaseModel):
    account_id: int | None
    account_name: str
    total_value: Decimal


class ContractReportResponse(BaseModel):
    status_breakdown: list[StatusValueItem]
    upcoming_renewals: list[UpcomingRenewal]
    value_by_account: list[AccountValue]
    filters_applied: ReportFiltersApplied
    cached_until: datetime | None = None


class ReportFiltersApplied(BaseModel):
    created_after: date | None = None
    created_before: date | None = None
    owner_id: int | None = None
    assignee_id: int | None = None
    renewal_window: int | None = None
