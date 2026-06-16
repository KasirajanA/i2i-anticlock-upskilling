"""Pydantic v2 schemas for the Sales Pipeline deal endpoints."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal import DealStage


class UserRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class AccountRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_archived: bool


class ContactRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class DealCreate(BaseModel):
    title: str = Field(min_length=1)
    value: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    stage: DealStage = DealStage.LEAD_IN
    expected_close_date: date
    owner_id: int
    account_id: int
    contact_id: int | None = None


class DealUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1)
    value: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    expected_close_date: date | None = None
    owner_id: int | None = None
    account_id: int | None = None
    contact_id: int | None = None


class DealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ref_id: str
    title: str
    value: Decimal
    stage: DealStage
    expected_close_date: date
    loss_reason: str | None
    is_overdue: bool
    is_archived: bool
    owner: UserRef
    account: AccountRef | None
    contact: ContactRef | None
    created_at: datetime
    updated_at: datetime


class DealSummary(BaseModel):
    """Lightweight read model for list views — same fields as DealRead."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    ref_id: str
    title: str
    value: Decimal
    stage: DealStage
    expected_close_date: date
    is_overdue: bool
    is_archived: bool
    owner: UserRef
    account: AccountRef | None
    contact: ContactRef | None
    created_at: datetime
    updated_at: datetime


class DealListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[DealSummary]


class DealFilterParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    stage: DealStage | None = None
    owner_id: int | None = Field(default=None, alias="owner")
    account_id: int | None = None
    is_overdue: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=25, ge=1, le=100)


class StageChangeRequest(BaseModel):
    stage: DealStage
    loss_reason: str | None = None


class StageChangeResponse(BaseModel):
    ref_id: str
    previous_stage: DealStage
    new_stage: DealStage
    is_overdue: bool
    updated_at: datetime
