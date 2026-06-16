"""Pydantic v2 schemas for the deal activity log."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.deal import UserRef


class ActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action_type: str
    actor: UserRef
    note: str | None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    total: int
    items: list[ActivityLogRead]
