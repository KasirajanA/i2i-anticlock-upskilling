"""Integration tests for admin user management endpoints."""

import pytest


@pytest.mark.asyncio
async def test_admin_create_user_returns_201(admin_client):
    resp = await admin_client.post(
        "/api/v1/auth/users",
        json={"email": "newrep@example.com", "password": "securepass1", "role": "Sales Rep", "name": "New Rep"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newrep@example.com"
    assert body["role"] == "Sales Rep"


@pytest.mark.asyncio
async def test_admin_create_user_normalises_email(admin_client):
    resp = await admin_client.post(
        "/api/v1/auth/users",
        json={"email": "UPPER@EXAMPLE.COM", "password": "securepass1", "role": "Manager", "name": "Upper Case"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "upper@example.com"


@pytest.mark.asyncio
async def test_duplicate_email_returns_409(admin_client):
    payload = {"email": "dup@example.com", "password": "securepass1", "role": "Manager", "name": "Dup"}
    await admin_client.post("/api/v1/auth/users", json=payload)
    resp = await admin_client.post("/api/v1/auth/users", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_short_password_returns_422(admin_client):
    resp = await admin_client.post(
        "/api/v1/auth/users",
        json={"email": "short@example.com", "password": "abc", "role": "Manager", "name": "Short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_role_returns_422(admin_client):
    resp = await admin_client.post(
        "/api/v1/auth/users",
        json={"email": "badrole@example.com", "password": "securepass1", "role": "InvalidRole", "name": "Bad"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_non_admin_returns_403(client):
    resp = await client.post(
        "/api/v1/auth/users",
        json={"email": "blocked@example.com", "password": "securepass1", "role": "Manager", "name": "Blocked"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reset_password_returns_204(admin_client, db_session, test_user):
    resp = await admin_client.post(
        f"/api/v1/auth/users/{test_user.id}/reset-password",
        json={"new_password": "newpassword1"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_deactivate_user_returns_204(admin_client, db_session, test_user):
    resp = await admin_client.post(f"/api/v1/auth/users/{test_user.id}/deactivate")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_unlock_user_returns_204(admin_client, db_session, test_user):
    resp = await admin_client.post(f"/api/v1/auth/users/{test_user.id}/unlock")
    assert resp.status_code == 204
