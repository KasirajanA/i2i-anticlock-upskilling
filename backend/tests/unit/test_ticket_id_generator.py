"""Unit tests for TicketIDGenerator (sequential counter in ticket_service)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support import TicketSequence
from app.services.ticket_service import TicketService


@pytest.mark.asyncio
async def test_sequential_counter_increments(db_session: AsyncSession):
    svc = TicketService()
    seq1 = await svc._next_seq(db_session)
    seq2 = await svc._next_seq(db_session)
    seq3 = await svc._next_seq(db_session)
    assert seq1 < seq2 < seq3


@pytest.mark.asyncio
async def test_formats_as_i2i_crm_ref(db_session: AsyncSession):
    svc = TicketService()
    seq = await svc._next_seq(db_session)
    assert seq >= 1
    ref = f"I2I-CRM-{seq:04d}"
    assert ref.startswith("I2I-CRM-")
    assert len(ref) == 12  # "I2I-CRM-0001"


@pytest.mark.asyncio
async def test_first_seq_is_two_after_fixture_seed(db_session: AsyncSession):
    """Fixture seeds next_value=1; first UPDATE returns 2 (increments first)."""
    svc = TicketService()
    seq = await svc._next_seq(db_session)
    assert seq == 2
