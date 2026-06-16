"""Integration tests for the /api/v1/deals endpoints."""

from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture
def deal_payload(test_account):
    return {
        "title": "Acme Corp Expansion",
        "value": "15000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-09-30",
        "owner_id": None,  # filled per test with test_user.id
        "account_id": test_account.id,
    }


@pytest.mark.asyncio
async def test_create_deal_returns_201(client, test_user, test_account):
    resp = await client.post("/api/v1/deals", json={
        "title": "Test Deal",
        "value": "5000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["ref_id"] == "DEAL-0001"
    assert data["stage"] == "Lead In"
    assert data["title"] == "Test Deal"
    assert data["owner"]["id"] == test_user.id
    assert data["account"]["id"] == test_account.id


@pytest.mark.asyncio
async def test_create_deal_unknown_account_returns_400(client, test_user):
    resp = await client.post("/api/v1/deals", json={
        "title": "No Account",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": 99999,
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_deals_returns_200(client, test_user, test_account):
    # Create two deals first
    for i in range(2):
        await client.post("/api/v1/deals", json={
            "title": f"Deal {i}",
            "value": "1000.00",
            "stage": "Lead In",
            "expected_close_date": "2026-12-31",
            "owner_id": test_user.id,
            "account_id": test_account.id,
        })
    resp = await client.get("/api/v1/deals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_deal_returns_200(client, test_user, test_account):
    create = await client.post("/api/v1/deals", json={
        "title": "Fetch Test",
        "value": "9000.00",
        "stage": "Qualified",
        "expected_close_date": "2026-11-30",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    resp = await client.get(f"/api/v1/deals/{ref_id}")
    assert resp.status_code == 200
    assert resp.json()["ref_id"] == ref_id


@pytest.mark.asyncio
async def test_get_deal_not_found_returns_404(client):
    resp = await client.get("/api/v1/deals/DEAL-9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_deal_returns_200(client, test_user, test_account):
    create = await client.post("/api/v1/deals", json={
        "title": "Patch Me",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    resp = await client.patch(f"/api/v1/deals/{ref_id}", json={"value": "2000.00"})
    assert resp.status_code == 200
    assert resp.json()["value"] == "2000.00"


@pytest.mark.asyncio
async def test_stage_change_full_chain(client, test_user, test_account):
    create = await client.post("/api/v1/deals", json={
        "title": "Stage Chain",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    for from_s, to_s in [("Lead In", "Qualified"), ("Qualified", "Proposal"), ("Proposal", "Closed Won")]:
        resp = await client.post(f"/api/v1/deals/{ref_id}/stage", json={"stage": to_s})
        assert resp.status_code == 200
        data = resp.json()
        assert data["previous_stage"] == from_s
        assert data["new_stage"] == to_s


@pytest.mark.asyncio
async def test_stage_change_terminal_guard_returns_422(client, test_user, test_account):
    create = await client.post("/api/v1/deals", json={
        "title": "Terminal Test",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    await client.post(f"/api/v1/deals/{ref_id}/stage", json={"stage": "Closed Won"})
    resp = await client.post(f"/api/v1/deals/{ref_id}/stage", json={"stage": "Qualified"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "TERMINAL_STAGE"


@pytest.mark.asyncio
async def test_stage_change_closed_lost_requires_loss_reason(client, test_user, test_account):
    create = await client.post("/api/v1/deals", json={
        "title": "Lost Test",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    resp = await client.post(f"/api/v1/deals/{ref_id}/stage", json={"stage": "Closed Lost"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "LOSS_REASON_REQUIRED"

    resp2 = await client.post(
        f"/api/v1/deals/{ref_id}/stage",
        json={"stage": "Closed Lost", "loss_reason": "Budget cut"},
    )
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_sales_rep_non_owner_patch_returns_403(db_engine, test_user, test_account, admin_user):
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from httpx import ASGITransport, AsyncClient
    from app.core.database import get_session
    from app.core.security import get_current_user, CurrentUser
    from app.main import create_app
    from app.models.deal import Deal, DealStage

    # Create a deal owned by admin_user directly
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        deal = Deal(
            ref_id="DEAL-OTHER",
            title="Admin Deal",
            value=Decimal("1000.00"),
            stage=DealStage.LEAD_IN,
            expected_close_date=date(2026, 12, 31),
            owner_id=admin_user.id,
            account_id=test_account.id,
        )
        session.add(deal)
        await session.commit()

    app = create_app()
    async def _override_db():
        async with factory() as session:
            yield session
    mock_rep = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    app.dependency_overrides[get_session] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_rep

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.patch("/api/v1/deals/DEAL-OTHER", json={"title": "Stolen"})
    # In MVP, out-of-scope deals are invisible to Sales Reps → 404 (not 403).
    # Module 006 (Team Management) will introduce team-scoped visibility where
    # a rep can SEE a team deal but still get 403 when trying to edit it.
    assert resp.status_code in (403, 404)
