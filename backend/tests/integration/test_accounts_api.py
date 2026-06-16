"""Integration tests for /api/v1/accounts endpoints (Module 007)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_accounts_empty(client: AsyncClient):
    resp = await client.get("/api/v1/accounts")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_create_and_get_account(admin_client: AsyncClient):
    payload = {"name": "Acme Corp", "industry": "Technology"}
    resp = await admin_client.post("/api/v1/accounts", json=payload)
    assert resp.status_code == 201
    account_id = resp.json()["id"]

    get_resp = await admin_client.get(f"/api/v1/accounts/{account_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["name"] == "Acme Corp"
    assert data["industry"] == "Technology"
    assert "contact_count" in data


@pytest.mark.asyncio
async def test_support_agent_cannot_create_account(support_client: AsyncClient):
    resp = await support_client.post("/api/v1/accounts", json={"name": "TestCo"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_account_timeline_empty(admin_client: AsyncClient):
    create_resp = await admin_client.post("/api/v1/accounts", json={"name": "Timeline Corp"})
    account_id = create_resp.json()["id"]

    timeline_resp = await admin_client.get(f"/api/v1/accounts/{account_id}/timeline")
    assert timeline_resp.status_code == 200
    assert isinstance(timeline_resp.json(), list)


@pytest.mark.asyncio
async def test_archive_account_admin_only(admin_client: AsyncClient, client: AsyncClient):
    create_resp = await admin_client.post("/api/v1/accounts", json={"name": "Archive Me"})
    account_id = create_resp.json()["id"]

    non_admin = await client.delete(f"/api/v1/accounts/{account_id}")
    assert non_admin.status_code == 403

    admin_del = await admin_client.delete(f"/api/v1/accounts/{account_id}")
    assert admin_del.status_code == 204
