"""Append-only activity log writer for support tickets."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support import TicketActivityLog


class ActivityLogger:
    async def append(
        self,
        session: AsyncSession,
        ticket_id: int,
        event_type: str,
        actor_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TicketActivityLog:
        entry = TicketActivityLog(
            ticket_id=ticket_id,
            event_type=event_type,
            actor_id=actor_id,
            event_metadata=metadata,
        )
        session.add(entry)
        await session.flush()
        return entry
