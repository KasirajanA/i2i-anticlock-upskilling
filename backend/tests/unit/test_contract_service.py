"""T044: ContractService unit tests — transitions, renewals, attachment guard."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.models.contracts import Contract, ContractStatus
from app.services.contract_service import VALID_TRANSITIONS, ContractService


def _user(role: str = "Sales Rep", uid: int = 1) -> CurrentUser:
    return CurrentUser(id=uid, name="Test", email="t@t.com", role=role)


def _contract(
    owner_id: int = 1,
    status: ContractStatus = ContractStatus.DRAFT,
) -> Contract:
    c = Contract(
        id=1,
        ref_id="CON-0001",
        value=Decimal("1000.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=status,
        owner_id=owner_id,
        account_id=1,
    )
    return c


# ---------------------------------------------------------------------------
# VALID_TRANSITIONS table tests
# ---------------------------------------------------------------------------

def test_valid_transitions_sales_rep_forward():
    allowed = VALID_TRANSITIONS.get((ContractStatus.DRAFT, "Sales Rep"), set())
    assert ContractStatus.SENT_FOR_REVIEW in allowed


def test_valid_transitions_sales_rep_cannot_go_backward():
    allowed = VALID_TRANSITIONS.get((ContractStatus.SENT_FOR_REVIEW, "Sales Rep"), set())
    assert ContractStatus.DRAFT not in allowed


def test_valid_transitions_admin_can_revert():
    allowed = VALID_TRANSITIONS.get((ContractStatus.ACTIVE, "Admin"), set())
    assert ContractStatus.DRAFT in allowed
    assert ContractStatus.SENT_FOR_REVIEW in allowed


def test_valid_transitions_manager_forward_only():
    # Manager can go Draft → SFR
    assert ContractStatus.SENT_FOR_REVIEW in VALID_TRANSITIONS.get(
        (ContractStatus.DRAFT, "Manager"), set()
    )
    # Manager cannot revert
    assert ContractStatus.DRAFT not in VALID_TRANSITIONS.get(
        (ContractStatus.SENT_FOR_REVIEW, "Manager"), set()
    )


# ---------------------------------------------------------------------------
# Service transition tests (async, using real DB session from conftest)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transition_happy_path(db_session: AsyncSession, test_user, test_account):
    svc = ContractService(db_session)
    user = _user("Sales Rep", test_user.id)

    contract = Contract(
        ref_id="CON-0001",
        value=Decimal("500.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=ContractStatus.DRAFT,
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(contract)
    await db_session.flush()

    prev, _ = await svc.transition(
        contract, ContractStatus.SENT_FOR_REVIEW, None, user
    )
    assert prev == ContractStatus.DRAFT
    assert contract.status == ContractStatus.SENT_FOR_REVIEW


@pytest.mark.asyncio
async def test_transition_invalid_raises_400(db_session, test_user, test_account):
    svc = ContractService(db_session)
    user = _user("Sales Rep", test_user.id)

    contract = Contract(
        ref_id="CON-0002",
        value=Decimal("500.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=ContractStatus.DRAFT,
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(contract)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        # Sales Rep cannot jump Draft → Active
        await svc.transition(contract, ContractStatus.ACTIVE, None, user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_backward_without_note_raises_400(db_session, admin_user, test_account):
    svc = ContractService(db_session)
    admin = _user("Admin", admin_user.id)

    contract = Contract(
        ref_id="CON-0003",
        value=Decimal("500.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=ContractStatus.ACTIVE,
        owner_id=admin_user.id,
        account_id=test_account.id,
    )
    db_session.add(contract)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await svc.transition(contract, ContractStatus.DRAFT, note=None, current_user=admin)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_backward_raises_403(db_session, test_user, test_account):
    svc = ContractService(db_session)
    manager = _user("Manager", test_user.id)

    contract = Contract(
        ref_id="CON-0004",
        value=Decimal("500.00"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=ContractStatus.ACTIVE,
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(contract)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await svc.transition(contract, ContractStatus.DRAFT, note="reason", current_user=manager)
    assert exc.value.status_code == 403
