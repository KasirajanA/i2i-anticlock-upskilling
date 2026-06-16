from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool
    display_name: str | None = None
    avatar_url: str | None = None
    timezone: str | None = "UTC"
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    role: str
    password: str = Field(min_length=8)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"Admin", "Manager", "Sales Rep", "Support Agent"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {sorted(allowed)}")
        return v


class UpdateUserRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"Admin", "Manager", "Sales Rep", "Support Agent"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {sorted(allowed)}")
        return v


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    joined_at: datetime


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    lead_user_id: int | None
    created_by_id: int
    created_at: datetime
    member_count: int = 0


class TeamDetailResponse(TeamResponse):
    members: list[TeamMemberResponse] = []


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    lead_user_id: int | None = None
    member_ids: list[int] = Field(default_factory=list)


class UpdateTeamRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    lead_user_id: int | None = None


class AddMembersRequest(BaseModel):
    user_ids: list[int] = Field(min_length=1)


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    total: int


class PaginatedTeams(BaseModel):
    items: list[TeamResponse]
    total: int
