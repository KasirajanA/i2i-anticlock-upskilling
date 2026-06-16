from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.base import UserSession


class SessionService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create(self, user_id: int) -> UserSession:
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.session_timeout_minutes)
        session_obj = UserSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            expires_at=expires_at,
            last_active_at=now,
        )
        self._db.add(session_obj)
        await self._db.commit()
        await self._db.refresh(session_obj)
        return session_obj

    async def validate(self, session_id: str) -> UserSession | None:
        session_obj = await self._db.get(UserSession, session_id)
        if session_obj is None:
            return None
        cutoff = datetime.utcnow() - timedelta(minutes=settings.session_timeout_minutes)
        last_active = session_obj.last_active_at or session_obj.created_at
        if last_active < cutoff:
            await self.delete_by_id(session_id)
            return None
        return session_obj

    async def touch(self, session_id: str) -> None:
        await self._db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(last_active_at=datetime.utcnow())
        )
        await self._db.commit()

    async def delete_by_id(self, session_id: str) -> None:
        await self._db.execute(
            delete(UserSession).where(UserSession.id == session_id)
        )
        await self._db.commit()

    async def delete_by_user_id(self, user_id: int) -> None:
        await self._db.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )
        await self._db.commit()

    async def purge_expired(self) -> None:
        cutoff = datetime.utcnow() - timedelta(minutes=settings.session_timeout_minutes)
        await self._db.execute(
            delete(UserSession).where(UserSession.last_active_at < cutoff)
        )
        await self._db.commit()
