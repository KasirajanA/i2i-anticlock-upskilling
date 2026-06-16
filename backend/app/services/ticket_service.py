"""Business logic for Customer Support tickets (Module 003)."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Notification, User
from app.models.contact import Contact
from app.models.support import Reply, SLARecord, Ticket, TicketSequence
from app.repositories.sqlite_ticket_repository import SqliteTicketRepository
from app.schemas.support import TicketCreate, TicketUpdate
from app.services.activity_logger import ActivityLogger
from app.services.sla_engine import SLAEngine

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"closed", "open"},
    "closed": set(),
}

ADMIN_REVERSIONS: dict[str, set[str]] = {
    "in_progress": {"open"},
    "resolved": {"in_progress", "open"},
    "closed": {"resolved", "in_progress", "open"},
}


class TicketService:
    def __init__(
        self,
        repo: SqliteTicketRepository | None = None,
        logger: ActivityLogger | None = None,
        sla_engine: SLAEngine | None = None,
    ) -> None:
        self._repo = repo or SqliteTicketRepository()
        self._logger = logger or ActivityLogger()
        self._sla = sla_engine or SLAEngine()

    # ------------------------------------------------------------------ #
    # ID Generation                                                        #
    # ------------------------------------------------------------------ #

    async def _next_seq(self, session: AsyncSession) -> int:
        result = await session.execute(
            update(TicketSequence)
            .where(TicketSequence.id == 1)
            .values(next_value=TicketSequence.next_value + 1)
            .returning(TicketSequence.next_value)
        )
        return result.scalar_one()

    # ------------------------------------------------------------------ #
    # Create                                                               #
    # ------------------------------------------------------------------ #

    async def create_ticket(
        self,
        session: AsyncSession,
        payload: TicketCreate,
        actor_id: int,
    ) -> tuple[Ticket, SLARecord]:
        # Resolve contact name snapshot
        contact = await session.get(Contact, payload.contact_id)
        if contact is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="contact_id does not reference a known contact",
            )

        seq = await self._next_seq(session)

        ticket = Ticket(
            seq_number=seq,
            subject=payload.subject,
            description=payload.description,
            status="open",
            priority=payload.priority,
            contact_id=payload.contact_id,
            contact_name_snapshot=contact.name,
            account_id=None,
            assignee_id=payload.assignee_id,
            created_by_id=actor_id,
        )

        now = datetime.utcnow()
        fr_due, res_due = self._sla.compute_due_dates(payload.priority, now)
        sla = SLARecord(
            cycle=1,
            first_response_due=fr_due,
            resolution_due=res_due,
            is_active=True,
        )

        ticket, sla = await self._repo.create(session, ticket, sla)

        await self._logger.append(
            session, ticket.id, "creation", actor_id, {"ref": f"I2I-CRM-{seq:04d}"}
        )

        if payload.assignee_id and payload.assignee_id != actor_id:
            await self._dispatch_notification(
                session,
                user_id=payload.assignee_id,
                message=f"Ticket I2I-CRM-{seq:04d} assigned to you.",
                entity_type="ticket",
                entity_id=ticket.id,
            )

        return ticket, sla

    # ------------------------------------------------------------------ #
    # Status Transition                                                    #
    # ------------------------------------------------------------------ #

    async def transition(
        self,
        session: AsyncSession,
        ticket: Ticket,
        new_status: str,
        actor_id: int,
        actor_role: str,
    ) -> Ticket:
        current = ticket.status
        agent_allowed = set(ALLOWED_TRANSITIONS.get(current, set()))
        admin_only = set(ADMIN_REVERSIONS.get(current, set()))

        # Agent trying an admin-only reversion → 403 (not 422)
        if new_status in admin_only and actor_role != "Admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Agents cannot revert ticket status.",
            )

        allowed = set(agent_allowed)
        if actor_role == "Admin":
            allowed |= admin_only

        if new_status not in allowed:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://crm.i2i.io/errors/invalid-status-transition",
                    "title": "Invalid Status Transition",
                    "status": 422,
                    "detail": f"Transition from '{current}' to '{new_status}' is not allowed.",
                },
            )

        old_status = ticket.status
        ticket.status = new_status

        # Track resolved_at on active SLA
        if new_status == "resolved":
            sla = await self._repo._active_sla(session, ticket.id)
            if sla:
                sla.resolved_at = datetime.utcnow()

        ticket = await self._repo.update(session, ticket)
        await self._logger.append(
            session, ticket.id, "status_change", actor_id,
            {"from": old_status, "to": new_status},
        )
        return ticket

    # ------------------------------------------------------------------ #
    # Reply                                                                #
    # ------------------------------------------------------------------ #

    async def add_reply(
        self,
        session: AsyncSession,
        ticket: Ticket,
        body: str,
        is_internal: bool,
        actor_id: int,
    ) -> Reply:
        was_resolved = ticket.status == "resolved"

        if was_resolved and not is_internal:
            await self._reopen(session, ticket, actor_id)

        reply = Reply(
            ticket_id=ticket.id,
            author_id=actor_id,
            body=body,
            is_internal=is_internal,
        )
        session.add(reply)
        await session.flush()

        if not is_internal:
            sla = await self._repo._active_sla(session, ticket.id)
            if sla and sla.first_response_at is None:
                sla.first_response_at = datetime.utcnow()
                await session.flush()

        event = "note_added" if is_internal else "reply_added"
        await self._logger.append(session, ticket.id, event, actor_id)
        await session.refresh(reply)
        return reply

    async def _reopen(
        self, session: AsyncSession, ticket: Ticket, actor_id: int
    ) -> None:
        # Deactivate old SLA record
        old_sla = await self._repo._active_sla(session, ticket.id)
        if old_sla:
            old_sla.is_active = False

        # New SLA cycle
        cycle = (old_sla.cycle + 1) if old_sla else 2
        now = datetime.utcnow()
        fr_due, res_due = self._sla.compute_due_dates(ticket.priority, now)
        new_sla = SLARecord(
            ticket_id=ticket.id,
            cycle=cycle,
            first_response_due=fr_due,
            resolution_due=res_due,
            is_active=True,
        )
        session.add(new_sla)

        ticket.status = "open"
        ticket.updated_at = datetime.utcnow()
        await session.flush()
        await self._logger.append(
            session, ticket.id, "reopen", actor_id, {"new_cycle": cycle}
        )

    # ------------------------------------------------------------------ #
    # Assignment                                                           #
    # ------------------------------------------------------------------ #

    async def assign(
        self,
        session: AsyncSession,
        ticket: Ticket,
        assignee_id: int,
        actor_id: int,
        actor_role: str,
    ) -> Ticket:
        if actor_role not in ("Admin",) and assignee_id != actor_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Agents may only self-assign tickets.",
            )

        assignee = await session.get(User, assignee_id)
        if assignee is None or not assignee.is_active:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee not found or inactive.",
            )
        if assignee.role not in ("Admin", "Support Agent"):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee must have support or admin role.",
            )

        ticket = await self._repo.assign(session, ticket, assignee_id)
        await self._logger.append(
            session, ticket.id, "assignment", actor_id,
            {"assignee_id": assignee_id},
        )
        if assignee_id != actor_id:
            await self._dispatch_notification(
                session,
                user_id=assignee_id,
                message=f"Ticket I2I-CRM-{ticket.seq_number:04d} assigned to you.",
                entity_type="ticket",
                entity_id=ticket.id,
            )
        return ticket

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    async def _dispatch_notification(
        self,
        session: AsyncSession,
        user_id: int,
        message: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> None:
        notif = Notification(
            user_id=user_id,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        session.add(notif)
        await session.flush()
