"""Unit tests for DealService — stage change guards, ref_id generation, overdue logic."""

import pytest

from app.models.deal import DealStage


# ---------------------------------------------------------------------------
# DealStage helpers
# ---------------------------------------------------------------------------

def test_terminal_stages():
    assert DealStage.CLOSED_WON.is_terminal is True
    assert DealStage.CLOSED_LOST.is_terminal is True
    assert DealStage.LEAD_IN.is_terminal is False
    assert DealStage.QUALIFIED.is_terminal is False
    assert DealStage.PROPOSAL.is_terminal is False
    assert DealStage.NEGOTIATION.is_terminal is False


def test_probability_mapping():
    from decimal import Decimal
    assert DealStage.probability(DealStage.LEAD_IN)     == Decimal("0.10")
    assert DealStage.probability(DealStage.QUALIFIED)   == Decimal("0.25")
    assert DealStage.probability(DealStage.PROPOSAL)    == Decimal("0.50")
    assert DealStage.probability(DealStage.NEGOTIATION) == Decimal("0.75")
    assert DealStage.probability(DealStage.CLOSED_WON)  == Decimal("1.00")
    assert DealStage.probability(DealStage.CLOSED_LOST) == Decimal("0.00")


# ---------------------------------------------------------------------------
# Stage change guard — unit tests against DealService with real async DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_stage_happy_path(db_session, test_user, test_account):
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.models.deal import Deal
    from decimal import Decimal
    from datetime import date

    deal = Deal(
        ref_id="DEAL-9001",
        title="Unit Test Deal",
        value=Decimal("5000.00"),
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.flush()

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)
    updated = await svc.change_stage(deal, DealStage.QUALIFIED, None, user)
    assert updated.stage == DealStage.QUALIFIED


@pytest.mark.asyncio
async def test_change_stage_terminal_guard_raises_422(db_session, test_user, test_account):
    from fastapi import HTTPException
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.models.deal import Deal
    from decimal import Decimal
    from datetime import date

    deal = Deal(
        ref_id="DEAL-9002",
        title="Closed Deal",
        value=Decimal("5000.00"),
        stage=DealStage.CLOSED_WON,
        expected_close_date=date(2026, 6, 1),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.flush()

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.change_stage(deal, DealStage.QUALIFIED, None, user)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "TERMINAL_STAGE"


@pytest.mark.asyncio
async def test_change_stage_closed_lost_missing_reason_raises_422(db_session, test_user, test_account):
    from fastapi import HTTPException
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.models.deal import Deal
    from decimal import Decimal
    from datetime import date

    deal = Deal(
        ref_id="DEAL-9003",
        title="Proposal Deal",
        value=Decimal("5000.00"),
        stage=DealStage.PROPOSAL,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.flush()

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.change_stage(deal, DealStage.CLOSED_LOST, None, user)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "LOSS_REASON_REQUIRED"


@pytest.mark.asyncio
async def test_change_stage_clears_overdue_on_close(db_session, test_user, test_account):
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.models.deal import Deal
    from decimal import Decimal
    from datetime import date

    deal = Deal(
        ref_id="DEAL-9004",
        title="Overdue Deal",
        value=Decimal("5000.00"),
        stage=DealStage.NEGOTIATION,
        expected_close_date=date(2026, 1, 1),
        owner_id=test_user.id,
        account_id=test_account.id,
        is_overdue=True,
    )
    db_session.add(deal)
    await db_session.flush()

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)
    updated = await svc.change_stage(deal, DealStage.CLOSED_WON, None, user)
    assert updated.is_overdue is False
    assert updated.stage == DealStage.CLOSED_WON


@pytest.mark.asyncio
async def test_change_stage_log_note_format(db_session, test_user, test_account):
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.repositories.activity_repository import ActivityRepository
    from app.models.deal import Deal
    from decimal import Decimal
    from datetime import date

    deal = Deal(
        ref_id="DEAL-9005",
        title="Log Test Deal",
        value=Decimal("5000.00"),
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.flush()

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)
    await svc.change_stage(deal, DealStage.QUALIFIED, None, user)

    repo = ActivityRepository(db_session)
    entries = await repo.fetch_for_deal(deal.id)
    stage_logs = [e for e in entries if e.action_type == "stage_changed"]
    assert len(stage_logs) == 1
    assert stage_logs[0].note == "Lead In → Qualified"


@pytest.mark.asyncio
async def test_ref_id_generation_sequence(db_session, test_user, test_account):
    from app.core.security import CurrentUser
    from app.services.deal_service import DealService
    from app.schemas.deal import DealCreate
    from datetime import date

    user = CurrentUser(id=test_user.id, name=test_user.name, email=test_user.email, role="Sales Rep")
    svc = DealService(db_session)

    payload = DealCreate(
        title="First Deal",
        value="1000.00",
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    d1 = await svc.create(payload, user)
    assert d1.ref_id == "DEAL-0001"

    payload2 = DealCreate(
        title="Second Deal",
        value="2000.00",
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    d2 = await svc.create(payload2, user)
    assert d2.ref_id == "DEAL-0002"
