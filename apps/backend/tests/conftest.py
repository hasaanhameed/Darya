import pytest
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    """A database session whose changes are rolled back after the test, so tests leave no data behind."""
    # NullPool: each test runs in its own event loop, so connections must not be reused between tests
    engine = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
        yield session
        await session.close()
        await transaction.rollback()
    await engine.dispose()
