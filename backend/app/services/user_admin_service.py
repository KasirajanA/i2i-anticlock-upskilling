from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import FailedLoginAttempt, User
from app.services.password_hasher import PasswordHasher
from app.services.session_service import SessionService

VALID_ROLES = {"Admin", "Manager", "Sales Rep", "Support Agent"}


class UserAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._hasher = PasswordHasher()
        self._session_svc = SessionService(session)

    async def create_user(self, email: str, password: str, role: str, name: str) -> User:
        email = email.lower().strip()
        if len(password) < 8:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters.")
        if role not in VALID_ROLES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid role: {role}.")

        existing = (await self._db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered.")

        password_hash = await self._hasher.hash(password)
        user = User(name=name, email=email, role=role, password_hash=password_hash)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def reset_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < 8:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters.")
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.password_hash = await self._hasher.hash(new_password)
        await self._db.commit()
        await self._session_svc.delete_by_user_id(user_id)

    async def deactivate_user(self, user_id: int) -> None:
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.role == "Admin":
            active_admins = (await self._db.execute(
                select(func.count(User.id)).where(User.role == "Admin", User.is_active == True)  # noqa: E712
            )).scalar_one()
            if active_admins <= 1:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Cannot deactivate the last active Admin.")
        user.is_active = False
        await self._db.commit()
        await self._session_svc.delete_by_user_id(user_id)

    async def unlock_user(self, user_id: int) -> None:
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.locked = False
        await self._db.commit()
        record = (await self._db.execute(
            select(FailedLoginAttempt).where(FailedLoginAttempt.email == user.email)
        )).scalar_one_or_none()
        if record:
            await self._db.delete(record)
            await self._db.commit()

    async def update_role(self, user_id: int, new_role: str) -> User:
        if new_role not in VALID_ROLES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid role: {new_role}.")
        user = await self._db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.role == "Admin" and new_role != "Admin":
            active_admins = (await self._db.execute(
                select(func.count(User.id)).where(User.role == "Admin", User.is_active == True)  # noqa: E712
            )).scalar_one()
            if active_admins <= 1:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Cannot change the role of the last active Admin.")
        user.role = new_role
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def list_users(self) -> list[User]:
        result = await self._db.execute(select(User).order_by(User.created_at))
        return list(result.scalars().all())
