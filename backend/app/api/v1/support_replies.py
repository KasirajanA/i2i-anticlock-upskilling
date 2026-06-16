"""Reply and internal note endpoints for support tickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.repositories.sqlite_ticket_repository import SqliteTicketRepository
from app.schemas.support import ReplyCreate, ReplyListResponse, ReplyRead
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/support/tickets", tags=["support-replies"])
_svc = TicketService()
_repo = SqliteTicketRepository()


def _get_svc() -> TicketService:
    return _svc


def _get_repo() -> SqliteTicketRepository:
    return _repo


AGENT_ROLES = {"Admin", "Support Agent"}


@router.get("/{ticket_id}/replies", response_model=ReplyListResponse)
async def list_replies(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
):
    pair = await repo.get_by_id(db, ticket_id)
    if pair is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    include_internal = current_user.role in AGENT_ROLES
    replies = await repo.get_replies(db, ticket_id, include_internal=include_internal)
    return ReplyListResponse(items=[ReplyRead.model_validate(r) for r in replies])


@router.post("/{ticket_id}/replies", status_code=201, response_model=ReplyRead)
async def add_reply(
    ticket_id: int,
    payload: ReplyCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
    svc: TicketService = Depends(_get_svc),
):
    pair = await repo.get_by_id(db, ticket_id)
    if pair is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket, _ = pair

    reply = await svc.add_reply(
        db, ticket, payload.body, payload.is_internal, current_user.id
    )
    await db.commit()
    await db.refresh(reply)
    return ReplyRead.model_validate(reply)
