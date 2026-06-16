"""Shared pytest fixtures for unit and integration tests."""

from datetime import date
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models so Base.metadata includes every table before create_all
import app.models.base  # noqa: F401
import app.models.contracts  # noqa: F401
import app.models.deal  # noqa: F401
import app.models.support  # noqa: F401
import app.models.team  # noqa: F401
import app.models.contact  # noqa: F401
from app.core.database import Base, get_session
from app.core.security import CurrentUser, get_current_user
from app.main import create_app
from app.models.base import User
from app.models.contact import Account, Contact
from app.models.deal import Deal, DealStage
from app.models.support import TicketSequence

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed TicketSequence row (single-row counter)
    from sqlalchemy.ext.asyncio import async_sessionmaker  # noqa: PLC0415
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(TicketSequence(id=1, next_value=1))
        await session.commit()
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(name="Test Sales Rep", email="rep@test.com", role="Sales Rep")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(name="Test Admin", email="admin@test.com", role="Admin")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def manager_user(db_session: AsyncSession) -> User:
    user = User(name="Test Manager", email="manager@test.com", role="Manager")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def support_agent_user(db_session: AsyncSession) -> User:
    user = User(name="Test Agent", email="agent@test.com", role="Support Agent")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_account(db_session: AsyncSession) -> Account:
    account = Account(name="Acme Corp")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


@pytest_asyncio.fixture
async def test_deal(db_session: AsyncSession, test_user: User, test_account: Account) -> Deal:
    """A minimal active deal used as a FK target or base for stage tests."""
    deal = Deal(
        ref_id="DEAL-0001",
        title="Test Deal",
        value=Decimal("10000.00"),
        stage=DealStage.LEAD_IN,
        expected_close_date=date(2026, 12, 31),
        owner_id=test_user.id,
        account_id=test_account.id,
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    return deal


def _make_current_user(user: User) -> CurrentUser:
    return CurrentUser(id=user.id, name=user.name, email=user.email, role=user.role)


@pytest_asyncio.fixture
async def client(db_engine, test_user: User):
    """HTTPX async client against the FastAPI app with a mocked Sales Rep session."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    app = create_app()

    async def _override_db():
        async with factory() as session:
            yield session

    mock_user = _make_current_user(test_user)

    app.dependency_overrides[get_session] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def admin_client(db_engine, admin_user: User):
    """HTTPX async client with an Admin session."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    app = create_app()

    async def _override_db():
        async with factory() as session:
            yield session

    mock_user = _make_current_user(admin_user)

    app.dependency_overrides[get_session] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def test_contact(db_session: AsyncSession) -> Contact:
    contact = Contact(name="Jane Doe")
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def support_client(db_engine, support_agent_user: User):
    """HTTPX async client with a Support Agent session."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    app = create_app()

    async def _override_db():
        async with factory() as session:
            yield session

    mock_user = _make_current_user(support_agent_user)

    app.dependency_overrides[get_session] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def manager_client(db_engine, manager_user: User):
    """HTTPX async client with a Manager session."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    app = create_app()

    async def _override_db():
        async with factory() as session:
            yield session

    mock_user = _make_current_user(manager_user)

    app.dependency_overrides[get_session] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
