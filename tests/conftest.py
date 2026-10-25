import os
from collections.abc import AsyncIterator

# Тесты работают с отдельной базой tasks_test. Адрес можно переопределить через
# TEST_DATABASE_URL (например, если PostgreSQL запущен на другом порту).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/tasks_test"
)
# app.config читает DATABASE_URL при импорте, поэтому задаём его до импорта приложения
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.db import Base, get_session
from app.main import app


async def create_test_database() -> None:
    """Создаёт базу tasks_test, если её ещё нет."""
    url = make_url(TEST_DATABASE_URL)
    admin = create_async_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    await admin.dispose()


@pytest.fixture(scope="session")
async def engine():
    await create_test_database()
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    # В тестовой базе схему можно пересоздавать целиком, миграции нужны только для рабочей
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    # Каждый тест начинается с пустых таблиц
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE tasks, users RESTART IDENTITY CASCADE"))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user(client: AsyncClient) -> dict:
    response = await client.post("/users", json={"email": "ivan@example.com", "name": "Иван"})
    return response.json()
