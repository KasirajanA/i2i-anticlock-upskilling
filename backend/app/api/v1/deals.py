"""All /api/v1/deals route handlers and internal job trigger endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import (
    CurrentUser,
    get_current_user,
    require_roles,
    require_team_scope,
)
from app.repositories.activity_repository import ActivityRepository
from app.repositories.deal_repository import DealRepository
from app.schemas.activity_log import ActivityLogRead, ActivityLogResponse
from app.schemas.deal import (
    DealCreate,
    DealFilterParams,
    DealListResponse,
    DealRead,
    DealSummary,
    DealUpdate,
    StageChangeRequest,
    StageChangeResponse,
)
from app.schemas.deal_comment import CommentCreate, CommentListResponse, CommentRead
from app.services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])


def _svc(db: AsyncSession = Depends(get_session)) -> DealService:
    return DealService(db)


async def _get_deal_or_404(ref_id: str, db: AsyncSession) -> object:
    repo = DealRepository(db)
    deal = await repo.get_by_ref_id(ref_id)
    if deal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Deal '{ref_id}' not found")
    return deal


# ---------------------------------------------------------------------------
# List & Create
# ---------------------------------------------------------------------------

@router.get("", response_model=DealListResponse)
async def list_deals(
    filters: DealFilterParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> DealListResponse:
    repo = DealRepository(db)
    total, items = await repo.list_paginated(
        current_user=current_user,
        stage=filters.stage,
        owner_id=filters.owner_id,
        account_id=filters.account_id,
        is_overdue=filters.is_overdue,
        page=filters.page,
        limit=filters.limit,
    )
    return DealListResponse(
        total=total,
        page=filters.page,
        limit=filters.limit,
        items=[DealSummary.model_validate(d) for d in items],
    )


@router.post("", response_model=DealRead, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    svc: DealService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Manager", "Admin")),
    db: AsyncSession = Depends(get_session),
) -> DealRead:
    deal = await svc.create(payload, current_user)
    await db.commit()
    repo = DealRepository(db)
    deal = await repo.get_by_ref_id(deal.ref_id)
    return DealRead.model_validate(deal)


# ---------------------------------------------------------------------------
# Single deal CRUD
# ---------------------------------------------------------------------------

@router.get("/{ref_id}", response_model=DealRead)
async def get_deal(
    ref_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> DealRead:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    return DealRead.model_validate(deal)


@router.patch("/{ref_id}", response_model=DealRead)
async def update_deal(
    ref_id: str,
    payload: DealUpdate,
    svc: DealService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Manager", "Admin")),
    db: AsyncSession = Depends(get_session),
) -> DealRead:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    deal = await svc.update(deal, payload, current_user)
    await db.commit()
    repo = DealRepository(db)
    deal = await repo.get_by_ref_id(deal.ref_id)
    return DealRead.model_validate(deal)


# ---------------------------------------------------------------------------
# Stage transition
# ---------------------------------------------------------------------------

@router.post("/{ref_id}/stage", response_model=StageChangeResponse)
async def change_stage(
    ref_id: str,
    payload: StageChangeRequest,
    svc: DealService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Manager", "Admin")),
    db: AsyncSession = Depends(get_session),
) -> StageChangeResponse:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    previous_stage = deal.stage
    deal = await svc.change_stage(deal, payload.stage, payload.loss_reason, current_user)
    await db.commit()
    return StageChangeResponse(
        ref_id=ref_id,
        previous_stage=previous_stage,
        new_stage=deal.stage,
        is_overdue=deal.is_overdue,
        updated_at=deal.updated_at,
    )


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@router.get("/{ref_id}/comments", response_model=CommentListResponse)
async def list_comments(
    ref_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> CommentListResponse:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    repo = DealRepository(db)
    total, comments = await repo.get_comments_paginated(deal.id, page=page, limit=limit)
    return CommentListResponse(
        total=total,
        page=page,
        limit=limit,
        items=[CommentRead.model_validate(c) for c in comments],
    )


@router.post("/{ref_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ref_id: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> CommentRead:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    repo = DealRepository(db)
    activity = ActivityRepository(db)
    comment = await repo.add_comment(
        deal_id=deal.id, author_id=current_user.id, body=payload.body
    )
    await activity.insert_log(
        deal_id=deal.id,
        action_type="comment_added",
        actor_id=current_user.id,
        note=payload.body[:80],
    )
    await db.commit()
    return CommentRead.model_validate(comment)


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------

@router.get("/{ref_id}/activity", response_model=ActivityLogResponse)
async def get_activity(
    ref_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> ActivityLogResponse:
    deal = await _get_deal_or_404(ref_id, db)
    require_team_scope(deal.owner_id, current_user)
    activity_repo = ActivityRepository(db)
    entries = await activity_repo.fetch_for_deal(deal.id)
    return ActivityLogResponse(
        total=len(entries),
        items=[ActivityLogRead.model_validate(e) for e in entries],
    )


# ---------------------------------------------------------------------------
# Internal job triggers (Admin-only; for testing and on-demand execution)
# ---------------------------------------------------------------------------

internal_router = APIRouter(prefix="/internal/jobs", tags=["internal"])


@internal_router.post("/flag-overdue")
async def trigger_flag_overdue(
    _: CurrentUser = Depends(require_roles("Admin")),
    db: AsyncSession = Depends(get_session),
) -> dict:
    from app.scheduler.jobs import _run_flag_overdue_with_session  # noqa: PLC0415
    count = await _run_flag_overdue_with_session(db)
    await db.commit()
    return {"flagged": count}
