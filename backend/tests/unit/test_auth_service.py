"""Unit tests for AuthService."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base, FailedLoginAttempt, User
from app.services.auth_service import AuthService
from app.services.password_hasher import PasswordHasher


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    hasher = PasswordHasher(rounds=4)
    pw_hash = await hasher.hash("password123")
    user = User(name="Test", email="test@example.com", role="Sales Rep", password_hash=pw_hash)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_success(db_session, test_user):
    svc = AuthService(db_session)
    session = await svc.login("test@example.com", "password123")
    assert session.user_id == test_user.id


@pytest.mark.asyncio
async def test_login_wrong_password_raises_401(db_session, test_user):
    from fastapi import HTTPException  # noqa: PLC0415
    svc = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.login("test@example.com", "wrong_password")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user_raises_401(db_session):
    from fastapi import HTTPException  # noqa: PLC0415
    svc = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.login("nobody@example.com", "anything")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_lockout_after_5_failures(db_session, test_user):
    from fastapi import HTTPException  # noqa: PLC0415
    svc = AuthService(db_session)
    for _ in range(5):
        try:
            await svc.login("test@example.com", "wrong")
        except HTTPException:
            pass
    await db_session.refresh(test_user)
    assert test_user.locked is True


@pytest.mark.asyncio
async def test_locked_user_cannot_login(db_session, test_user):
    from fastapi import HTTPException  # noqa: PLC0415
    test_user.locked = True
    await db_session.commit()
    svc = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.login("test@example.com", "password123")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_failure_counter_resets_on_success(db_session, test_user):
    svc = AuthService(db_session)
    try:
        await svc.login("test@example.com", "wrong")
    except Exception:
        pass
    await svc.login("test@example.com", "password123")
    from sqlalchemy import select  # noqa: PLC0415
    record = (await db_session.execute(
        select(FailedLoginAttempt).where(FailedLoginAttempt.email == "test@example.com")
    )).scalar_one_or_none()
    assert record is None
