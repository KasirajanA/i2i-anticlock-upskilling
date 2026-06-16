from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import DashboardResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    from app.models.base import User  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415
    user = (await session.execute(select(User).where(User.id == current_user.id))).scalar_one()
    repo = AnalyticsRepository(session)
    return await repo.get_dashboard(user)
