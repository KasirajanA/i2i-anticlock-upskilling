"""Integration tests for /api/v1/users endpoints (Module 006)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_list_users_as_admin(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/users")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_users_forbidden_for_non_admin(client: AsyncClient):
    resp = await client.get("/api/v1/users")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_user_as_admin(admin_client: AsyncClient):
    payload = {
        "name": "New User",
        "email": "newuser@example.com",
        "role": "Manager",
        "password": "securepassword1",
    }
    resp = await admin_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "Manager"


@pytest.mark.asyncio
async def test_update_user_role_as_admin(admin_client: AsyncClient, db_session: AsyncSession):
    from app.models.base import User

    target = User(name="Role Target", email="roletarget@example.com", role="Sales Rep")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    resp = await admin_client.patch(f"/api/v1/users/{target.id}/role", json={"role": "Manager"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "Manager"


@pytest.mark.asyncio
async def test_get_me_returns_own_profile(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "rep@test.com"


@pytest.mark.asyncio
async def test_update_me_profile(client: AsyncClient):
    payload = {"display_name": "Updated Name", "timezone": "America/New_York"}
    resp = await client.patch("/api/v1/users/me", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Updated Name"
    assert data["timezone"] == "America/New_York"


@pytest.mark.asyncio
async def test_update_me_invalid_timezone(client: AsyncClient):
    resp = await client.patch("/api/v1/users/me", json={"timezone": "Not/ATimezone"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_user_as_admin(admin_client: AsyncClient, db_session: AsyncSession):
    from app.models.base import User

    target = User(name="Deactivate Me", email="deactivate@example.com", role="Sales Rep")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    resp = await admin_client.post(f"/api/v1/users/{target.id}/deactivate")
    assert resp.status_code == 204
