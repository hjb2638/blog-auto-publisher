import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_api: tests that make real HTTP requests to WordPress (opt-in via RUN_REAL_API_TESTS=1)",
    )

from app.main import app
from app.core.dependencies import get_settings, get_session
from app.core.config import Settings
from app.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://bojinhu:bojinhu@localhost:5433/blog_test_db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def test_engine():
    import asyncpg
    sys_conn = await asyncpg.connect(
        "postgresql://bojinhu:bojinhu@localhost:5433/postgres"
    )
    exists = await sys_conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname='blog_test_db'"
    )
    if not exists:
        await sys_conn.execute("CREATE DATABASE blog_test_db")
    await sys_conn.close()

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session):
    async def override_get_session():
        yield test_session

    def override_get_settings():
        return Settings()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = override_get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
