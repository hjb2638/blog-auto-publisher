from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import get_db


def get_settings() -> Settings:
    return settings


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session
