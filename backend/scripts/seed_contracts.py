#!/usr/bin/env python3
"""Seed script for SC-004 performance testing (10,000 contracts)."""

import argparse
import asyncio
import random
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.models.base import Account, User
from app.models.contracts import Contract, ContractStatus

STATUSES = list(ContractStatus)


async def seed(count: int) -> None:
    engine = create_async_engine(settings.db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        async with db.begin():
            user = User(name="Seed User", email="seed@test.com", role="Sales Rep")
            account = Account(name="Seed Account")
            db.add(user)
            db.add(account)
        await db.refresh(user)
        await db.refresh(account)

        batch_size = 500
        for batch_start in range(0, count, batch_size):
            batch = min(batch_size, count - batch_start)
            async with db.begin():
                for i in range(batch_start, batch_start + batch):
                    start = date(2020, 1, 1) + timedelta(days=random.randint(0, 2000))
                    end = start + timedelta(days=random.randint(30, 730))
                    db.add(
                        Contract(
                            ref_id=f"CON-{i + 1:04d}",
                            value=round(random.uniform(1000, 100000), 2),
                            start_date=start,
                            end_date=end,
                            status=random.choice(STATUSES),
                            owner_id=user.id,
                            account_id=account.id,
                        )
                    )
            print(f"  seeded {min(batch_start + batch, count)}/{count}")

    await engine.dispose()
    print(f"Done — {count} contracts seeded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000)
    args = parser.parse_args()
    asyncio.run(seed(args.count))
