"""
Status updates
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.project import Project
from app.models.repository import Repository


logger = get_logger("codebase_documentor.status")


async def set_repository_status(repo_id: str, status: str, error: str | None = None) -> None:
    logger.info(
        "repo_status_update repo_id=%s status=%s error=%s",
        repo_id,
        status,
        error or "-",
    )

    async with SessionLocal() as session:
        await session.execute(
            update(Repository)
            .where(Repository.id == uuid.UUID(repo_id))
            .values(status=status, error_message=error, updated_at=datetime.utcnow())
        )
        await session.commit()


async def set_project_status(project_id: str, status: str, error: str | None = None) -> None:
    logger.info(
        "project_status_update project_id=%s status=%s error=%s",
        project_id,
        status,
        error or "-",
    )

    async with SessionLocal() as session:
        await session.execute(
            update(Project)
            .where(Project.id == uuid.UUID(project_id))
            .values(status=status, error_message=error, updated_at=datetime.utcnow())
        )
        await session.commit()


async def refresh_project_status(project_id: str) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Repository.status).where(Repository.project_id == uuid.UUID(project_id))
        )
        statuses = [row[0] for row in result.all()]

        if not statuses:
            new_status = "pending"
        elif any(status == "failed" for status in statuses):
            new_status = "failed"
        elif all(status == "completed" for status in statuses):
            new_status = "completed"
        elif any(status == "processing" for status in statuses):
            new_status = "processing"
        else:
            new_status = "pending"

        await session.execute(
            update(Project)
            .where(Project.id == uuid.UUID(project_id))
            .values(status=new_status, updated_at=datetime.utcnow())
        )
        await session.commit()
