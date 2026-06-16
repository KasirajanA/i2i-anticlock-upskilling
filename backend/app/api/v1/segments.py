from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.contact import SegmentRequest, SegmentResponse
from app.services.segment_service import SegmentService

router = APIRouter(prefix="/segments", tags=["segments"])


@router.get("", response_model=list[SegmentResponse])
async def list_segments(
    entity_type: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[SegmentResponse]:
    svc = SegmentService(session)
    return await svc.list(owner_id=current_user.id, entity_type=entity_type)


@router.post("", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    payload: SegmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SegmentResponse:
    if current_user.role == "Support Agent":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
    svc = SegmentService(session)
    return await svc.create(
        payload.name,
        payload.entity_type,
        payload.filter_spec,
        current_user.id,
    )


@router.get("/{segment_id}/count")
async def get_segment_count(
    segment_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    svc = SegmentService(session)
    count = await svc.get_live_count(segment_id)
    return {"count": count}
