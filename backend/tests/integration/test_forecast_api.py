"""Integration tests for GET /api/v1/pipeline/forecast — accuracy and access control."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.deal import Deal, DealStage


async def _seed_deal(db_session, user, account, stage, value, close_date):
    from sqlalchemy import select, func
    from app.models.deal import Deal
    result = await db_session.execute(select(func.count()).select_from(Deal))
    seq = (result.scalar_one() or 0) + 1
    deal = Deal(
        ref_id=f"DEAL-FC{seq:03d}",
        title=f"Forecast {stage.value}",
        value=value,
        stage=stage,
        expected_close_date=close_date,
        owner_id=user.id,
        account_id=account.id,
    )
    db_session.add(deal)
    await db_session.flush()
    return deal


@pytest.mark.asyncio
async def test_forecast_sc003_exact_totals(manager_client, db_session, manager_user, test_account):
    """SC-003: forecast values match known arithmetic to the cent."""
    close_date = date(2026, 8, 1)
    seeds = [
        (DealStage.LEAD_IN,     Decimal("10000.00")),
        (DealStage.QUALIFIED,   Decimal("20000.00")),
        (DealStage.PROPOSAL,    Decimal("30000.00")),
        (DealStage.NEGOTIATION, Decimal("40000.00")),
    ]
    for stage, value in seeds:
        await _seed_deal(db_session, manager_user, test_account, stage, value, close_date)
    await db_session.commit()

    resp = await manager_client.get(
        "/api/v1/pipeline/forecast",
        params={"period": "2026-07-01/2026-09-30"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["total_weighted_forecast"]) == Decimal("51000.00")

    stage_map = {row["stage"]: row for row in data["open_pipeline"]}
    assert Decimal(stage_map["Lead In"]["weighted_value"])     == Decimal("1000.00")
    assert Decimal(stage_map["Qualified"]["weighted_value"])   == Decimal("5000.00")
    assert Decimal(stage_map["Proposal"]["weighted_value"])    == Decimal("15000.00")
    assert Decimal(stage_map["Negotiation"]["weighted_value"]) == Decimal("30000.00")


@pytest.mark.asyncio
async def test_forecast_excludes_closed_lost(manager_client, db_session, manager_user, test_account):
    deal = Deal(
        ref_id="DEAL-CLOST-FC",
        title="Lost",
        value=Decimal("99999.00"),
        stage=DealStage.CLOSED_LOST,
        expected_close_date=date(2026, 8, 1),
        loss_reason="No budget",
        owner_id=manager_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.commit()

    resp = await manager_client.get(
        "/api/v1/pipeline/forecast",
        params={"period": "2026-07-01/2026-09-30"},
    )
    assert resp.status_code == 200
    stages_in_pipeline = [r["stage"] for r in resp.json()["open_pipeline"]]
    assert "Closed Lost" not in stages_in_pipeline
    assert Decimal(resp.json()["total_weighted_forecast"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_forecast_forbidden_for_sales_rep(client):
    resp = await client.get("/api/v1/pipeline/forecast")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_forecast_invalid_period_returns_400(manager_client):
    resp = await manager_client.get(
        "/api/v1/pipeline/forecast",
        params={"period": "not-a-date"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_forecast_period_end_before_start_returns_400(manager_client):
    resp = await manager_client.get(
        "/api/v1/pipeline/forecast",
        params={"period": "2026-09-30/2026-07-01"},
    )
    assert resp.status_code == 400
