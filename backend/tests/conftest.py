"""Test fixtures and configuration."""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

from app.core.config import Settings
from app.core.database import metadata
from app.main import create_app


TEST_DATABASE_URL = "postgresql+asyncpg://meridian:meridian@localhost:5432/meridian_test"


class MockLLMClient:
    """Mock LLM client for testing intelligence features."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.call_count = 0
        self.calls: list[dict] = []

    async def complete(self, messages, **kwargs):
        self.calls.append({"messages": messages, **kwargs})
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = self.responses[-1] if self.responses else '{"result": "default"}'
        self.call_count += 1
        return response

    async def complete_json(self, messages, **kwargs):
        text_response = await self.complete(messages, **kwargs)
        import json
        text_response = text_response.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text_response)

    async def health_check(self):
        return True

    async def close(self):
        pass


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database and return the engine."""
    import asyncpg

    # Connect to postgres default db to manage databases
    conn = await asyncpg.connect(
        "postgresql://meridian:meridian@localhost:5432/postgres"
    )
    try:
        await conn.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'meridian_test'
            AND pid <> pg_backend_pid()
            """
        )
        await conn.execute("DROP DATABASE IF EXISTS meridian_test")
        await conn.execute("CREATE DATABASE meridian_test")
    finally:
        await conn.close()

    # Import all models to register metadata
    from app.models import user, task, daily_plan, pattern, notification  # noqa

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    yield engine

    await engine.dispose()

    # Drop the test database
    admin_conn = await asyncpg.connect(
        "postgresql://meridian:meridian@localhost:5432/postgres"
    )
    try:
        await admin_conn.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'meridian_test'
            AND pid <> pg_backend_pid()
            """
        )
        await admin_conn.execute("DROP DATABASE IF EXISTS meridian_test")
    finally:
        await admin_conn.close()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    factory = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def app(test_engine):
    """Create a test FastAPI app pointing to the test database."""
    import app.core.database as db_module

    # Point the global engine and session factory at the test engine
    old_engine = db_module._engine
    old_factory = db_module._session_factory

    db_module._engine = test_engine
    db_module._session_factory = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    _settings = Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret="test-secret",
        debug=True,
    )

    test_app = create_app(_settings)

    yield test_app

    # Restore original globals
    db_module._engine = old_engine
    db_module._session_factory = old_factory


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Create authorization headers with a test token."""
    from app.core.security import create_access_token
    token = create_access_token("test-user-id")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM client for intelligence tests."""
    mock = MockLLMClient()

    def get_mock_llm():
        return mock

    monkeypatch.setattr("app.core.llm.get_llm_client", get_mock_llm)
    return mock
