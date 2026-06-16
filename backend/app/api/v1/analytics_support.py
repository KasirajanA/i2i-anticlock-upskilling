from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.models.base import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import SupportReportResponse
from app.services.csv_streamer import CSVStreamer

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/reports/support", response_model=SupportReportResponse)
async def get_support_report(
    created_after: date | None = Query(None),
    created_before: date | None = Query(None),
    assignee_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SupportReportResponse:
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()

    if user.role == "Support Agent" and assignee_id is not None and assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Support Agents can only view their own data.")

    filters = {
        "created_after": created_after,
        "created_before": created_before,
        "assignee_id": assignee_id,
    }
    repo = AnalyticsRepository(session)
    return await repo.execute_support_report(filters, user)


@router.get("/reports/support/export")
async def export_support_report(
    created_after: date | None = Query(None),
    created_before: date | None = Query(None),
    assignee_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    if user.role == "Support Agent" and assignee_id is not None and assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Support Agents can only view their own data.")

    from app.models.support import Ticket  # noqa: PLC0415
    from sqlalchemy import select as sa_select  # noqa: PLC0415

    stmt = sa_select(Ticket.id, Ticket.subject, Ticket.status, Ticket.priority, Ticket.assignee_id, Ticket.created_at, Ticket.updated_at)
    if user.role == "Support Agent":
        stmt = stmt.where(Ticket.assignee_id == user.id)
    elif assignee_id:
        stmt = stmt.where(Ticket.assignee_id == assignee_id)
    if created_after:
        stmt = stmt.where(Ticket.created_at >= created_after)
    if created_before:
        stmt = stmt.where(Ticket.created_at <= created_before)

    rows_result = await session.execute(stmt)
    rows = [
        {
            "ticket_id": r.id,
            "subject": r.subject,
            "status": r.status,
            "priority": r.priority,
            "assignee_id": r.assignee_id,
            "created_at": str(r.created_at),
            "resolved_at": str(r.updated_at),
        }
        for r in rows_result.all()
    ]
    return CSVStreamer().stream(rows, ["ticket_id", "subject", "status", "priority", "assignee_id", "created_at", "resolved_at"], "support_report.csv")
