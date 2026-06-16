"""Integration tests for /api/v1/leads endpoints (Module 007)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_lead(client: AsyncClient):
    payload = {
        "first_name": "Alex",
        "last_name": "Johnson",
        "email": "alex@startup.io",
        "company_name": "StartupIO",
        "notes": "Interested in enterprise plan.",
    }
    resp = await client.post("/api/v1/leads", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "new"
    assert data["first_name"] == "Alex"

    list_resp = await client.get("/api/v1/leads")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_support_agent_cannot_list_leads(support_client: AsyncClient):
    resp = await support_client.get("/api/v1/leads")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_lead_conversion(client: AsyncClient):
    create_resp = await client.post("/api/v1/leads", json={
        "first_name": "Sam",
        "last_name": "Lee",
        "email": "sam@company.io",
        "company_name": "CompanyIO",
    })
    lead_id = create_resp.json()["id"]

    convert_resp = await client.post(f"/api/v1/leads/{lead_id}/convert", json={
        "create_account": True,
        "create_deal": False,
    })
    assert convert_resp.status_code == 201
    data = convert_resp.json()
    assert "contact_id" in data
    assert data["lead_id"] == lead_id
