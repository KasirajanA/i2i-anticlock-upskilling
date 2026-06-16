"""T053: Scheduler job integration tests — expire, renewal flag, renew endpoint."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contracts import Contract, ContractStatus


@pytest.mark.asyncio
async def test_expire_contracts_job(client, admin_client, test_account, test_user):
    """SC-002: Active contract past end_date becomes Expired via trigger endpoint."""
    yesterday = date.today() - timedelta(days=1)
    create = await client.post("/api/v1/contracts", json={
        "value": 1000.0,
        "start_date": "2025-01-01",
        "end_date": yesterday.isoformat(),
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    # Advance to Active
    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Sent for Review"})
    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Active"})

    trigger = await admin_client.post("/api/v1/internal/jobs/expire-contracts")
    assert trigger.status_code == 200
    assert trigger.json()["expired"] >= 1

    detail = await client.get(f"/api/v1/contracts/{ref_id}")
    assert detail.json()["status"] == "Expired"


@pytest.mark.asyncio
async def test_flag_renewals_job(client, admin_client, test_account):
    """SC-003: Active contract within 30-day window is flagged via trigger endpoint."""
    soon = date.today() + timedelta(days=20)
    create = await client.post("/api/v1/contracts", json={
        "value": 2000.0,
        "start_date": "2026-01-01",
        "end_date": soon.isoformat(),
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Sent for Review"})
    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Active"})

    trigger = await admin_client.post("/api/v1/internal/jobs/flag-renewals")
    assert trigger.status_code == 200
    assert trigger.json()["flagged"] >= 1

    detail = await client.get(f"/api/v1/contracts/{ref_id}")
    assert detail.json()["is_renewal_due"] is True


@pytest.mark.asyncio
async def test_renew_creates_successor(client, test_account):
    """SC-005: Renew endpoint creates successor with correct date arithmetic."""
    create = await client.post("/api/v1/contracts", json={
        "value": 5000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Sent for Review"})
    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Active"})

    renew = await client.post(f"/api/v1/contracts/{ref_id}/renew")
    assert renew.status_code == 201
    data = renew.json()
    assert data["successor"]["status"] == "Draft"
    assert data["successor"]["start_date"] == "2027-01-01"
    assert data["successor"]["end_date"] == "2027-12-31"
    assert data["successor"]["value"] == "5000.00"


@pytest.mark.asyncio
async def test_duplicate_renew_blocked(client, test_account):
    """Renewing the same contract twice returns 400."""
    create = await client.post("/api/v1/contracts", json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Sent for Review"})
    await client.post(f"/api/v1/contracts/{ref_id}/transition",
                      json={"status": "Active"})

    first = await client.post(f"/api/v1/contracts/{ref_id}/renew")
    assert first.status_code == 201

    second = await client.post(f"/api/v1/contracts/{ref_id}/renew")
    assert second.status_code == 400
