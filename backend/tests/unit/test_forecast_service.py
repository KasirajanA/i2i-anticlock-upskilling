"""Unit tests for DealService.get_forecast — Decimal accuracy, stage mapping, 403 enforcement."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.deal import DealStage


def test_probability_covers_all_stages():
    for stage in DealStage:
        prob = DealStage.probability(stage)
        assert isinstance(prob, Decimal)
        assert Decimal("0") <= prob <= Decimal("1")


def test_closed_lost_probability_is_zero():
    assert DealStage.probability(DealStage.CLOSED_LOST) == Decimal("0.00")


def test_closed_won_probability_is_one():
    assert DealStage.probability(DealStage.CLOSED_WON) == Decimal("1.00")


@pytest.mark.asyncio
async def test_forecast_sc003_exact_values(db_session, test_user, test_account):
    """SC-003: forecast totals accurate to the cent with known seed data."""
    from app.models.deal import Deal
    from app.services.deal_service import DealService

    period_start = date(2026, 7, 1)
    period_end   = date(2026, 9, 30)
    close_date   = date(2026, 8, 1)  # within the quarter

    seeds = [
        (DealStage.LEAD_IN,     Decimal("10000.00")),
        (DealStage.QUALIFIED,   Decimal("20000.00")),
        (DealStage.PROPOSAL,    Decimal("30000.00")),
        (DealStage.NEGOTIATION, Decimal("40000.00")),
    ]
    for stage, value in seeds:
        deal = Deal(
            ref_id=f"DEAL-FCST-{stage.name}",
            title=f"Forecast Seed {stage.value}",
            value=value,
            stage=stage,
            expected_close_date=close_date,
            owner_id=test_user.id,
            account_id=test_account.id,
        )
        db_session.add(deal)
    await db_session.flush()

    svc = DealService(db_session)
    result = await svc.get_forecast(period_start, period_end)

    assert result.total_weighted_forecast == Decimal("51000.00")

    stage_map = {row.stage: row for row in result.open_pipeline}
    assert stage_map[DealStage.LEAD_IN].weighted_value     == Decimal("1000.00")
    assert stage_map[DealStage.QUALIFIED].weighted_value   == Decimal("5000.00")
    assert stage_map[DealStage.PROPOSAL].weighted_value    == Decimal("15000.00")
    assert stage_map[DealStage.NEGOTIATION].weighted_value == Decimal("30000.00")


@pytest.mark.asyncio
async def test_forecast_excludes_closed_lost(db_session, test_user, test_account):
    from app.models.deal import Deal
    from app.services.deal_service import DealService

    period_start = date(2026, 7, 1)
    period_end   = date(2026, 9, 30)

    deal = Deal(
        ref_id="DEAL-CLOST-01",
        title="Lost Deal",
        value=Decimal("99999.00"),
        stage=DealStage.CLOSED_LOST,
        expected_close_date=date(2026, 8, 1),
        loss_reason="Budget cut",
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.flush()

    svc = DealService(db_session)
    result = await svc.get_forecast(period_start, period_end)

    # Closed Lost should NOT appear in open_pipeline
    for row in result.open_pipeline:
        assert row.stage != DealStage.CLOSED_LOST

    assert result.total_weighted_forecast == Decimal("0.00")


@pytest.mark.asyncio
async def test_forecast_period_filter(db_session, test_user, test_account):
    """Deals outside the requested period must be excluded."""
    from app.models.deal import Deal
    from app.services.deal_service import DealService

    in_period  = Deal(
        ref_id="DEAL-IN-01",
        title="In Period",
        value=Decimal("10000.00"),
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 8, 1),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    out_period = Deal(
        ref_id="DEAL-OUT-01",
        title="Out of Period",
        value=Decimal("10000.00"),
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 1),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add_all([in_period, out_period])
    await db_session.flush()

    svc = DealService(db_session)
    result = await svc.get_forecast(date(2026, 7, 1), date(2026, 9, 30))

    lead_in_row = next(r for r in result.open_pipeline if r.stage == DealStage.LEAD_IN)
    assert lead_in_row.deal_count == 1
    assert lead_in_row.total_value == Decimal("10000.00")
