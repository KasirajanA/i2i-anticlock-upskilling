"""Unit tests for SLAEngine — due-date computation and breach detection."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support import SLARecord
from app.services.sla_engine import SLAEngine


def _make_sla(ticket_id: int, fr_due: datetime, res_due: datetime) -> SLARecord:
    return SLARecord(
        ticket_id=ticket_id,
        cycle=1,
        first_response_due=fr_due,
        resolution_due=res_due,
        is_active=True,
    )


@pytest.mark.parametrize(
    "priority,fr_hours,res_hours",
    [
        ("critical", 1, 4),
        ("high", 4, 24),
        ("medium", 8, 48),
        ("low", 24, 72),
    ],
)
def test_compute_due_dates(priority: str, fr_hours: int, res_hours: int):
    engine = SLAEngine()
    from_dt = datetime(2026, 6, 16, 9, 0, 0)
    fr, res = engine.compute_due_dates(priority, from_dt)
    assert fr == from_dt + timedelta(hours=fr_hours)
    assert res == from_dt + timedelta(hours=res_hours)


@pytest.mark.asyncio
async def test_check_breaches_sets_flag(
    db_session: AsyncSession, support_agent_user
):
    now = datetime.utcnow()
    # Insert a ticket stub
    from app.models.support import Ticket  # noqa: PLC0415

    ticket = Ticket(
        seq_number=501,
        subject="SLA Test",
        status="open",
        priority="critical",
        contact_name_snapshot="Tester",
        created_by_id=support_agent_user.id,
    )
    db_session.add(ticket)
    await db_session.flush()

    sla = _make_sla(
        ticket.id,
        fr_due=now - timedelta(hours=2),  # already past
        res_due=now + timedelta(hours=2),
    )
    db_session.add(sla)
    await db_session.flush()

    engine = SLAEngine()
    breached = await engine.check_breaches(db_session)
    assert ticket.id in breached
    assert sla.first_response_breached is True
    assert sla.resolution_breached is False


@pytest.mark.asyncio
async def test_already_breached_not_reflagged(
    db_session: AsyncSession, support_agent_user
):
    from app.models.support import Ticket  # noqa: PLC0415

    now = datetime.utcnow()
    ticket = Ticket(
        seq_number=502,
        subject="SLA Already Breached",
        status="open",
        priority="high",
        contact_name_snapshot="Tester",
        created_by_id=support_agent_user.id,
    )
    db_session.add(ticket)
    await db_session.flush()

    sla = SLARecord(
        ticket_id=ticket.id,
        cycle=1,
        first_response_due=now - timedelta(hours=5),
        resolution_due=now - timedelta(hours=2),
        first_response_breached=True,  # already flagged
        resolution_breached=False,
        is_active=True,
    )
    db_session.add(sla)
    await db_session.flush()

    engine = SLAEngine()
    breached = await engine.check_breaches(db_session)
    # Should not flag first_response again (already True)
    # Should flag resolution_breached (past due and not flagged)
    assert sla.resolution_breached is True


def test_is_warning_within_threshold():
    engine = SLAEngine()
    # 30 min from now → warning
    due = datetime.utcnow() + timedelta(minutes=30)
    assert engine.is_warning(due) is True


def test_is_warning_outside_threshold():
    engine = SLAEngine()
    # 2 hours from now → not warning
    due = datetime.utcnow() + timedelta(hours=2)
    assert engine.is_warning(due) is False
