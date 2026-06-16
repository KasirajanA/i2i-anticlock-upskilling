from collections.abc import Callable
from datetime import datetime

from fastapi import Cookie, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session


class CurrentUser(BaseModel):
    """Authenticated user context — populated from the session store."""

    id: int
    name: str
    email: str
    role: str  # Admin | Manager | Sales Rep | Support Agent


async def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Resolve the current user from the HTTP-only session cookie.

    Raises 401 when no valid session exists; 403 when the user is inactive.
    This is the MVP stub — Module 005 (Authentication) will replace the session
    lookup logic while keeping this dependency signature stable.
    """
    if not session_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Import here to avoid circular imports at module load time
    from app.models.base import User, UserSession  # noqa: PLC0415

    result = await db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None or session.expires_at < datetime.utcnow():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return CurrentUser(id=user.id, name=user.name, email=user.email, role=user.role)


def require_roles(*roles: str) -> Callable:
    """Dependency factory: enforces that the current user has one of the given roles."""

    async def _check(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted for this action.",
            )
        return current_user

    return _check


def assert_contract_ownership(contract_owner_id: int, current_user: CurrentUser) -> None:
    """Raise 403 if a Sales Rep attempts to act on a contract they do not own."""
    if current_user.role in ("Admin", "Manager"):
        return
    if contract_owner_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this contract.",
        )


def require_deal_ownership(deal_owner_id: int, current_user: CurrentUser) -> None:
    """Raise 403 if a Sales Rep attempts to act on a deal they do not own."""
    if current_user.role in ("Admin", "Manager"):
        return
    if deal_owner_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this deal.",
        )


def require_team_scope(deal_owner_id: int, current_user: CurrentUser) -> None:
    """Enforce team-scope visibility for Sales Reps (FR-006).

    Sales Reps may only view deals they own. Raises 404 (not 403) so that
    out-of-scope deals are indistinguishable from non-existent ones.
    Module 006 (User & Team Management) will extend this to team-level scoping.
    """
    if current_user.role in ("Admin", "Manager"):
        return
    if deal_owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Deal not found")
