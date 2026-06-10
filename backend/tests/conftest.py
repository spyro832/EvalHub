"""
Pytest configuration for EvalHub backend tests.

Design:
- Tables are created ONCE at session start using asyncio.run() (avoids
  session-scoped async fixture event-loop-scope issues with pytest-asyncio).
- Each test gets a fresh async engine + session via function-scoped fixtures,
  so SQLAlchemy objects always live in the correct event loop.
- db_session rolls back after every test to keep state isolated.
"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


# ── Session-level DB setup (sync wrapper so no loop-scope headaches) ──────────


def _run(coro):
    """Run a coroutine to completion in a fresh event loop."""
    return asyncio.run(coro)


async def _create_tables():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def _drop_tables():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def db_tables():
    """Create all tables once before the session; drop them after."""
    _run(_create_tables())
    yield
    _run(_drop_tables())


# ── Per-test async fixtures ───────────────────────────────────────────────────


@pytest.fixture
async def db_session(db_tables):  # noqa: ARG001  (ensures tables exist)
    """Fresh async session for each test; rolls back at teardown."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Async HTTP client wired to the FastAPI app with DB overridden."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
