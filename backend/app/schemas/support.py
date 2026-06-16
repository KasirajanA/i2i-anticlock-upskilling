"""Pydantic v2 schemas for the Customer Support module."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class UserRef(BaseModel):
    id: int
    display_name: str


class SLARecordRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    cycle: int
    first_response_due: datetime
    resolution_due: datetime
    first_response_at: datetime | None
    resolved_at: datetime | None
    first_response_breached: bool
    resolution_breached: bool
    is_active: bool


class SLASummary(BaseModel):
    """Compact SLA info embedded in ticket list items."""

    first_response_due: datetime
    resolution_due: datetime
    first_response_breached: bool
    resolution_breached: bool
    warning: bool


class TicketCreate(BaseModel):
    model_config = {"extra": "forbid"}

    subject: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str
    contact_id: int
    assignee_id: int | None = None

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v


class TicketUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    status: str | None = None
    priority: str | None = None
    assignee_id: int | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class AssignRequest(BaseModel):
    assignee_id: int


class TicketRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ref: str
    subject: str
    description: str | None
    status: str
    priority: str
    contact_id: int | None
    contact_name_snapshot: str
    account_id: int | None
    assignee_id: int | None
    created_by_id: int
    sla: SLARecordRead | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_ref(cls, ticket: Any, sla: Any | None = None) -> "TicketRead":
        data = {
            "id": ticket.id,
            "ref": f"I2I-CRM-{ticket.seq_number:04d}",
            "subject": ticket.subject,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "contact_id": ticket.contact_id,
            "contact_name_snapshot": ticket.contact_name_snapshot,
            "account_id": ticket.account_id,
            "assignee_id": ticket.assignee_id,
            "created_by_id": ticket.created_by_id,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "sla": SLARecordRead.model_validate(sla) if sla else None,
        }
        return cls(**data)


class TicketSummary(BaseModel):
    """Lightweight item for list responses."""

    id: int
    ref: str
    subject: str
    status: str
    priority: str
    contact_name: str
    assignee_id: int | None
    sla: SLASummary | None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketSummary]
    next_cursor: str | None
    total: int


class ReplyCreate(BaseModel):
    model_config = {"extra": "forbid"}

    body: str = Field(min_length=1, max_length=10_000)
    is_internal: bool = False

    @field_validator("body")
    @classmethod
    def _strip_body(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("body must not be blank")
        return stripped


class ReplyRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ticket_id: int
    author_id: int
    body: str
    is_internal: bool
    created_at: datetime


class ReplyListResponse(BaseModel):
    items: list[ReplyRead]


class ActivityLogRead(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: int
    event_type: str
    actor_id: int | None
    event_metadata: dict[str, Any] | None = None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    items: list[ActivityLogRead]


class SLAListResponse(BaseModel):
    items: list[SLARecordRead]
