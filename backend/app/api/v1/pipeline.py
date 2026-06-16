"""Pipeline-level endpoints: forecast summary."""

from datetime import date
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.schemas.forecast import ForecastResponse
from app.services.deal_service import DealService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _current_quarter_bounds() -> tuple[date, date]:
    """Return (start, end) for the current calendar quarter."""
    today = date.today()
    q_start_month = ((today.month - 1) // 3) * 3 + 1
    q_end_month = q_start_month + 2
    last_day = monthrange(today.year, q_end_month)[1]
    return date(today.year, q_start_month, 1), date(today.year, q_end_month, last_day)


def _parse_period(period: str | None) -> tuple[date, date]:
    if period is None:
        return _current_quarter_bounds()
    parts = period.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "period must be in ISO range format: YYYY-MM-DD/YYYY-MM-DD",
        )
    try:
        start = date.fromisoformat(parts[0].strip())
        end = date.fromisoformat(parts[1].strip())
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "period dates must be valid ISO dates (YYYY-MM-DD)",
        )
    if start > end:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "period start must be before or equal to end",
        )
    return start, end


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    period: str | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
    _: CurrentUser = Depends(require_roles("Manager", "Admin")),
) -> ForecastResponse:
    period_start, period_end = _parse_period(period)
    svc = DealService(db)
    return await svc.get_forecast(period_start, period_end)
