"""
Database engine + session
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from sqlalchemy import text

from app.core.settings import settings
from app.models.base import Base


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """
    Create extension + tables
    """

    async with engine.begin() as conn:

        await conn.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE repositories "
                "ADD COLUMN IF NOT EXISTS normalized_url VARCHAR(500)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE repositories "
                "ADD COLUMN IF NOT EXISTS commit_sha VARCHAR(64)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_repositories_normalized_url "
                "ON repositories (normalized_url)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_repositories_commit_sha "
                "ON repositories (commit_sha)"
            )
        )


async def get_db():
    """
    FastAPI dependency
    """

    async with SessionLocal() as session:
        yield session
