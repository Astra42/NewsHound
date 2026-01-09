"""
Database connection configuration.

Принцип SOLID:
- Single Responsibility: только подключение к БД
"""

from typing import AsyncGenerator, Generator

from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Sync engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Async engine (для asyncpg)
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения синхронной сессии БД.

    Использование в FastAPI:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения асинхронной сессии БД.

    Использование в FastAPI:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Создание всех таблиц в БД."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с БД."""
    await async_engine.dispose()
