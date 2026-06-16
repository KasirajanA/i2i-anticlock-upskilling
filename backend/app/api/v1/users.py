from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.dependencies.role_guard import require_module_access
from app.models.base import User
from app.schemas.user_mgmt import (
    CreateUserRequest,
    PaginatedUsers,
    UpdateProfileRequest,
    UpdateUserRoleRequest,
    UserResponse,
)
from app.services.avatar_processor import AvatarProcessor
from app.services.user_admin_service import UserAdminService
from app.services.user_profile_service import UserProfileService

router = APIRouter(prefix="/users", tags=["users"])

_require_admin = require_module_access("user_team_management")


# --- Self-service profile (any authenticated user) ---
# Must be declared BEFORE /{user_id} routes to avoid path ambiguity.

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await session.get(User, current_user.id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    svc = UserProfileService(session)
    user = await svc.update_profile(
        current_user.id,
        display_name=payload.display_name,
        timezone=payload.timezone,
    )
    return UserResponse.model_validate(user)


@router.post("/me/avatar", response_model=dict)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    processor = AvatarProcessor()
    avatar_url = await processor.process(file, current_user.id)
    user = await session.get(User, current_user.id)
    if user:
        user.avatar_url = avatar_url
        await session.commit()
    return {"avatar_url": avatar_url}


# --- Admin user management (require_module_access("user_team_management")) ---

@router.get("", response_model=PaginatedUsers)
async def list_users(
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> PaginatedUsers:
    svc = UserAdminService(session)
    users = await svc.list_users()
    return PaginatedUsers(items=[UserResponse.model_validate(u) for u in users], total=len(users))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    svc = UserAdminService(session)
    user = await svc.create_user(
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
        name=payload.name,
    )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    svc = UserAdminService(session)
    user = await svc.update_role(user_id, payload.role)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = UserAdminService(session)
    await svc.deactivate_user(user_id)


@router.post("/{user_id}/unlock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_user(
    user_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = UserAdminService(session)
    await svc.unlock_user(user_id)
