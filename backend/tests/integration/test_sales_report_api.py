"""Integration tests for GET /api/v1/analytics/reports/sales."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.deal import Deal, DealStage


@pytest.mark.asyncio
async def test_sales_report_returns_200(client):
    resp = await client.get("/api/v1/analytics/reports/sales")
    assert resp.status_code == 200
    body = resp.json()
    assert "stage_breakdown" in body
    assert "won_count" in body
    assert "lost_count" in body


@pytest.mark.asyncio
async def test_sales_rep_sees_only_own_deals(client, admin_client, db_session, test_user, admin_user, test_account):
    from app.models.base import User  # noqa: PLC0415
    # Deal owned by test_user (Sales Rep)
    db_session.add(Deal(
        ref_id="DEAL-SR-01",
        title="My Deal",
        value=Decimal("3000.00"),
        stage=DealStage.QUALIFIED,
        expected_close_date=date(2027, 1, 1),
        owner_id=test_user.id,
        account_id=test_account.id,
    ))
    # Deal owned by admin_user
    db_session.add(Deal(
        ref_id="DEAL-SR-02",
        title="Other Deal",
        value=Decimal("7000.00"),
        stage=DealStage.PROPOSAL,
        expected_close_date=date(2027, 1, 1),
        owner_id=admin_user.id,
        account_id=test_account.id,
    ))
    await db_session.commit()

    rep_resp = await client.get("/api/v1/analytics/reports/sales")
    admin_resp = await admin_client.get("/api/v1/analytics/reports/sales")

    rep_total = sum(s["count"] for s in rep_resp.json()["stage_breakdown"])
    admin_total = sum(s["count"] for s in admin_resp.json()["stage_breakdown"])
    assert rep_total < admin_total


@pytest.mark.asyncio
async def test_sales_rep_owner_id_override_returns_403(client, admin_user):
    resp = await client.get(f"/api/v1/analytics/reports/sales?owner_id={admin_user.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_date_range_returns_422(client):
    resp = await client.get("/api/v1/analytics/reports/sales?created_after=2026-06-30&created_before=2026-01-01")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_export_returns_csv(client):
    resp = await client.get("/api/v1/analytics/reports/sales/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
