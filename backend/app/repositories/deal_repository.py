"""Async repository for Deal CRUD and query operations."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser
from app.models.deal import Deal, DealComment, DealStage


class DealRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_next_seq(self) -> int:
        """MAX+1 sequential ref_id counter, safe within a transaction."""
        result = await self._db.execute(select(func.count()).select_from(Deal))
        return (result.scalar_one() or 0) + 1

    async def create(self, deal: Deal) -> Deal:
        self._db.add(deal)
        await self._db.flush()
        await self._db.refresh(deal)
        return deal

    async def get_by_ref_id(self, ref_id: str) -> Deal | None:
        stmt = (
            select(Deal)
            .where(Deal.ref_id == ref_id)
            .options(
                selectinload(Deal.owner),
                selectinload(Deal.account),
                selectinload(Deal.contact),
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, deal: Deal, **fields: object) -> Deal:
        fields["updated_at"] = datetime.utcnow()
        for key, value in fields.items():
            setattr(deal, key, value)
        await self._db.flush()
        await self._db.refresh(deal)
        return deal

    async def list_paginated(
        self,
        *,
        current_user: CurrentUser,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        account_id: int | None = None,
        is_overdue: bool | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> tuple[int, list[Deal]]:
        base = (
            select(Deal)
            .where(Deal.is_archived.is_(False))
            .options(
                selectinload(Deal.owner),
                selectinload(Deal.account),
                selectinload(Deal.contact),
            )
        )

        # FR-006: Sales Reps see only their own deals (team scope — Module 006 extends this)
        if current_user.role == "Sales Rep":
            base = base.where(Deal.owner_id == current_user.id)

        if stage is not None:
            base = base.where(Deal.stage == stage)
        if owner_id is not None:
            base = base.where(Deal.owner_id == owner_id)
        if account_id is not None:
            base = base.where(Deal.account_id == account_id)
        if is_overdue is not None:
            base = base.where(Deal.is_overdue == is_overdue)

        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        items_result = await self._db.execute(
            base.order_by(Deal.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return total, list(items_result.scalars().all())

    async def forecast_aggregate(
        self, period_start: date, period_end: date
    ) -> list[tuple[DealStage, int, Decimal]]:
        """Single GROUP BY query returning (stage, deal_count, sum_value) tuples.

        Excludes Closed Lost (probability 0) and archived deals.
        """
        result = await self._db.execute(
            select(
                Deal.stage,
                func.count().label("deal_count"),
                func.coalesce(func.sum(Deal.value), 0).label("total_value"),
            )
            .where(
                Deal.is_archived.is_(False),
                Deal.stage != DealStage.CLOSED_LOST,
                Deal.expected_close_date >= period_start,
                Deal.expected_close_date <= period_end,
            )
            .group_by(Deal.stage)
        )
        return [
            (row[0], row[1], Decimal(str(row[2])))
            for row in result.all()
        ]

    # -----------------------------------------------------------------------
    # Comments
    # -----------------------------------------------------------------------

    async def get_comments_paginated(
        self, deal_id: int, *, page: int = 1, limit: int = 25
    ) -> tuple[int, list[DealComment]]:
        base = (
            select(DealComment)
            .where(
                DealComment.deal_id == deal_id,
                DealComment.is_deleted.is_(False),
            )
            .options(selectinload(DealComment.author))
        )
        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        items_result = await self._db.execute(
            base.order_by(DealComment.created_at.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return total, list(items_result.scalars().all())

    async def add_comment(self, *, deal_id: int, author_id: int, body: str) -> DealComment:
        comment = DealComment(deal_id=deal_id, author_id=author_id, body=body)
        self._db.add(comment)
        await self._db.flush()
        # Eager-load author for serialization
        await self._db.refresh(comment)
        result = await self._db.execute(
            select(DealComment)
            .where(DealComment.id == comment.id)
            .options(selectinload(DealComment.author))
        )
        return result.scalar_one()
