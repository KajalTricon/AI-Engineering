"""
Database engine + session
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import settings
from app.models import Documentation, Module, Project, Repository  # noqa: F401
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
    Create extension + tables.
    """

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

        await conn.execute(text("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS project_id UUID"))
        await conn.execute(text("ALTER TABLE modules ADD COLUMN IF NOT EXISTS project_id UUID"))
        await conn.execute(text("ALTER TABLE modules ADD COLUMN IF NOT EXISTS repository_name VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE documentation ADD COLUMN IF NOT EXISTS project_id UUID"))
        await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS repository_count INTEGER DEFAULT 0"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_repositories_project_id ON repositories (project_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_modules_project_id ON modules (project_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_modules_repository_id ON modules (repository_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documentation_project_id ON documentation (project_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_repositories_normalized_url ON repositories (normalized_url)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_repositories_commit_sha ON repositories (commit_sha)"))


async def get_db():
    """
    FastAPI dependency.
    """

    async with SessionLocal() as session:
        yield session
