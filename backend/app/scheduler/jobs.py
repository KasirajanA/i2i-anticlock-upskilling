"""APScheduler jobs — each job also reachable via an Admin-only HTTP trigger endpoint.

Each job has two layers:
  - `_run_*_with_session(db)`: contains the actual logic; accepts an AsyncSession
  - `expire_contracts()` / `flag_renewals()`: cron entry-points that create their own session

This separation lets HTTP trigger endpoints pass the request's session (testable)
while the cron scheduler uses its own session factory.
"""

from datetime import date, timedelta

from sqlalchemy import exists, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.contracts import ActivityLog, Contract, ContractStatus, RenewalLink

_SYSTEM_ACTOR_ID = 0


async def _run_expire_with_session(db: AsyncSession) -> int:
    today = date.today()
    result = await db.execute(
        select(Contract).where(
            Contract.status == ContractStatus.ACTIVE,
            Contract.end_date < today,
        )
    )
    contracts = result.scalars().all()
    for c in contracts:
        c.status = ContractStatus.EXPIRED
        db.add(
            ActivityLog(
                contract_id=c.id,
                action_type="status_transition",
                actor_id=_SYSTEM_ACTOR_ID,
                note="Auto-expired by nightly job",
            )
        )
    return len(contracts)


async def expire_contracts() -> int:
    """Cron entry-point: expire overdue Active contracts."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            return await _run_expire_with_session(db)


async def _run_flag_renewals_with_session(
    db: AsyncSession, renewal_window_days: int = 30
) -> int:
    today = date.today()
    cutoff = today + timedelta(days=renewal_window_days)

    has_renewal = exists().where(RenewalLink.original_contract_id == Contract.id)
    result = await db.execute(
        select(Contract).where(
            Contract.status == ContractStatus.ACTIVE,
            Contract.end_date <= cutoff,
            Contract.end_date >= today,
            Contract.is_renewal_due.is_(False),
            not_(has_renewal),
        )
    )
    contracts = result.scalars().all()
    for c in contracts:
        c.is_renewal_due = True
        db.add(
            ActivityLog(
                contract_id=c.id,
                action_type="renewal_flagged",
                actor_id=_SYSTEM_ACTOR_ID,
                note=f"Renewal due within {renewal_window_days} days",
            )
        )
    return len(contracts)


async def flag_renewals(renewal_window_days: int = 30) -> int:
    """Cron entry-point: flag contracts approaching renewal."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            return await _run_flag_renewals_with_session(db, renewal_window_days)


# ---------------------------------------------------------------------------
# Sales Pipeline: overdue deal flagging
# ---------------------------------------------------------------------------

async def _run_flag_overdue_with_session(db: AsyncSession) -> int:
    """Flag open deals where expected_close_date < today.

    Inserts one notification per affected deal owner and writes an
    activity log entry on each deal. Clears flag atomically when called
    after a terminal stage change (handled in DealService.change_stage).
    """
    from datetime import date  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415
    from app.models.deal import Deal, DealActivity, DealStage  # noqa: PLC0415
    from app.models.base import Notification  # noqa: PLC0415

    today = date.today()
    result = await db.execute(
        select(Deal).where(
            Deal.is_archived.is_(False),
            Deal.is_overdue.is_(False),
            Deal.stage.notin_([DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value]),
            Deal.expected_close_date < today,
        )
    )
    deals = result.scalars().all()

    for deal in deals:
        deal.is_overdue = True
        db.add(
            DealActivity(
                deal_id=deal.id,
                action_type="overdue_flagged",
                actor_id=_SYSTEM_ACTOR_ID,
                note=f"Expected close date {deal.expected_close_date} has passed",
            )
        )
        db.add(
            Notification(
                user_id=deal.owner_id,
                message=f"Deal {deal.ref_id} is overdue — expected close date has passed",
                entity_type="deal",
                entity_id=deal.id,
            )
        )

    return len(deals)


async def flag_overdue_deals() -> int:
    """Cron entry-point: flag overdue open deals and notify owners."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            return await _run_flag_overdue_with_session(db)


# ---------------------------------------------------------------------------
# Customer Support: SLA breach detection
# ---------------------------------------------------------------------------

async def _run_sla_breach_with_session(db: AsyncSession) -> list[int]:
    """Detect newly breached SLA records and notify all Admin users."""
    from sqlalchemy import select  # noqa: PLC0415
    from app.models.base import Notification, User  # noqa: PLC0415
    from app.services.sla_engine import SLAEngine  # noqa: PLC0415
    from app.models.support import Ticket  # noqa: PLC0415

    engine = SLAEngine()
    breached_ids = await engine.check_breaches(db)

    if breached_ids:
        admin_result = await db.execute(
            select(User).where(User.role == "Admin", User.is_active.is_(True))
        )
        admins = admin_result.scalars().all()

        for ticket_id in breached_ids:
            ticket_result = await db.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            ticket = ticket_result.scalar_one_or_none()
            if not ticket:
                continue
            ref = f"I2I-CRM-{ticket.seq_number:04d}"
            for admin in admins:
                db.add(
                    Notification(
                        user_id=admin.id,
                        message=f"SLA breach detected for ticket {ref}.",
                        entity_type="ticket",
                        entity_id=ticket_id,
                    )
                )
        await db.flush()

    return breached_ids


async def sla_breach_job() -> list[int]:
    """Cron entry-point: detect SLA breaches and notify admins (every 5 min)."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            return await _run_sla_breach_with_session(db)
