"""Integration tests for /api/v1/contacts endpoints (Module 007)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_list_contacts_empty(client: AsyncClient):
    resp = await client.get("/api/v1/contacts")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_create_contact(admin_client: AsyncClient):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "janedoe@example.com",
        "account_ids": [],
        "tags": [],
    }
    resp = await admin_client.post("/api/v1/contacts", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["contact"]["email"] == "janedoe@example.com"


@pytest.mark.asyncio
async def test_duplicate_email_returns_warning(admin_client: AsyncClient):
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "account_ids": [],
        "tags": [],
    }
    first = await admin_client.post("/api/v1/contacts", json=payload)
    assert first.status_code == 201
    # Second create with same email
    second = await admin_client.post("/api/v1/contacts", json={**payload, "first_name": "Alicia"})
    assert second.status_code == 201
    data = second.json()
    assert data.get("duplicate_warning") is not None


@pytest.mark.asyncio
async def test_support_agent_cannot_create_contact(support_client: AsyncClient):
    payload = {
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob@example.com",
        "account_ids": [],
        "tags": [],
    }
    resp = await support_client.post("/api/v1/contacts", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_contact(admin_client: AsyncClient):
    create_resp = await admin_client.post("/api/v1/contacts", json={
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@example.com",
        "account_ids": [],
        "tags": [],
    })
    assert create_resp.status_code == 201
    contact_id = create_resp.json()["contact"]["id"]

    get_resp = await admin_client.get(f"/api/v1/contacts/{contact_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "charlie@example.com"


@pytest.mark.asyncio
async def test_archive_contact_admin_only(client: AsyncClient, admin_client: AsyncClient):
    create_resp = await admin_client.post("/api/v1/contacts", json={
        "first_name": "Del",
        "last_name": "Rey",
        "email": "del@example.com",
        "account_ids": [],
        "tags": [],
    })
    contact_id = create_resp.json()["contact"]["id"]

    # Sales Rep cannot archive
    del_resp = await client.delete(f"/api/v1/contacts/{contact_id}")
    assert del_resp.status_code == 403

    # Admin can archive
    admin_del = await admin_client.delete(f"/api/v1/contacts/{contact_id}")
    assert admin_del.status_code == 204
