from __future__ import annotations

import zoneinfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import User
from app.services.password_hasher import PasswordHasher

_VALID_TIMEZONES = zoneinfo.available_timezones()


class UserProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._hasher = PasswordHasher()

    async def update_profile(
        self,
        user_id: int,
        display_name: str | None = None,
        timezone: str | None = None,
    ) -> User:
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        if display_name is not None:
            if not (1 <= len(display_name) <= 100):
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="display_name must be 1–100 characters.")
            user.display_name = display_name
        if timezone is not None:
            if timezone not in _VALID_TIMEZONES:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid timezone: {timezone}.")
            user.timezone = timezone
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        if not user.password_hash:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")
        if not await self._hasher.verify(current_password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")
        user.password_hash = await self._hasher.hash(new_password)
        await self._db.commit()
