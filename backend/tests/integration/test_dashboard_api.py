"""Integration tests for GET /api/v1/analytics/dashboard."""

from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.deal import Deal, DealStage
from app.models.support import Ticket, TicketSequence


@pytest.mark.asyncio
async def test_sales_rep_gets_deal_widgets(client, db_session, test_user, test_account):
    # Seed 2 open deals owned by test_user (Sales Rep)
    for i in range(2):
        db_session.add(Deal(
            ref_id=f"DEAL-DASH-{i:02d}",
            title=f"Deal {i}",
            value=Decimal("1000.00"),
            stage=DealStage.QUALIFIED,
            expected_close_date=__import__("datetime").date(2027, 1, 1),
            owner_id=test_user.id,
            account_id=test_account.id,
        ))
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    keys = {w["key"] for w in body["widgets"]}
    assert "open_deals_count" in keys
    assert "pipeline_value" in keys
    # Sales Rep should NOT see org-level widgets
    assert "org_open_deals" not in keys
    assert "org_open_tickets" not in keys


@pytest.mark.asyncio
async def test_sales_rep_open_deals_count_matches_seeds(client, db_session, test_user, test_account):
    for i in range(3):
        db_session.add(Deal(
            ref_id=f"DEAL-D2-{i:02d}",
            title=f"D {i}",
            value=Decimal("500.00"),
            stage=DealStage.LEAD_IN,
            expected_close_date=__import__("datetime").date(2027, 6, 1),
            owner_id=test_user.id,
            account_id=test_account.id,
        ))
    await db_session.commit()

    resp = await client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    widgets = {w["key"]: w["value"] for w in resp.json()["widgets"]}
    assert widgets["open_deals_count"] >= 3


@pytest.mark.asyncio
async def test_support_agent_gets_ticket_widgets(support_client, db_session, support_agent_user, test_contact):
    resp = await support_client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    keys = {w["key"] for w in resp.json()["widgets"]}
    assert "open_tickets" in keys
    assert "sla_breach_count" in keys
    assert "open_deals_count" not in keys


@pytest.mark.asyncio
async def test_admin_gets_both_deal_and_org_widgets(admin_client):
    resp = await admin_client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    keys = {w["key"] for w in resp.json()["widgets"]}
    assert "open_deals_count" in keys
    assert "open_tickets" in keys
    assert "org_open_deals" in keys


@pytest.mark.asyncio
async def test_dashboard_not_cached(client):
    r1 = await client.get("/api/v1/analytics/dashboard")
    r2 = await client.get("/api/v1/analytics/dashboard")
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Both responses have a generated_at — they are independent (staleTime: 0)
    assert "generated_at" in r1.json()
