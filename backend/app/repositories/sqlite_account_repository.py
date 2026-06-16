from __future__ import annotations

import base64
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Account, ContactAccount
from app.schemas.contact import PaginatedAccounts


class SqliteAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create(self, data: dict) -> Account:
        account = Account(**data)
        self._db.add(account)
        await self._db.commit()
        await self._db.refresh(account)
        return account

    async def get_by_id(self, id: int, include_archived: bool = False) -> Account | None:
        q = select(Account).where(Account.id == id)
        if not include_archived:
            q = q.where(Account.deleted_at.is_(None))
        return (await self._db.execute(q)).scalar_one_or_none()

    async def list(
        self,
        q: str | None = None,
        industry: str | None = None,
        owner_id: int | None = None,
        include_archived: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedAccounts:
        base = select(Account)
        if not include_archived:
            base = base.where(Account.deleted_at.is_(None))
        if q:
            base = base.where(Account.name.ilike(f"%{q}%"))
        if industry:
            base = base.where(Account.industry == industry)
        if owner_id:
            base = base.where(Account.owner_id == owner_id)
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
                base = base.where(Account.id > cursor_data["id"])
            except Exception:
                pass

        total_q = select(func.count()).select_from(base.subquery())
        total = (await self._db.execute(total_q)).scalar_one()

        base = base.order_by(Account.id).limit(limit + 1)
        rows = list((await self._db.execute(base)).scalars().all())
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = base64.b64encode(json.dumps({"id": rows[-1].id}).encode()).decode()

        return PaginatedAccounts(items=rows, total=total, next_cursor=next_cursor)

    async def update(self, id: int, fields: dict) -> Account | None:
        account = await self._db.get(Account, id)
        if account is None:
            return None
        for k, v in fields.items():
            setattr(account, k, v)
        account.updated_at = datetime.utcnow()
        await self._db.commit()
        await self._db.refresh(account)
        return account

    async def archive(self, id: int) -> None:
        account = await self._db.get(Account, id)
        if account:
            account.deleted_at = datetime.utcnow()
            account.is_archived = True
            await self._db.commit()

    async def get_contact_count(self, id: int) -> int:
        result = await self._db.execute(
            select(func.count(ContactAccount.contact_id)).where(
                ContactAccount.account_id == id
            )
        )
        return result.scalar_one()
