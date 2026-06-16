from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Lead
from app.schemas.contact import PaginatedLeads


class SqliteLeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create(self, data: dict) -> Lead:
        lead = Lead(**data)
        self._db.add(lead)
        await self._db.commit()
        await self._db.refresh(lead)
        return lead

    async def get_by_id(self, id: int) -> Lead | None:
        q = select(Lead).where(Lead.id == id, Lead.deleted_at.is_(None))
        return (await self._db.execute(q)).scalar_one_or_none()

    async def list(
        self,
        status: str | None = None,
        owner_id: int | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedLeads:
        base = select(Lead).where(Lead.deleted_at.is_(None))
        if status:
            base = base.where(Lead.status == status)
        if owner_id:
            base = base.where(Lead.owner_id == owner_id)
        if q:
            pattern = f"%{q}%"
            base = base.where(
                Lead.first_name.ilike(pattern)
                | Lead.last_name.ilike(pattern)
                | Lead.email.ilike(pattern)
            )

        total = (await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar_one()

        base = base.order_by(Lead.id).limit(limit)
        rows = list((await self._db.execute(base)).scalars().all())
        return PaginatedLeads(items=rows, total=total)

    async def update(self, id: int, fields: dict) -> Lead | None:
        lead = await self._db.get(Lead, id)
        if lead is None:
            return None
        for k, v in fields.items():
            setattr(lead, k, v)
        lead.updated_at = datetime.utcnow()
        await self._db.commit()
        await self._db.refresh(lead)
        return lead

    async def archive(self, id: int, reason: str | None = None) -> Lead | None:
        lead = await self._db.get(Lead, id)
        if lead:
            lead.deleted_at = datetime.utcnow()
            if reason:
                lead.disqualify_reason = reason
            await self._db.commit()
        return lead
