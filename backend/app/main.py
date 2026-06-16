from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.contracts import internal_router, router as contracts_router
from app.api.v1.deals import internal_router as deals_internal_router
from app.api.v1.deals import router as deals_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.support_tickets import router as support_tickets_router
from app.api.v1.support_replies import router as support_replies_router
from app.api.v1.support_activity import router as support_activity_router
from app.api.v1.analytics_dashboard import router as analytics_dashboard_router
from app.api.v1.analytics_sales import router as analytics_sales_router
from app.api.v1.analytics_support import router as analytics_support_router
from app.api.v1.analytics_contracts import router as analytics_contracts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.users import router as users_router
from app.api.v1.user_password import router as user_password_router
from app.api.v1.teams import router as teams_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.leads import router as leads_router
from app.api.v1.segments import router as segments_router
from app.api.v1.custom_fields import router as custom_fields_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start/stop background scheduler at application lifecycle boundaries."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: PLC0415
        from apscheduler.triggers.cron import CronTrigger  # noqa: PLC0415
        from apscheduler.triggers.interval import IntervalTrigger  # noqa: PLC0415
        from app.scheduler.jobs import (  # noqa: PLC0415
            expire_contracts,
            flag_renewals,
            flag_overdue_deals,
            sla_breach_job,
        )

        scheduler = AsyncIOScheduler()
        # Nightly at 01:00 — expire overdue Active contracts
        scheduler.add_job(expire_contracts, CronTrigger(hour=1, minute=0), id="expire_contracts")
        # Nightly at 02:00 — flag contracts approaching renewal
        scheduler.add_job(flag_renewals, CronTrigger(hour=2, minute=0), id="flag_renewals")
        # Nightly at 01:00 UTC — flag overdue open deals
        scheduler.add_job(flag_overdue_deals, CronTrigger(hour=1, minute=0), id="flag_overdue_deals")
        # Every 5 minutes — detect SLA breaches
        scheduler.add_job(sla_breach_job, IntervalTrigger(minutes=5), id="sla_breach_job")
        scheduler.start()
        app.state.scheduler = scheduler
        yield
        scheduler.shutdown(wait=False)
    except Exception:
        # If APScheduler is unavailable (e.g., test environment), skip gracefully
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="CRM — Contract Management API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(contracts_router, prefix="/api/v1")
    app.include_router(internal_router, prefix="/api/v1")
    app.include_router(deals_router, prefix="/api/v1")
    app.include_router(deals_internal_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")
    app.include_router(support_tickets_router, prefix="/api/v1")
    app.include_router(support_replies_router, prefix="/api/v1")
    app.include_router(support_activity_router, prefix="/api/v1")
    app.include_router(analytics_dashboard_router, prefix="/api/v1")
    app.include_router(analytics_sales_router, prefix="/api/v1")
    app.include_router(analytics_support_router, prefix="/api/v1")
    app.include_router(analytics_contracts_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(admin_users_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(user_password_router, prefix="/api/v1")
    app.include_router(teams_router, prefix="/api/v1")
    app.include_router(contacts_router, prefix="/api/v1")
    app.include_router(accounts_router, prefix="/api/v1")
    app.include_router(leads_router, prefix="/api/v1")
    app.include_router(segments_router, prefix="/api/v1")
    app.include_router(custom_fields_router, prefix="/api/v1")

    _avatars_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "avatars")
    os.makedirs(_avatars_dir, exist_ok=True)
    app.mount("/static/avatars", StaticFiles(directory=_avatars_dir), name="avatars")

    return app


app = create_app()
