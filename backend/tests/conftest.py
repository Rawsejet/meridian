"""Test fixtures and configuration."""
import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.database import get_engine, init_db, drop_db, get_session
from app.main import create_app
from app.core.security import create_access_token


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
        text = await self.complete(messages, **kwargs)
        import json
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def health_check(self):
        return True

    async def close(self):
        pass


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create a test database and session."""
    _settings = Settings(
        test_database_url="postgresql+asyncpg://meridian:meridian@localhost:5432/meridian_test"
    )
    engine = create_async_engine(_settings.test_database_url)

    # Create tables
    from app.core.database import metadata
    async with engine.begin() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS meridian_test"))
        await conn.execute(text("CREATE DATABASE meridian_test"))

    # Reconnect to test DB
    test_engine = create_async_engine(_settings.test_database_url)
    from app.models import *  # noqa: Import all models
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    yield test_engine

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    factory = sessionmaker(bind=test_db, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


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


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    _settings = Settings(
        database_url="postgresql+asyncpg://meridian:meridian@localhost:5432/meridian_test",
        jwt_secret="test-secret",
        debug=True,
    )
    return create_app(_settings)


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)