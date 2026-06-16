"""Integration tests for POST /api/v1/auth/login."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_session
from app.core.security import get_current_user
from app.main import create_app
from app.models.base import User
from app.services.password_hasher import PasswordHasher


@pytest_asyncio.fixture
async def auth_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_user(auth_engine):
    factory = async_sessionmaker(auth_engine, expire_on_commit=False)
    hasher = PasswordHasher(rounds=4)
    pw = await hasher.hash("securepass1")
    async with factory() as s:
        u = User(name="Auth User", email="auth@example.com", role="Sales Rep", password_hash=pw)
        s.add(u)
        await s.commit()
        await s.refresh(u)
        return u


@pytest_asyncio.fixture
async def auth_client(auth_engine, auth_user):
    factory = async_sessionmaker(auth_engine, expire_on_commit=False)
    app = create_app()

    async def _db():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _db
    # No get_current_user override — login endpoint doesn't require auth

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_valid_credentials_returns_200_and_cookie(auth_client):
    resp = await auth_client.post("/api/v1/auth/login", json={"email": "auth@example.com", "password": "securepass1"})
    assert resp.status_code == 200
    assert "crm_session" in resp.cookies
    body = resp.json()
    assert body["user"]["email"] == "auth@example.com"


@pytest.mark.asyncio
async def test_wrong_password_returns_401(auth_client):
    resp = await auth_client.post("/api/v1/auth/login", json={"email": "auth@example.com", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password."


@pytest.mark.asyncio
async def test_unknown_user_returns_401_same_body(auth_client):
    resp = await auth_client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "anything"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password."


@pytest.mark.asyncio
async def test_lockout_on_fifth_failure(auth_client, auth_user, auth_engine):
    for _ in range(5):
        await auth_client.post("/api/v1/auth/login", json={"email": "auth@example.com", "password": "bad"})

    factory = async_sessionmaker(auth_engine, expire_on_commit=False)
    async with factory() as s:
        user = await s.get(User, auth_user.id)
        assert user.locked is True


@pytest.mark.asyncio
async def test_sixth_attempt_while_locked_returns_401(auth_client):
    for _ in range(6):
        await auth_client.post("/api/v1/auth/login", json={"email": "auth@example.com", "password": "bad"})
    resp = await auth_client.post("/api/v1/auth/login", json={"email": "auth@example.com", "password": "securepass1"})
    assert resp.status_code == 401
