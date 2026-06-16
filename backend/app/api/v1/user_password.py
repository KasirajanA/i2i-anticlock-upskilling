from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.user_mgmt import ChangePasswordRequest
from app.services.user_profile_service import UserProfileService

router = APIRouter(prefix="/users", tags=["profile"])


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    svc = UserProfileService(session)
    await svc.change_password(
        current_user.id,
        payload.current_password,
        payload.new_password,
    )
