"""Integration tests for /api/v1/teams endpoints (Module 006)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_team(admin_client: AsyncClient, db_session: AsyncSession):
    from app.models.base import User

    m1 = User(name="Alice", email="alice@example.com", role="Sales Rep")
    m2 = User(name="Bob", email="bob@example.com", role="Sales Rep")
    db_session.add_all([m1, m2])
    await db_session.commit()
    await db_session.refresh(m1)
    await db_session.refresh(m2)

    payload = {
        "name": "EMEA Sales",
        "lead_user_id": m1.id,
        "member_ids": [m1.id, m2.id],
    }
    resp = await admin_client.post("/api/v1/teams", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "EMEA Sales"
    assert data["lead_user_id"] == m1.id
    assert data["member_count"] == 2


@pytest.mark.asyncio
async def test_list_teams(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/teams")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_create_team_lead_not_in_members_returns_422(admin_client: AsyncClient, db_session: AsyncSession):
    from app.models.base import User

    m1 = User(name="Carol", email="carol@example.com", role="Sales Rep")
    m2 = User(name="Dave", email="dave@example.com", role="Sales Rep")
    lead = User(name="Eve", email="eve@example.com", role="Manager")
    db_session.add_all([m1, m2, lead])
    await db_session.commit()
    await db_session.refresh(lead)
    await db_session.refresh(m1)
    await db_session.refresh(m2)

    payload = {
        "name": "Bad Team",
        "lead_user_id": lead.id,
        "member_ids": [m1.id, m2.id],
    }
    resp = await admin_client.post("/api/v1/teams", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_and_remove_member(admin_client: AsyncClient, db_session: AsyncSession):
    from app.models.base import User

    u1 = User(name="Frank", email="frank@example.com", role="Sales Rep")
    u2 = User(name="Grace", email="grace@example.com", role="Sales Rep")
    db_session.add_all([u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)
    await db_session.refresh(u2)

    create_resp = await admin_client.post("/api/v1/teams", json={"name": "Test Team", "member_ids": [u1.id]})
    assert create_resp.status_code == 201
    team_id = create_resp.json()["id"]

    add_resp = await admin_client.post(f"/api/v1/teams/{team_id}/members", json={"user_ids": [u2.id]})
    assert add_resp.status_code == 204

    detail_resp = await admin_client.get(f"/api/v1/teams/{team_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["member_count"] == 2

    del_resp = await admin_client.delete(f"/api/v1/teams/{team_id}/members/{u2.id}")
    assert del_resp.status_code == 204

    after_resp = await admin_client.get(f"/api/v1/teams/{team_id}")
    assert after_resp.json()["member_count"] == 1


@pytest.mark.asyncio
async def test_teams_forbidden_for_non_admin(client: AsyncClient):
    resp = await client.get("/api/v1/teams")
    assert resp.status_code == 403
