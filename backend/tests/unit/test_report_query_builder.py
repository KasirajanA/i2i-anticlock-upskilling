"""Unit tests for ReportQueryBuilder."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base, User
from app.services.report_query_builder import ReportQueryBuilder


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _user(role: str) -> User:
    u = User(id=42, name="Test", email="t@t.com", role=role)
    return u


def test_sales_rep_forces_owner_id(session):
    user = _user("Sales Rep")
    qb = ReportQueryBuilder(session).with_role_scope(user)
    assert qb._owner_id == 42


def test_manager_no_owner_filter(session):
    user = _user("Manager")
    qb = ReportQueryBuilder(session).with_role_scope(user)
    assert qb._owner_id is None


def test_admin_no_owner_filter(session):
    user = _user("Admin")
    qb = ReportQueryBuilder(session).with_role_scope(user)
    assert qb._owner_id is None


def test_support_agent_forces_owner_id(session):
    user = _user("Support Agent")
    qb = ReportQueryBuilder(session).with_role_scope(user)
    assert qb._owner_id == 42


def test_date_range_stored(session):
    from datetime import date  # noqa: PLC0415
    user = _user("Admin")
    qb = (
        ReportQueryBuilder(session)
        .with_role_scope(user)
        .with_date_range(date(2026, 1, 1), date(2026, 6, 30))
    )
    assert qb._date_after == date(2026, 1, 1)
    assert qb._date_before == date(2026, 6, 30)


def test_archive_policy_does_not_add_deleted_at_filter(session):
    """_apply_archive_policy must NOT add a deleted_at IS NULL clause (FR-011)."""
    from sqlalchemy import select  # noqa: PLC0415
    qb = ReportQueryBuilder(session)
    stmt = select(User)
    result = qb._apply_archive_policy(stmt)
    compiled = str(result.compile())
    assert "deleted_at" not in compiled
