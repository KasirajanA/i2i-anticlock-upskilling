from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import User
from app.models.contracts import Contract
from app.models.deal import Deal, DealStage
from app.models.support import SLARecord, Ticket


class ReportQueryBuilder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._owner_id: int | None = None
        self._date_after: date | None = None
        self._date_before: date | None = None

    def with_role_scope(self, user: User) -> "ReportQueryBuilder":
        if user.role in ("Sales Rep", "Support Agent"):
            self._owner_id = user.id
        return self

    def with_owner(self, owner_id: int | None) -> "ReportQueryBuilder":
        if self._owner_id is None:
            self._owner_id = owner_id
        return self

    def with_date_range(self, after: date | None, before: date | None) -> "ReportQueryBuilder":
        self._date_after = after
        self._date_before = before
        return self

    def _apply_archive_policy(self, stmt: Select) -> Select:
        # FR-011: soft-deleted/archived records are INCLUDED in historical aggregates
        return stmt

    def build_sales_stage_breakdown(self) -> Select:
        stmt = select(
            Deal.stage,
            func.count(Deal.id).label("count"),
            func.coalesce(func.sum(Deal.value), 0).label("total_value"),
        ).group_by(Deal.stage)
        stmt = self._apply_archive_policy(stmt)
        if self._owner_id is not None:
            stmt = stmt.where(Deal.owner_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Deal.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Deal.created_at <= self._date_before)
        return stmt

    def build_sales_won_lost(self) -> Select:
        stmt = select(
            Deal.stage,
            func.count(Deal.id).label("count"),
        ).where(Deal.stage.in_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])).group_by(Deal.stage)
        if self._owner_id is not None:
            stmt = stmt.where(Deal.owner_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Deal.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Deal.created_at <= self._date_before)
        return stmt

    def build_sales_avg_value(self) -> Select:
        stmt = select(func.avg(Deal.value).label("avg_value")).where(
            Deal.stage.in_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
        )
        if self._owner_id is not None:
            stmt = stmt.where(Deal.owner_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Deal.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Deal.created_at <= self._date_before)
        return stmt

    def build_sales_top_reps(self) -> Select:
        stmt = (
            select(
                Deal.owner_id,
                User.name.label("owner_name"),
                func.coalesce(func.sum(Deal.value), 0).label("revenue"),
            )
            .join(User, Deal.owner_id == User.id)
            .where(Deal.stage == DealStage.CLOSED_WON)
            .group_by(Deal.owner_id, User.name)
            .order_by(func.sum(Deal.value).desc())
            .limit(10)
        )
        if self._date_after:
            stmt = stmt.where(Deal.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Deal.created_at <= self._date_before)
        return stmt

    def build_support_status_breakdown(self) -> Select:
        stmt = select(
            Ticket.status,
            func.count(Ticket.id).label("count"),
        ).group_by(Ticket.status)
        if self._owner_id is not None:
            stmt = stmt.where(Ticket.assignee_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Ticket.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Ticket.created_at <= self._date_before)
        return stmt

    def build_support_priority_breakdown(self) -> Select:
        stmt = select(
            Ticket.priority,
            func.count(Ticket.id).label("count"),
        ).group_by(Ticket.priority)
        if self._owner_id is not None:
            stmt = stmt.where(Ticket.assignee_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Ticket.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Ticket.created_at <= self._date_before)
        return stmt

    def build_support_avg_resolution(self) -> Select:
        # Returns avg seconds between created_at and updated_at for resolved tickets
        stmt = select(
            func.avg(
                func.strftime("%s", Ticket.updated_at) - func.strftime("%s", Ticket.created_at)
            ).label("avg_seconds")
        ).where(Ticket.status == "resolved")
        if self._owner_id is not None:
            stmt = stmt.where(Ticket.assignee_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Ticket.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Ticket.created_at <= self._date_before)
        return stmt

    def build_support_sla_breach_rate(self) -> Select:
        stmt = select(
            func.count(SLARecord.id).label("total"),
            func.sum(
                func.cast(
                    and_(
                        SLARecord.first_response_breached == True,  # noqa: E712
                    ),
                    func.count(SLARecord.id).type,
                )
            ).label("breached"),
        ).where(SLARecord.is_active == True)  # noqa: E712
        if self._owner_id is not None:
            stmt = stmt.join(Ticket, SLARecord.ticket_id == Ticket.id).where(
                Ticket.assignee_id == self._owner_id
            )
        return stmt

    def build_support_per_agent(self) -> Select:
        stmt = (
            select(
                Ticket.assignee_id,
                User.name.label("assignee_name"),
                User.is_active,
                func.count(Ticket.id).label("count"),
            )
            .join(User, Ticket.assignee_id == User.id, isouter=True)
            .group_by(Ticket.assignee_id, User.name, User.is_active)
        )
        if self._owner_id is not None:
            stmt = stmt.where(Ticket.assignee_id == self._owner_id)
        if self._date_after:
            stmt = stmt.where(Ticket.created_at >= self._date_after)
        if self._date_before:
            stmt = stmt.where(Ticket.created_at <= self._date_before)
        return stmt

    def build_contract_status_breakdown(self) -> Select:
        stmt = (
            select(
                Contract.status,
                func.count(Contract.id).label("count"),
                func.coalesce(func.sum(Contract.value), 0).label("total_value"),
            )
            .group_by(Contract.status)
        )
        stmt = self._apply_archive_policy(stmt)
        if self._owner_id is not None:
            stmt = stmt.where(Contract.owner_id == self._owner_id)
        return stmt

    def build_contract_upcoming_renewals(self, window_days: int, today: date) -> Select:
        from datetime import timedelta  # noqa: PLC0415
        cutoff = today + timedelta(days=window_days)
        stmt = (
            select(
                Contract.id,
                Contract.ref_id,
                Contract.value,
                Contract.end_date,
                Contract.account_id,
            )
            .where(Contract.end_date >= today)
            .where(Contract.end_date <= cutoff)
            .order_by(Contract.end_date)
        )
        if self._owner_id is not None:
            stmt = stmt.where(Contract.owner_id == self._owner_id)
        return stmt

    def build_contract_value_by_account(self) -> Select:
        stmt = (
            select(
                Contract.account_id,
                func.coalesce(func.sum(Contract.value), 0).label("total_value"),
            )
            .group_by(Contract.account_id)
            .order_by(func.sum(Contract.value).desc())
        )
        stmt = self._apply_archive_policy(stmt)
        if self._owner_id is not None:
            stmt = stmt.where(Contract.owner_id == self._owner_id)
        return stmt
