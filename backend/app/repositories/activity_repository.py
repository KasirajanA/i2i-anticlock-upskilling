"""Async repository for deal activity log entries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal import DealActivity


class ActivityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def insert_log(
        self,
        *,
        deal_id: int,
        action_type: str,
        actor_id: int,
        note: str | None = None,
    ) -> DealActivity:
        entry = DealActivity(
            deal_id=deal_id,
            action_type=action_type,
            actor_id=actor_id,
            note=note,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def fetch_for_deal(self, deal_id: int) -> list[DealActivity]:
        result = await self._db.execute(
            select(DealActivity)
            .where(DealActivity.deal_id == deal_id)
            .options(selectinload(DealActivity.actor))
            .order_by(DealActivity.created_at.asc())
        )
        return list(result.scalars().all())
