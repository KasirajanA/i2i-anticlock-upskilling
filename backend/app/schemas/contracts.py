from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.contracts import ContractStatus


class ContractCreate(BaseModel):
    value: Decimal = Field(gt=0, decimal_places=2)
    start_date: date
    end_date: date
    description: str | None = None
    account_id: int
    deal_id: int | None = None
    # Admins/Managers may supply an explicit owner; defaults to current user
    owner_id: int | None = None

    @model_validator(mode="after")
    def _dates_in_order(self) -> "ContractCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ContractUpdate(BaseModel):
    value: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    deal_id: int | None = None

    @model_validator(mode="after")
    def _dates_in_order(self) -> "ContractUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref_id: str
    value: Decimal
    start_date: date
    end_date: date
    status: ContractStatus
    description: str | None
    is_renewal_due: bool
    is_archived: bool
    owner_id: int
    account_id: int
    deal_id: int | None
    created_at: datetime
    updated_at: datetime
    attachment: AttachmentResponse | None = None


class ContractListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref_id: str
    value: Decimal
    start_date: date
    end_date: date
    status: ContractStatus
    is_renewal_due: bool
    is_archived: bool
    owner_id: int
    account_id: int
    deal_id: int | None
    created_at: datetime
    updated_at: datetime


class ContractListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[ContractListItem]


class TransitionRequest(BaseModel):
    status: ContractStatus
    note: str | None = None

    @field_validator("note")
    @classmethod
    def _strip_note(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class TransitionResponse(BaseModel):
    ref_id: str
    previous_status: ContractStatus
    new_status: ContractStatus
    logged_at: datetime


class ActivityLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    actor_id: int
    actor_name: str
    note: str | None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    ref_id: str
    logs: list[ActivityLogEntry]


class RenewResponse(BaseModel):
    original_ref_id: str
    successor: ContractResponse


class ContractFilterParams(BaseModel):
    status: ContractStatus | None = None
    owner_id: int | None = Field(default=None, alias="owner")
    account_id: int | None = None
    end_date_from: date | None = None
    end_date_to: date | None = None
    is_renewal_due: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _date_range_order(self) -> "ContractFilterParams":
        if (
            self.end_date_from
            and self.end_date_to
            and self.end_date_to < self.end_date_from
        ):
            raise ValueError("end_date_to must be on or after end_date_from")
        return self
