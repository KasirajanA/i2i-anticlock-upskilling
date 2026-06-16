from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.models.base import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import ContractReportResponse
from app.services.csv_streamer import CSVStreamer

router = APIRouter(prefix="/analytics", tags=["analytics"])

VALID_WINDOWS = {30, 60, 90}


@router.get("/reports/contracts", response_model=ContractReportResponse)
async def get_contract_report(
    renewal_window: int = Query(30),
    owner_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContractReportResponse:
    if renewal_window not in VALID_WINDOWS:
        raise HTTPException(status_code=422, detail=f"renewal_window must be one of {sorted(VALID_WINDOWS)}.")

    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()

    if user.role == "Sales Rep" and owner_id is not None and owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sales Reps can only view their own data.")

    filters = {"renewal_window": renewal_window, "owner_id": owner_id}
    repo = AnalyticsRepository(session)
    return await repo.execute_contract_report(filters, user)


@router.get("/reports/contracts/export")
async def export_contract_report(
    renewal_window: int = Query(30),
    owner_id: int | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if renewal_window not in VALID_WINDOWS:
        raise HTTPException(status_code=422, detail=f"renewal_window must be one of {sorted(VALID_WINDOWS)}.")

    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    if user.role == "Sales Rep" and owner_id is not None and owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sales Reps can only view their own data.")

    from datetime import date  # noqa: PLC0415
    from app.models.contracts import Contract  # noqa: PLC0415
    from sqlalchemy import select as sa_select  # noqa: PLC0415
    from app.services.report_query_builder import ReportQueryBuilder  # noqa: PLC0415

    qb = ReportQueryBuilder(session).with_role_scope(user).with_owner(owner_id)
    stmt = sa_select(Contract.id, Contract.ref_id, Contract.account_id, Contract.owner_id, Contract.status, Contract.value, Contract.start_date, Contract.end_date)
    if qb._owner_id:
        stmt = stmt.where(Contract.owner_id == qb._owner_id)

    rows_result = await session.execute(stmt)
    today = date.today()
    rows = [
        {
            "contract_id": r.id,
            "ref_id": r.ref_id,
            "account_id": r.account_id,
            "owner_id": r.owner_id,
            "status": r.status,
            "value": str(r.value),
            "start_date": str(r.start_date),
            "expiry_date": str(r.end_date),
            "days_remaining": (r.end_date - today).days if r.end_date else None,
        }
        for r in rows_result.all()
    ]
    columns = ["contract_id", "ref_id", "account_id", "owner_id", "status", "value", "start_date", "expiry_date", "days_remaining"]
    return CSVStreamer().stream(rows, columns, "contracts_report.csv")
