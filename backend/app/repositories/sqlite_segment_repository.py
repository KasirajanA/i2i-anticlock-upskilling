from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Segment


class SqliteSegmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create(
        self,
        name: str,
        entity_type: str,
        filter_spec: dict,
        owner_id: int | None,
    ) -> Segment:
        seg = Segment(name=name, entity_type=entity_type, filter_spec=filter_spec, owner_id=owner_id)
        self._db.add(seg)
        await self._db.commit()
        await self._db.refresh(seg)
        return seg

    async def list(self, owner_id: int | None = None, entity_type: str | None = None) -> list[Segment]:
        q = select(Segment)
        if owner_id:
            q = q.where(Segment.owner_id == owner_id)
        if entity_type:
            q = q.where(Segment.entity_type == entity_type)
        q = q.order_by(Segment.created_at)
        return list((await self._db.execute(q)).scalars().all())

    async def get_by_id(self, id: int) -> Segment | None:
        return await self._db.get(Segment, id)

    async def delete(self, id: int) -> None:
        seg = await self._db.get(Segment, id)
        if seg:
            await self._db.delete(seg)
            await self._db.commit()
