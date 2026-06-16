from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.schemas.auth import CreateUserRequest, ResetPasswordRequest, UserResponse
from app.services.user_admin_service import UserAdminService

router = APIRouter(prefix="/auth", tags=["auth-admin"])

_require_admin = require_roles("Admin")


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    svc = UserAdminService(session)
    user = await svc.create_user(
        email=payload.email,
        password=payload.password,
        role=payload.role,
        name=payload.name,
    )
    return UserResponse.model_validate(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[UserResponse]:
    svc = UserAdminService(session)
    users = await svc.list_users()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = UserAdminService(session)
    await svc.reset_password(user_id, payload.new_password)


@router.post("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = UserAdminService(session)
    await svc.deactivate_user(user_id)


@router.post("/users/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_user(
    user_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = UserAdminService(session)
    await svc.unlock_user(user_id)
