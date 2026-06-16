"""Activity log endpoint for support tickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.repositories.sqlite_ticket_repository import SqliteTicketRepository
from app.schemas.support import ActivityLogRead, ActivityLogResponse

router = APIRouter(prefix="/support/tickets", tags=["support-activity"])
_repo = SqliteTicketRepository()


def _get_repo() -> SqliteTicketRepository:
    return _repo


@router.get("/{ticket_id}/activity", response_model=ActivityLogResponse)
async def get_activity(
    ticket_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    repo: SqliteTicketRepository = Depends(_get_repo),
):
    pair = await repo.get_by_id(db, ticket_id)
    if pair is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    entries = await repo.get_activity(db, ticket_id)
    return ActivityLogResponse(
        items=[ActivityLogRead.model_validate(e) for e in entries]
    )
