"""Pydantic v2 schemas for deal comments."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.deal import UserRef


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)

    @field_validator("body")
    @classmethod
    def body_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Comment body cannot be empty or whitespace")
        return v


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author: UserRef
    body: str
    created_at: datetime


class CommentListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[CommentRead]
