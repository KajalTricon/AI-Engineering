"""
Status updates
"""

import uuid
from datetime import datetime

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models.repository import Repository


async def set_status(
    repo_id: str,
    status: str,
    error: str | None = None,
):

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