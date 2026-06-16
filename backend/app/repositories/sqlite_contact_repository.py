from __future__ import annotations

import base64
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactAccount
from app.schemas.contact import PaginatedContacts


class SqliteContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create(self, contact_data: dict, account_ids: list[int]) -> Contact:
        contact = Contact(**contact_data)
        self._db.add(contact)
        await self._db.flush()
        for aid in account_ids:
            self._db.add(ContactAccount(contact_id=contact.id, account_id=aid))
        await self._db.commit()
        await self._db.refresh(contact)
        return contact

    async def get_by_id(self, id: int, include_archived: bool = False) -> Contact | None:
        q = select(Contact).where(Contact.id == id)
        if not include_archived:
            q = q.where(Contact.deleted_at.is_(None))
        return (await self._db.execute(q)).scalar_one_or_none()

    async def list(
        self,
        q: str | None = None,
        account_id: int | None = None,
        tag: str | None = None,
        owner_id: int | None = None,
        include_archived: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedContacts:
        base = select(Contact)
        if not include_archived:
            base = base.where(Contact.deleted_at.is_(None))
        if q:
            pattern = f"%{q}%"
            base = base.where(
                Contact.first_name.ilike(pattern)
                | Contact.last_name.ilike(pattern)
                | Contact.email.ilike(pattern)
                | Contact.name.ilike(pattern)
            )
        if tag:
            base = base.where(Contact.tags.contains([tag]))
        if account_id:
            base = base.where(
                Contact.id.in_(
                    select(ContactAccount.contact_id).where(ContactAccount.account_id == account_id)
                )
            )
        if owner_id:
            base = base.where(Contact.owner_id == owner_id)
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
                base = base.where(Contact.id > cursor_data["id"])
            except Exception:
                pass

        total_q = select(func.count()).select_from(base.subquery())
        total = (await self._db.execute(total_q)).scalar_one()

        base = base.order_by(Contact.id).limit(limit + 1)
        rows = list((await self._db.execute(base)).scalars().all())

        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = base64.b64encode(json.dumps({"id": rows[-1].id}).encode()).decode()

        return PaginatedContacts(items=rows, total=total, next_cursor=next_cursor)

    async def find_by_email(self, email: str) -> Contact | None:
        q = select(Contact).where(func.lower(Contact.email) == email.lower().strip())
        return (await self._db.execute(q)).scalar_one_or_none()

    async def update(self, id: int, fields: dict) -> Contact | None:
        contact = await self._db.get(Contact, id)
        if contact is None:
            return None
        for k, v in fields.items():
            setattr(contact, k, v)
        contact.updated_at = datetime.utcnow()
        await self._db.commit()
        await self._db.refresh(contact)
        return contact

    async def archive(self, id: int) -> None:
        contact = await self._db.get(Contact, id)
        if contact:
            contact.deleted_at = datetime.utcnow()
            contact.is_archived = True
            await self._db.commit()

    async def link_account(self, contact_id: int, account_id: int) -> None:
        existing = (await self._db.execute(
            select(ContactAccount).where(
                ContactAccount.contact_id == contact_id,
                ContactAccount.account_id == account_id,
            )
        )).scalar_one_or_none()
        if not existing:
            self._db.add(ContactAccount(contact_id=contact_id, account_id=account_id))
            await self._db.commit()

    async def unlink_account(self, contact_id: int, account_id: int) -> None:
        link = (await self._db.execute(
            select(ContactAccount).where(
                ContactAccount.contact_id == contact_id,
                ContactAccount.account_id == account_id,
            )
        )).scalar_one_or_none()
        if link:
            await self._db.delete(link)
            await self._db.commit()
