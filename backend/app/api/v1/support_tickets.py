"""Support ticket CRUD, status transition, and SLA endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user, require_roles
from app.repositories.sqlite_ticket_repository import SqliteTicketRepository
from app.schemas.support import (
    AssignRequest,
    SLAListResponse,
    SLARecordRead,
    TicketCreate,
    TicketListResponse,
    TicketRead,
    TicketSummary,
    TicketUpdate,
    SLASummary,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/support/tickets", tags=["support-tickets"])
_svc = TicketService()
_repo = SqliteTicketRepository()


def _get_svc() -> TicketService:
    return _svc


def _get_repo() -> SqliteTicketRepository:
    return _repo


async def _get_ticket_or_404(ticket_id: int, session: AsyncSession, repo: SqliteTicketRepository):
    pair = await repo.get_by_id(session, ticket_id)
    if pair is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return pair


def _to_summary(ticket, sla) -> TicketSummary:
    sla_summary: SLASummary | None = None
    if sla:
        from app.services.sla_engine import SLAEngine  # noqa: PLC0415
        eng = SLAEngine()
        sla_summary = SLASummary(
            first_response_due=sla.first_response_due,
            resolution_due=sla.resolution_due,
            first_response_breached=sla.first_response_breached,
            resolution_breached=sla.resolution_breached,
            warning=eng.is_warning(sla.first_response_due),
        )
    return TicketSummary(
        id=ticket.id,
        ref=f"I2I-CRM-{ticket.seq_number:04d}",
        subject=ticket.subject,
        status=ticket.status,
        priority=ticket.priority,
        contact_name=ticket.contact_name_snapshot,
        assignee_id=ticket.assignee_id,
        sla=sla_summary,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


@router.post("", status_code=201, response_model=TicketRead)
async def create_ticket(
    payload: TicketCreate,
    current_user: CurrentUser = Depends(
        require_roles("Admin", "Support Agent")
    ),
    db: AsyncSession = Depends(get_session),
    svc: TicketService = Depends(_get_svc),
):
    ticket, sla = await svc.create_ticket(db, payload, current_user.id)
    await db.commit()
    return TicketRead.from_orm_with_ref(ticket, sla)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    queue: str | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    account_id: int | None = Query(default=None),
    created_after: str | None = Query(default=None),
    created_before: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
):
    pairs, next_cursor, total = await repo.list_paginated(
        db,
        queue=queue,
        caller_id=current_user.id,
        status=status_,
        priority=priority,
        assignee_id=assignee_id,
        account_id=account_id,
        created_after=created_after,
        created_before=created_before,
        cursor=cursor,
        limit=limit,
    )
    items = [_to_summary(t, s) for t, s in pairs]
    return TicketListResponse(items=items, next_cursor=next_cursor, total=total)


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
):
    ticket, sla = await _get_ticket_or_404(ticket_id, db, repo)
    return TicketRead.from_orm_with_ref(ticket, sla)


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
    svc: TicketService = Depends(_get_svc),
):
    ticket, sla = await _get_ticket_or_404(ticket_id, db, repo)

    if payload.status and payload.status != ticket.status:
        ticket = await svc.transition(
            db, ticket, payload.status, current_user.id, current_user.role
        )

    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.subject is not None:
        ticket.subject = payload.subject
    if payload.description is not None:
        ticket.description = payload.description
    if payload.assignee_id is not None:
        ticket.assignee_id = payload.assignee_id

    ticket = await repo.update(db, ticket)
    await db.commit()
    sla = await repo._active_sla(db, ticket.id)
    return TicketRead.from_orm_with_ref(ticket, sla)


@router.post("/{ticket_id}/assign", response_model=TicketRead)
async def assign_ticket(
    ticket_id: int,
    payload: AssignRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
    svc: TicketService = Depends(_get_svc),
):
    ticket, sla = await _get_ticket_or_404(ticket_id, db, repo)
    ticket = await svc.assign(
        db, ticket, payload.assignee_id, current_user.id, current_user.role
    )
    await db.commit()
    sla = await repo._active_sla(db, ticket.id)
    return TicketRead.from_orm_with_ref(ticket, sla)


@router.get("/{ticket_id}/sla", response_model=SLAListResponse)
async def get_ticket_sla(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
):
    pair = await repo.get_by_id(db, ticket_id)
    if pair is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    records = await repo.get_all_sla(db, ticket_id)
    return SLAListResponse(items=[SLARecordRead.model_validate(r) for r in records])
