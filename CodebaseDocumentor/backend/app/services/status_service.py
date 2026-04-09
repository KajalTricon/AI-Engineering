"""
Status updates
"""

import uuid
from datetime import datetime

from sqlalchemy import update

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.repository import Repository


logger = get_logger("codebase_documentor.status")


async def set_status(
    repo_id: str,
    status: str,
    error: str | None = None,
):
    logger.info(
        "repo_status_update repo_id=%s status=%s error=%s",
        repo_id,
        status,
        error or "-",
    )

    async with SessionLocal() as session:

        await session.execute(
            update(Repository)
            .where(
                Repository.id == uuid.UUID(repo_id)
            )
            .values(
                status=status,
                error_message=error,
                updated_at=datetime.utcnow(),
            )
        )

        await session.commit()
