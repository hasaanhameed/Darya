from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url)

# expire_on_commit=False keeps objects readable after a commit
# (in async code they can't be silently reloaded from the database)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for every table model in app/models/."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: opens one session per request and closes it afterwards."""
    async with SessionLocal() as session:
        yield session
