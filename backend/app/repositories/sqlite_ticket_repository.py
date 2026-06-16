"""SQLite-backed TicketRepository using SQLAlchemy 2.x async."""

import base64
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.support import SLARecord, Ticket, TicketActivityLog
from app.repositories.base import ITicketRepository


class SqliteTicketRepository(ITicketRepository):

    async def create(
        self,
        session: AsyncSession,
        ticket: Ticket,
        sla: SLARecord,
    ) -> tuple[Ticket, SLARecord]:
        session.add(ticket)
        await session.flush()
        sla.ticket_id = ticket.id
        session.add(sla)
        await session.flush()
        await session.refresh(ticket)
        await session.refresh(sla)
        return ticket, sla

    async def get_by_id(
        self, session: AsyncSession, ticket_id: int
    ) -> tuple[Ticket, SLARecord | None] | None:
        result = await session.execute(
            select(Ticket).where(
                Ticket.id == ticket_id, Ticket.deleted_at.is_(None)
            )
        )
        ticket = result.scalar_one_or_none()
        if ticket is None:
            return None
        sla = await self._active_sla(session, ticket_id)
        return ticket, sla

    async def list_paginated(
        self,
        session: AsyncSession,
        *,
        queue: str | None = None,
        caller_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: int | None = None,
        account_id: int | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[tuple[Ticket, SLARecord | None]], str | None, int]:
        limit = min(limit, 100)
        stmt = select(Ticket).where(Ticket.deleted_at.is_(None))

        if queue == "mine" and caller_id is not None:
            stmt = stmt.where(Ticket.assignee_id == caller_id)
        elif queue == "unassigned":
            stmt = stmt.where(Ticket.assignee_id.is_(None))

        if status:
            stmt = stmt.where(Ticket.status == status)
        if priority:
            stmt = stmt.where(Ticket.priority == priority)
        if assignee_id is not None:
            stmt = stmt.where(Ticket.assignee_id == assignee_id)
        if account_id is not None:
            stmt = stmt.where(Ticket.account_id == account_id)
        if created_after:
            stmt = stmt.where(Ticket.created_at >= created_after)
        if created_before:
            stmt = stmt.where(Ticket.created_at <= created_before)

        if cursor:
            try:
                decoded = json.loads(base64.b64decode(cursor).decode())
                cursor_dt = decoded.get("created_at")
                cursor_id = decoded.get("id")
                if cursor_dt and cursor_id:
                    stmt = stmt.where(
                        (Ticket.created_at < cursor_dt)
                        | ((Ticket.created_at == cursor_dt) & (Ticket.id < cursor_id))
                    )
            except Exception:
                pass

        # Total count (separate query without cursor)
        count_stmt = select(func.count()).select_from(
            select(Ticket).where(Ticket.deleted_at.is_(None)).subquery()
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit + 1)
        result = await session.execute(stmt)
        tickets = list(result.scalars().all())

        has_more = len(tickets) > limit
        if has_more:
            tickets = tickets[:limit]

        next_cursor: str | None = None
        if has_more and tickets:
            last = tickets[-1]
            raw = {"created_at": last.created_at.isoformat(), "id": last.id}
            next_cursor = base64.b64encode(json.dumps(raw).encode()).decode()

        pairs: list[tuple[Ticket, SLARecord | None]] = []
        for t in tickets:
            sla = await self._active_sla(session, t.id)
            pairs.append((t, sla))

        return pairs, next_cursor, total

    async def update(self, session: AsyncSession, ticket: Ticket) -> Ticket:
        ticket.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(ticket)
        return ticket

    async def assign(
        self, session: AsyncSession, ticket: Ticket, assignee_id: int | None
    ) -> Ticket:
        ticket.assignee_id = assignee_id
        ticket.updated_at = datetime.utcnow()
        await session.flush()
        await session.refresh(ticket)
        return ticket

    async def _active_sla(
        self, session: AsyncSession, ticket_id: int
    ) -> SLARecord | None:
        result = await session.execute(
            select(SLARecord).where(
                SLARecord.ticket_id == ticket_id, SLARecord.is_active.is_(True)
            )
        )
        return result.scalar_one_or_none()

    async def get_all_sla(
        self, session: AsyncSession, ticket_id: int
    ) -> list[SLARecord]:
        result = await session.execute(
            select(SLARecord)
            .where(SLARecord.ticket_id == ticket_id)
            .order_by(SLARecord.cycle)
        )
        return list(result.scalars().all())

    async def get_replies(
        self, session: AsyncSession, ticket_id: int, include_internal: bool = True
    ) -> list:
        from app.models.support import Reply  # noqa: PLC0415

        stmt = select(Reply).where(Reply.ticket_id == ticket_id)
        if not include_internal:
            stmt = stmt.where(Reply.is_internal.is_(False))
        stmt = stmt.order_by(Reply.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_activity(
        self, session: AsyncSession, ticket_id: int
    ) -> list[TicketActivityLog]:
        result = await session.execute(
            select(TicketActivityLog)
            .where(TicketActivityLog.ticket_id == ticket_id)
            .order_by(TicketActivityLog.created_at.desc())
        )
        return list(result.scalars().all())
