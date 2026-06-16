from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.models.base import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import SalesReportResponse
from app.services.csv_streamer import CSVStreamer

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _load_user(current_user: CurrentUser, session: AsyncSession):
    return session.execute(select(User).where(User.id == current_user.id))


@router.get("/reports/sales", response_model=SalesReportResponse)
async def get_sales_report(
    created_after: date | None = Query(None),
    created_before: date | None = Query(None),
    owner_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SalesReportResponse:
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()

    # Sales Rep cannot request another owner's data
    if user.role == "Sales Rep" and owner_id is not None and owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sales Reps can only view their own data.")

    if created_after and created_before and created_after > created_before:
        raise HTTPException(status_code=422, detail="created_after must be before created_before.")

    filters = {
        "created_after": created_after,
        "created_before": created_before,
        "owner_id": owner_id,
    }
    repo = AnalyticsRepository(session)
    return await repo.execute_sales_report(filters, user)


@router.get("/reports/sales/export")
async def export_sales_report(
    created_after: date | None = Query(None),
    created_before: date | None = Query(None),
    owner_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    if user.role == "Sales Rep" and owner_id is not None and owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sales Reps can only view their own data.")

    from app.models.deal import Deal  # noqa: PLC0415
    from app.services.report_query_builder import ReportQueryBuilder  # noqa: PLC0415

    qb = (
        ReportQueryBuilder(session)
        .with_role_scope(user)
        .with_owner(owner_id)
        .with_date_range(created_after, created_before)
    )
    from sqlalchemy import select as sa_select  # noqa: PLC0415
    stmt = sa_select(
        Deal.id, Deal.title, Deal.owner_id, Deal.stage, Deal.value, Deal.expected_close_date, Deal.created_at
    )
    if qb._owner_id:
        stmt = stmt.where(Deal.owner_id == qb._owner_id)
    if qb._date_after:
        stmt = stmt.where(Deal.created_at >= qb._date_after)
    if qb._date_before:
        stmt = stmt.where(Deal.created_at <= qb._date_before)

    rows_result = await session.execute(stmt)
    rows = [
        {
            "deal_id": r.id,
            "title": r.title,
            "owner_id": r.owner_id,
            "stage": r.stage,
            "value": str(r.value),
            "close_date": str(r.expected_close_date),
            "created_at": str(r.created_at),
        }
        for r in rows_result.all()
    ]
    return CSVStreamer().stream(rows, ["deal_id", "title", "owner_id", "stage", "value", "close_date", "created_at"], "sales_report.csv")
