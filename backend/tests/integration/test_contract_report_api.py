"""Integration tests for GET /api/v1/analytics/reports/contracts."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.contracts import Contract, ContractStatus


@pytest.mark.asyncio
async def test_contract_report_returns_200(manager_client):
    resp = await manager_client.get("/api/v1/analytics/reports/contracts")
    assert resp.status_code == 200
    body = resp.json()
    assert "status_breakdown" in body
    assert "upcoming_renewals" in body
    assert "value_by_account" in body


@pytest.mark.asyncio
async def test_invalid_renewal_window_returns_422(admin_client):
    resp = await admin_client.get("/api/v1/analytics/reports/contracts?renewal_window=99")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_renewal_window_filters_correctly(admin_client, db_session, admin_user, test_account):
    today = date.today()
    # Contract expiring in 15 days (within 30d window)
    db_session.add(Contract(
        ref_id="CTR-R-01",
        value=Decimal("5000.00"),
        start_date=today,
        end_date=today + timedelta(days=15),
        status=ContractStatus.ACTIVE,
        owner_id=admin_user.id,
        account_id=test_account.id,
    ))
    # Contract expiring in 100 days (outside 90d window)
    db_session.add(Contract(
        ref_id="CTR-R-02",
        value=Decimal("5000.00"),
        start_date=today,
        end_date=today + timedelta(days=100),
        status=ContractStatus.ACTIVE,
        owner_id=admin_user.id,
        account_id=test_account.id,
    ))
    await db_session.commit()

    resp = await admin_client.get("/api/v1/analytics/reports/contracts?renewal_window=30")
    assert resp.status_code == 200
    renewals = resp.json()["upcoming_renewals"]
    contract_ids = {r["ref_id"] for r in renewals}
    assert "CTR-R-01" in contract_ids
    assert "CTR-R-02" not in contract_ids


@pytest.mark.asyncio
async def test_sales_rep_cannot_override_owner_id(client, admin_user):
    resp = await client.get(f"/api/v1/analytics/reports/contracts?owner_id={admin_user.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_export_returns_csv(admin_client):
    resp = await admin_client.get("/api/v1/analytics/reports/contracts/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
