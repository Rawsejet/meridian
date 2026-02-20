"""Database connection and session management using SQLAlchemy async."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import Settings, get_settings

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

# Declarative base for ORM models
Base = declarative_base()

_engine = None
_session_factory = None


def get_engine(settings: Settings | None = None):
    """Get database engine."""
    global _engine
    if _engine is None:
        _settings = settings or get_settings()
        _engine = create_async_engine(
            _settings.database_url,
            echo=_settings.debug,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory(settings: Settings | None = None):
    """Get session factory."""
    global _session_factory
    if _session_factory is None:
        _engine = get_engine(settings)
        _session_factory = sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_session(
    settings: Settings | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session (context manager)."""
    factory = get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_async_connection(
    settings: Settings | None = None,
) -> AsyncGenerator[AsyncConnection, None]:
    """Get async database connection for raw SQL."""
    engine = get_engine(settings)
    async with engine.connect() as conn:
        try:
            yield conn
        except Exception:
            raise


async def init_db(settings: Settings | None = None):
    """Initialize database with all tables."""
    from app.models import user, task, daily_plan, notification, pattern  # noqa: Import all models to register metadata

    engine = get_engine(settings)
    async with engine.begin() as conn:
        # Create extension if needed (for UUID generation)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        await conn.run_sync(metadata.create_all)


async def drop_db(settings: Settings | None = None):
    """Drop all database tables."""
    from app.models import user, task, daily_plan, notification, pattern  # noqa: Import all models to register metadata

    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


async def create_test_db(settings: Settings | None = None):
    """Create test database."""
    _settings = settings or get_settings()
    # Drop and recreate test db
    test_engine = create_async_engine(
        _settings.test_database_url,
        echo=_settings.debug,
        isolation_level="AUTOCOMMIT",
    )
    async with test_engine.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS meridian_test"))
        await conn.execute(text("CREATE DATABASE meridian_test"))
    await test_engine.dispose()