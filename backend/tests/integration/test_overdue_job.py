"""Integration tests for the overdue-deal flagging scheduler job."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.deal import Deal, DealStage


async def _insert_deal(db_session, user, account, close_date, stage=DealStage.LEAD_IN):
    """Direct DB insert — bypasses service layer to control is_overdue/stage precisely."""
    from sqlalchemy import select, func
    result = await db_session.execute(select(func.count()).select_from(Deal))
    seq = (result.scalar_one() or 0) + 1
    deal = Deal(
        ref_id=f"DEAL-OD{seq:03d}",
        title="Overdue Test",
        value=Decimal("5000.00"),
        stage=stage,
        expected_close_date=close_date,
        owner_id=user.id,
        account_id=account.id,
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    return deal


@pytest.mark.asyncio
async def test_overdue_flag_set_on_past_close_deal(admin_client, db_session, test_user, test_account):
    """A non-closed deal with expected_close_date < today is flagged is_overdue=True."""
    deal = await _insert_deal(db_session, test_user, test_account, date(2026, 1, 1))

    resp = await admin_client.post("/api/v1/internal/jobs/flag-overdue")
    assert resp.status_code == 200
    assert resp.json()["flagged"] >= 1

    # db_session committed before the API call, so a fresh query sees API changes
    await db_session.refresh(deal)
    assert deal.is_overdue is True


@pytest.mark.asyncio
async def test_overdue_job_inserts_notification(admin_client, db_session, test_user, test_account):
    """The job inserts a Notification row for the deal owner."""
    from sqlalchemy import select
    from app.models.base import Notification

    deal = await _insert_deal(db_session, test_user, test_account, date(2026, 1, 1))

    await admin_client.post("/api/v1/internal/jobs/flag-overdue")

    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == test_user.id,
            Notification.entity_type == "deal",
            Notification.entity_id == deal.id,
        )
    )
    assert len(result.scalars().all()) >= 1


@pytest.mark.asyncio
async def test_overdue_flag_cleared_on_closed_won(admin_client, db_session, test_user, test_account):
    """Transitioning to Closed Won via the API clears is_overdue atomically."""
    deal = await _insert_deal(db_session, test_user, test_account, date(2026, 1, 1))

    # Flag it overdue
    await admin_client.post("/api/v1/internal/jobs/flag-overdue")
    await db_session.refresh(deal)
    assert deal.is_overdue is True

    # Close it using admin_client (admin owns nothing but has no ownership restriction)
    # Need to use a client that can see the deal — admin bypasses team scope
    resp = await admin_client.post(
        f"/api/v1/deals/{deal.ref_id}/stage", json={"stage": "Closed Won"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_overdue"] is False


@pytest.mark.asyncio
async def test_already_closed_deals_not_reflagged(admin_client, db_session, test_user, test_account):
    """Closed Won deals are not touched by the overdue job."""
    deal = await _insert_deal(
        db_session, test_user, test_account, date(2026, 1, 1), stage=DealStage.CLOSED_WON
    )

    resp = await admin_client.post("/api/v1/internal/jobs/flag-overdue")
    assert resp.status_code == 200

    await db_session.refresh(deal)
    assert deal.is_overdue is False
