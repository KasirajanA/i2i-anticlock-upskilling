from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import User
from app.models.contact import Account
from app.models.contracts import Contract
from app.models.deal import Deal, DealStage
from app.models.support import SLARecord, Ticket
from app.schemas.analytics import (
    AccountValue,
    ContractReportResponse,
    DashboardResponse,
    PerAgentCount,
    PriorityBreakdownItem,
    RepRevenue,
    ReportFiltersApplied,
    SalesReportResponse,
    StageBreakdownItem,
    StatusBreakdownItem,
    StatusValueItem,
    SupportReportResponse,
    UpcomingRenewal,
    WidgetItem,
)
from app.services.cache_manager import CacheManager, ReportCacheKey
from app.services.report_query_builder import ReportQueryBuilder

_cache = CacheManager()


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Dashboard widgets
    # ------------------------------------------------------------------

    async def get_dashboard(self, user: User) -> DashboardResponse:
        widgets: list[WidgetItem] = []

        if user.role in ("Sales Rep", "Admin"):
            open_deals, pipeline_value, closing_month, overdue = await asyncio.gather(
                self._count(
                    select(func.count(Deal.id)).where(
                        Deal.stage.notin_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]),
                        Deal.owner_id == user.id if user.role == "Sales Rep" else True,
                    )
                ),
                self._scalar(
                    select(func.coalesce(func.sum(Deal.value), 0)).where(
                        Deal.stage.notin_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]),
                        Deal.owner_id == user.id if user.role == "Sales Rep" else True,
                    )
                ),
                self._count(
                    select(func.count(Deal.id)).where(
                        Deal.expected_close_date >= date.today().replace(day=1),
                        Deal.expected_close_date < (date.today().replace(day=1) + timedelta(days=32)).replace(day=1),
                        Deal.owner_id == user.id if user.role == "Sales Rep" else True,
                    )
                ),
                self._count(
                    select(func.count(Deal.id)).where(
                        Deal.expected_close_date < date.today(),
                        Deal.stage.notin_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]),
                        Deal.owner_id == user.id if user.role == "Sales Rep" else True,
                    )
                ),
            )
            widgets += [
                WidgetItem(key="open_deals_count", label="Open Deals", value=open_deals),
                WidgetItem(key="pipeline_value", label="Pipeline Value", value=float(pipeline_value), unit="$"),
                WidgetItem(key="deals_closing_this_month", label="Closing This Month", value=closing_month),
                WidgetItem(key="overdue_deals", label="Overdue Deals", value=overdue),
            ]

        if user.role in ("Support Agent", "Admin"):
            owner_filter = (Ticket.assignee_id == user.id) if user.role == "Support Agent" else True
            open_tickets, sla_breaches, resolved_week = await asyncio.gather(
                self._count(
                    select(func.count(Ticket.id)).where(
                        Ticket.status.in_(["open", "in_progress"]),
                        owner_filter,
                    )
                ),
                self._count(
                    select(func.count(SLARecord.id)).where(
                        SLARecord.first_response_breached == True,  # noqa: E712
                        SLARecord.is_active == True,  # noqa: E712
                    )
                ),
                self._count(
                    select(func.count(Ticket.id)).where(
                        Ticket.status == "resolved",
                        Ticket.updated_at >= datetime.utcnow() - timedelta(days=7),
                        owner_filter,
                    )
                ),
            )
            widgets += [
                WidgetItem(key="open_tickets", label="Open Tickets", value=open_tickets),
                WidgetItem(key="sla_breach_count", label="SLA Breaches", value=sla_breaches),
                WidgetItem(key="resolved_this_week", label="Resolved This Week", value=resolved_week),
            ]

        if user.role in ("Manager", "Admin"):
            org_deals, org_tickets, expiring_contracts, active_accounts = await asyncio.gather(
                self._count(select(func.count(Deal.id)).where(
                    Deal.stage.notin_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
                )),
                self._count(select(func.count(Ticket.id)).where(
                    Ticket.status.in_(["open", "in_progress"])
                )),
                self._count(select(func.count(Contract.id)).where(
                    Contract.end_date >= date.today(),
                    Contract.end_date <= date.today() + timedelta(days=30),
                )),
                self._count(select(func.count()).select_from(User).where(User.is_active == True)),  # noqa: E712
            )
            widgets += [
                WidgetItem(key="org_open_deals", label="Org Open Deals", value=org_deals),
                WidgetItem(key="org_open_tickets", label="Org Open Tickets", value=org_tickets),
                WidgetItem(key="contracts_expiring_soon", label="Contracts Expiring (30d)", value=expiring_contracts),
                WidgetItem(key="total_active_accounts", label="Active Accounts", value=active_accounts),
            ]

        return DashboardResponse(widgets=widgets, generated_at=datetime.utcnow())

    # ------------------------------------------------------------------
    # Sales report
    # ------------------------------------------------------------------

    async def execute_sales_report(
        self,
        filters: dict,
        user: User,
    ) -> SalesReportResponse:
        key = ReportCacheKey.make(
            "sales", user.role, _scope_id(user, "sales"), filters,
            _cache.invalidator.version("sales"),
        )

        async def _build() -> SalesReportResponse:
            qb = (
                ReportQueryBuilder(self._session)
                .with_role_scope(user)
                .with_owner(filters.get("owner_id"))
                .with_date_range(filters.get("created_after"), filters.get("created_before"))
            )
            stage_rows = (await self._session.execute(qb.build_sales_stage_breakdown())).all()
            won_lost_rows = (await self._session.execute(qb.build_sales_won_lost())).all()
            avg_row = (await self._session.execute(qb.build_sales_avg_value())).one_or_none()
            top_rep_rows = (await self._session.execute(qb.build_sales_top_reps())).all()

            won_count = sum(r.count for r in won_lost_rows if r.stage == DealStage.CLOSED_WON)
            lost_count = sum(r.count for r in won_lost_rows if r.stage == DealStage.CLOSED_LOST)

            return SalesReportResponse(
                stage_breakdown=[
                    StageBreakdownItem(stage=r.stage, count=r.count, total_value=Decimal(str(r.total_value)))
                    for r in stage_rows
                ],
                won_count=won_count,
                lost_count=lost_count,
                avg_deal_value=Decimal(str(avg_row.avg_value)) if avg_row and avg_row.avg_value else None,
                top_reps=[
                    RepRevenue(owner_id=r.owner_id, owner_name=r.owner_name, revenue=Decimal(str(r.revenue)))
                    for r in top_rep_rows
                ],
                filters_applied=ReportFiltersApplied(
                    created_after=filters.get("created_after"),
                    created_before=filters.get("created_before"),
                    owner_id=filters.get("owner_id"),
                ),
                cached_until=datetime.utcnow() + timedelta(seconds=300),
            )

        return await _cache.get_or_set(key, _build)

    # ------------------------------------------------------------------
    # Support report
    # ------------------------------------------------------------------

    async def execute_support_report(
        self,
        filters: dict,
        user: User,
    ) -> SupportReportResponse:
        key = ReportCacheKey.make(
            "support", user.role, _scope_id(user, "support"), filters,
            _cache.invalidator.version("support"),
        )

        async def _build() -> SupportReportResponse:
            qb = (
                ReportQueryBuilder(self._session)
                .with_role_scope(user)
                .with_owner(filters.get("assignee_id"))
                .with_date_range(filters.get("created_after"), filters.get("created_before"))
            )
            status_rows, priority_rows, avg_row, per_agent_rows = await asyncio.gather(
                self._session.execute(qb.build_support_status_breakdown()),
                self._session.execute(qb.build_support_priority_breakdown()),
                self._session.execute(qb.build_support_avg_resolution()),
                self._session.execute(qb.build_support_per_agent()),
            )
            status_rows = status_rows.all()
            priority_rows = priority_rows.all()
            avg_row = avg_row.one_or_none()
            per_agent_rows = per_agent_rows.all()

            # SLA breach rate (simple: breached active records / total active)
            sla_total, sla_breached = await asyncio.gather(
                self._count(select(func.count(SLARecord.id)).where(SLARecord.is_active == True)),  # noqa: E712
                self._count(select(func.count(SLARecord.id)).where(
                    SLARecord.is_active == True,  # noqa: E712
                    SLARecord.first_response_breached == True,  # noqa: E712
                )),
            )
            breach_rate = (sla_breached / sla_total) if sla_total else None
            avg_secs = avg_row.avg_seconds if avg_row and avg_row.avg_seconds else None

            return SupportReportResponse(
                status_breakdown=[StatusBreakdownItem(status=r.status, count=r.count) for r in status_rows],
                priority_breakdown=[PriorityBreakdownItem(priority=r.priority, count=r.count) for r in priority_rows],
                avg_resolution_hours=avg_secs / 3600 if avg_secs else None,
                sla_breach_rate=breach_rate,
                per_agent=[
                    PerAgentCount(
                        assignee_id=r.assignee_id,
                        assignee_name=(r.assignee_name or "Unassigned") + ("" if r.is_active else " (deactivated)"),
                        count=r.count,
                    )
                    for r in per_agent_rows
                ],
                filters_applied=ReportFiltersApplied(
                    created_after=filters.get("created_after"),
                    created_before=filters.get("created_before"),
                    assignee_id=filters.get("assignee_id"),
                ),
                cached_until=datetime.utcnow() + timedelta(seconds=60),
            )

        return await _cache.get_or_set(key, _build)

    # ------------------------------------------------------------------
    # Contract report
    # ------------------------------------------------------------------

    async def execute_contract_report(
        self,
        filters: dict,
        user: User,
    ) -> ContractReportResponse:
        key = ReportCacheKey.make(
            "contract", user.role, _scope_id(user, "sales"), filters,
            _cache.invalidator.version("contract"),
        )

        async def _build() -> ContractReportResponse:
            window = filters.get("renewal_window", 30)
            today = date.today()
            qb = (
                ReportQueryBuilder(self._session)
                .with_role_scope(user)
                .with_owner(filters.get("owner_id"))
            )
            status_rows, renewal_rows, account_rows = await asyncio.gather(
                self._session.execute(qb.build_contract_status_breakdown()),
                self._session.execute(qb.build_contract_upcoming_renewals(window, today)),
                self._session.execute(qb.build_contract_value_by_account()),
            )
            status_rows = status_rows.all()
            renewal_rows = renewal_rows.all()
            account_rows = account_rows.all()

            # Resolve account names
            account_ids = {r.account_id for r in account_rows if r.account_id}
            renewal_account_ids = {r.account_id for r in renewal_rows if r.account_id}
            all_ids = account_ids | renewal_account_ids
            account_name_map: dict[int, str] = {}
            if all_ids:
                result = await self._session.execute(
                    select(Account.id, Account.name).where(Account.id.in_(all_ids))
                )
                account_name_map = {r.id: r.name for r in result.all()}

            upcoming: list[UpcomingRenewal] = []
            for r in renewal_rows:
                days_remaining = (r.end_date - today).days
                upcoming.append(UpcomingRenewal(
                    contract_id=r.id,
                    ref_id=r.ref_id,
                    account_name=account_name_map.get(r.account_id, "—") if r.account_id else "—",
                    value=Decimal(str(r.value)),
                    expiry_date=r.end_date,
                    days_remaining=days_remaining,
                ))

            return ContractReportResponse(
                status_breakdown=[
                    StatusValueItem(status=r.status, count=r.count, total_value=Decimal(str(r.total_value)))
                    for r in status_rows
                ],
                upcoming_renewals=upcoming,
                value_by_account=[
                    AccountValue(
                        account_id=r.account_id,
                        account_name=account_name_map.get(r.account_id, "—") if r.account_id else "—",
                        total_value=Decimal(str(r.total_value)),
                    )
                    for r in account_rows
                ],
                filters_applied=ReportFiltersApplied(
                    owner_id=filters.get("owner_id"),
                    renewal_window=window,
                ),
                cached_until=datetime.utcnow() + timedelta(seconds=300),
            )

        return await _cache.get_or_set(key, _build)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _count(self, stmt) -> int:
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def _scalar(self, stmt):
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0


def _scope_id(user: User, report_type: str) -> int | None:
    if report_type == "sales" and user.role == "Sales Rep":
        return user.id
    if report_type == "support" and user.role == "Support Agent":
        return user.id
    return None
