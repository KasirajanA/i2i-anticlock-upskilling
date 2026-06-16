"""SLA policy enforcement: due-date computation and breach detection."""

from datetime import datetime, timedelta

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support import SLARecord

SLA_POLICY: dict[str, dict[str, int]] = {
    "critical": {"first_response_hours": 1, "resolution_hours": 4},
    "high": {"first_response_hours": 4, "resolution_hours": 24},
    "medium": {"first_response_hours": 8, "resolution_hours": 48},
    "low": {"first_response_hours": 24, "resolution_hours": 72},
}

# Test-only clock offset (seconds). Adjusted via /api/v1/_test/sla/advance-clock.
_clock_offset_seconds: int = 0


def _now() -> datetime:
    return datetime.utcnow() + timedelta(seconds=_clock_offset_seconds)


class SLAEngine:
    def __init__(self, policy: dict[str, dict[str, int]] = SLA_POLICY) -> None:
        self._policy = policy

    def compute_due_dates(
        self, priority: str, from_dt: datetime
    ) -> tuple[datetime, datetime]:
        p = self._policy[priority]
        first_response_due = from_dt + timedelta(hours=p["first_response_hours"])
        resolution_due = from_dt + timedelta(hours=p["resolution_hours"])
        return first_response_due, resolution_due

    def is_warning(self, due: datetime, warning_hours: int = 1) -> bool:
        """Return True if the due time is within `warning_hours` but not yet breached."""
        now = _now()
        return now < due and (due - now) <= timedelta(hours=warning_hours)

    async def check_breaches(self, session: AsyncSession) -> list[int]:
        """Flag newly breached SLA records; return affected ticket IDs."""
        now = _now()

        # Flag first_response_breached
        result = await session.execute(
            select(SLARecord).where(
                and_(
                    SLARecord.is_active.is_(True),
                    SLARecord.first_response_breached.is_(False),
                    SLARecord.first_response_at.is_(None),
                    SLARecord.first_response_due <= now,
                )
            )
        )
        fr_records = list(result.scalars().all())
        for rec in fr_records:
            rec.first_response_breached = True

        # Flag resolution_breached
        result2 = await session.execute(
            select(SLARecord).where(
                and_(
                    SLARecord.is_active.is_(True),
                    SLARecord.resolution_breached.is_(False),
                    SLARecord.resolved_at.is_(None),
                    SLARecord.resolution_due <= now,
                )
            )
        )
        res_records = list(result2.scalars().all())
        for rec in res_records:
            rec.resolution_breached = True

        await session.flush()

        breached_ids = list(
            {r.ticket_id for r in fr_records} | {r.ticket_id for r in res_records}
        )
        return breached_ids
