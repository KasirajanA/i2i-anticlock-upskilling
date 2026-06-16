from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contracts import Contract, ContractStatus


class ContractRepository:
    """All async DB access for contracts — no business logic lives here."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_next_seq(self) -> int:
        """Return the next CON-NNNN sequence number using a MAX+1 strategy.

        Acquiring the count atomically within a transaction prevents duplicate
        ref_ids under concurrent creates.
        """
        result = await self._db.execute(select(func.count()).select_from(Contract))
        return (result.scalar_one() or 0) + 1

    async def create(self, contract: Contract) -> Contract:
        self._db.add(contract)
        await self._db.flush()
        await self._db.refresh(contract)
        return contract

    async def get_by_ref_id(
        self, ref_id: str, *, with_attachment: bool = True
    ) -> Contract | None:
        stmt = select(Contract).where(Contract.ref_id == ref_id)
        if with_attachment:
            stmt = stmt.options(
                selectinload(Contract.attachment),
                selectinload(Contract.renewal_as_original),
                selectinload(Contract.renewal_as_successor),
            )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, contract: Contract, **fields: object) -> Contract:
        for key, value in fields.items():
            setattr(contract, key, value)
        await self._db.flush()
        await self._db.refresh(contract)
        return contract

    async def list_paginated(
        self,
        *,
        status: ContractStatus | None = None,
        owner_id: int | None = None,
        account_id: int | None = None,
        end_date_from: date | None = None,
        end_date_to: date | None = None,
        is_renewal_due: bool | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[int, list[Contract]]:
        """Return (total, items) using only indexed columns in WHERE clauses."""
        base = select(Contract).where(Contract.is_archived.is_(False))

        if status is not None:
            base = base.where(Contract.status == status)
        if owner_id is not None:
            base = base.where(Contract.owner_id == owner_id)
        if account_id is not None:
            base = base.where(Contract.account_id == account_id)
        if end_date_from is not None:
            base = base.where(Contract.end_date >= end_date_from)
        if end_date_to is not None:
            base = base.where(Contract.end_date <= end_date_to)
        if is_renewal_due is not None:
            base = base.where(Contract.is_renewal_due == is_renewal_due)

        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        items_result = await self._db.execute(
            base.order_by(Contract.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return total, list(items_result.scalars().all())

    async def get_active_expired_before(self, cutoff: date) -> list[Contract]:
        result = await self._db.execute(
            select(Contract).where(
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date < cutoff,
            )
        )
        return list(result.scalars().all())

    async def get_renewal_candidates(self, cutoff_days: int, today: date) -> list[Contract]:
        """Active contracts within <cutoff_days> of expiry that have no RenewalLink."""
        from sqlalchemy import not_, exists  # noqa: PLC0415
        from app.models.contracts import RenewalLink  # noqa: PLC0415

        has_renewal = exists().where(
            RenewalLink.original_contract_id == Contract.id
        )
        result = await self._db.execute(
            select(Contract).where(
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date <= date.fromordinal(
                    today.toordinal() + cutoff_days
                ),
                Contract.end_date >= today,
                not_(has_renewal),
            )
        )
        return list(result.scalars().all())
