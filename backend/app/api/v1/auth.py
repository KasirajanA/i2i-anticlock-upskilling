from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.auth import LoginRequest, MeResponse, UserResponse
from app.services.auth_service import AuthService
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "crm_session"
_COOKIE_OPTS = dict(httponly=True, samesite="strict", max_age=1800)


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    svc = AuthService(session)
    user_session = await svc.login(payload.email, payload.password)
    response.set_cookie(
        key=_COOKIE_NAME,
        value=user_session.id,
        **_COOKIE_OPTS,
    )
    from sqlalchemy import select  # noqa: PLC0415
    from app.models.base import User  # noqa: PLC0415
    user = (await session.execute(select(User).where(User.id == user_session.user_id))).scalar_one()
    return {"user": UserResponse.model_validate(user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    crm_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
):
    if crm_session:
        svc = SessionService(session)
        await svc.delete_by_id(crm_session)
    response.delete_cookie(_COOKIE_NAME)


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> MeResponse:
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=True,
    )
