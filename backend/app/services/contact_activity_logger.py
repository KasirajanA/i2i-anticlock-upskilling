from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import ContactActivityLog


class ContactActivityLogger:
    async def log(
        self,
        session: AsyncSession,
        event_type: str,
        entity_type: str,
        entity_id: int,
        actor_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        entry = ContactActivityLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            metadata_=metadata,
        )
        session.add(entry)
        await session.flush()
