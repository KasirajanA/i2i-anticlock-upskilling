from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import FailedLoginAttempt, User, UserSession
from app.services.password_hasher import PasswordHasher
from app.services.session_service import SessionService

_LOCKOUT_THRESHOLD = 5


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._hasher = PasswordHasher()
        self._session_svc = SessionService(session)

    async def login(self, email: str, password: str) -> UserSession:
        email = email.lower().strip()
        user = await self._get_user(email)

        if user is None:
            await self._hasher.dummy_verify()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        await self._check_lockout(user)

        verified = await self._hasher.verify(password, user.password_hash or "")
        if not verified:
            await self._record_failure(email, user)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        await self._reset_failures(email)
        return await self._session_svc.create(user.id)

    async def _get_user(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _check_lockout(self, user: User) -> None:
        if user.locked or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    async def _record_failure(self, email: str, user: User) -> None:
        result = await self._db.execute(
            select(FailedLoginAttempt).where(FailedLoginAttempt.email == email)
        )
        record = result.scalar_one_or_none()
        now = datetime.utcnow()
        if record is None:
            record = FailedLoginAttempt(email=email, attempt_count=1, last_attempt_at=now)
            self._db.add(record)
        else:
            record.attempt_count += 1
            record.last_attempt_at = now

        if record.attempt_count >= _LOCKOUT_THRESHOLD:
            user.locked = True
            record.locked_at = now

        await self._db.commit()

    async def _reset_failures(self, email: str) -> None:
        result = await self._db.execute(
            select(FailedLoginAttempt).where(FailedLoginAttempt.email == email)
        )
        record = result.scalar_one_or_none()
        if record:
            await self._db.delete(record)
            await self._db.commit()
