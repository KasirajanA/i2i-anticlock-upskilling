from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.repositories.sqlite_segment_repository import SqliteSegmentRepository
from app.schemas.contact import SegmentResponse
from app.services.filter_query_builder import FilterQueryBuilder


class SegmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._repo = SqliteSegmentRepository(session)

    async def create(
        self,
        name: str,
        entity_type: str,
        filter_spec: dict,
        owner_id: int | None,
    ) -> SegmentResponse:
        builder = FilterQueryBuilder()
        builder.validate_spec(filter_spec)

        seg = await self._repo.create(name, entity_type, filter_spec, owner_id)
        live_count = await self._compute_count(filter_spec)
        resp = SegmentResponse.model_validate(seg)
        resp.live_count = live_count
        return resp

    async def list(
        self,
        owner_id: int | None = None,
        entity_type: str | None = None,
    ) -> list[SegmentResponse]:
        segs = await self._repo.list(owner_id=owner_id, entity_type=entity_type)
        results = []
        for seg in segs:
            count = await self._compute_count(seg.filter_spec)
            resp = SegmentResponse.model_validate(seg)
            resp.live_count = count
            results.append(resp)
        return results

    async def get_live_count(self, segment_id: int) -> int:
        seg = await self._repo.get_by_id(segment_id)
        if seg is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Segment not found.")
        return await self._compute_count(seg.filter_spec)

    async def _compute_count(self, filter_spec: dict) -> int:
        builder = FilterQueryBuilder()
        for cond in filter_spec.get("conditions", []):
            builder.add(cond.get("field", ""), cond.get("operator", "eq"), cond.get("value", ""))
        query = builder.build(select(func.count()).select_from(Contact).where(Contact.deleted_at.is_(None)))
        return (await self._db.execute(query)).scalar_one()
