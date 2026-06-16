"""Unit tests for TicketService business logic."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import User
from app.models.contact import Contact
from app.models.support import SLARecord, Ticket
from app.services.ticket_service import TicketService


def _make_ticket(db_session, owner_id: int, contact_name: str = "Jane Doe") -> Ticket:
    return Ticket(
        seq_number=999,
        subject="Test Ticket",
        status="open",
        priority="high",
        contact_name_snapshot=contact_name,
        created_by_id=owner_id,
    )


@pytest.mark.asyncio
async def test_valid_open_to_in_progress_transition(
    db_session: AsyncSession, support_agent_user: User
):
    svc = TicketService()
    ticket = _make_ticket(db_session, support_agent_user.id)
    db_session.add(ticket)
    await db_session.flush()

    result = await svc.transition(
        db_session, ticket, "in_progress", support_agent_user.id, "Support Agent"
    )
    assert result.status == "in_progress"


@pytest.mark.asyncio
async def test_invalid_transition_raises_422(
    db_session: AsyncSession, support_agent_user: User
):
    """Completely unknown transition (not admin-only reversion) returns 422."""
    from fastapi import HTTPException

    svc = TicketService()
    ticket = _make_ticket(db_session, support_agent_user.id)
    ticket.status = "open"
    db_session.add(ticket)
    await db_session.flush()

    # open → closed is not in ALLOWED_TRANSITIONS and not in ADMIN_REVERSIONS → 422
    with pytest.raises(HTTPException) as exc:
        await svc.transition(
            db_session, ticket, "closed", support_agent_user.id, "Support Agent"
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_agent_revert_blocked_403(
    db_session: AsyncSession, support_agent_user: User
):
    from fastapi import HTTPException

    svc = TicketService()
    ticket = _make_ticket(db_session, support_agent_user.id)
    ticket.status = "in_progress"
    db_session.add(ticket)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await svc.transition(
            db_session, ticket, "open", support_agent_user.id, "Support Agent"
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_revert_status(
    db_session: AsyncSession, admin_user: User
):
    svc = TicketService()
    ticket = _make_ticket(db_session, admin_user.id)
    ticket.status = "in_progress"
    db_session.add(ticket)
    await db_session.flush()

    result = await svc.transition(
        db_session, ticket, "open", admin_user.id, "Admin"
    )
    assert result.status == "open"


@pytest.mark.asyncio
async def test_reopen_creates_new_sla_cycle(
    db_session: AsyncSession, support_agent_user: User
):
    svc = TicketService()
    ticket = _make_ticket(db_session, support_agent_user.id)
    ticket.status = "resolved"
    db_session.add(ticket)
    await db_session.flush()

    # Add active SLA for cycle 1
    now = datetime.utcnow()
    sla = SLARecord(
        ticket_id=ticket.id,
        cycle=1,
        first_response_due=now + timedelta(hours=4),
        resolution_due=now + timedelta(hours=24),
        is_active=True,
    )
    db_session.add(sla)
    await db_session.flush()

    await svc._reopen(db_session, ticket, support_agent_user.id)
    await db_session.flush()

    assert sla.is_active is False
    assert ticket.status == "open"

    # Check new SLA was created
    from sqlalchemy import select  # noqa: PLC0415
    result = await db_session.execute(
        select(SLARecord).where(
            SLARecord.ticket_id == ticket.id,
            SLARecord.is_active.is_(True),
        )
    )
    new_sla = result.scalar_one()
    assert new_sla.cycle == 2


@pytest.mark.asyncio
async def test_first_response_at_set_only_once(
    db_session: AsyncSession, support_agent_user: User
):
    svc = TicketService()
    ticket = _make_ticket(db_session, support_agent_user.id)
    db_session.add(ticket)
    await db_session.flush()

    now = datetime.utcnow()
    sla = SLARecord(
        ticket_id=ticket.id,
        cycle=1,
        first_response_due=now + timedelta(hours=4),
        resolution_due=now + timedelta(hours=24),
        is_active=True,
    )
    db_session.add(sla)
    await db_session.flush()

    # First non-internal reply
    await svc.add_reply(
        db_session, ticket, "First reply", False, support_agent_user.id
    )
    await db_session.refresh(sla)
    first_ts = sla.first_response_at
    assert first_ts is not None

    # Second non-internal reply — should NOT overwrite first_response_at
    await svc.add_reply(
        db_session, ticket, "Second reply", False, support_agent_user.id
    )
    await db_session.refresh(sla)
    assert sla.first_response_at == first_ts
