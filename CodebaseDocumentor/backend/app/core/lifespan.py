"""
FastAPI lifespan
"""

import asyncio
from contextlib import asynccontextmanager

from sqlalchemy import select
from fastapi import FastAPI

from app.core.db import SessionLocal, init_db
from app.models.project import Project
from app.services.pipeline_service import process_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown
    """

    await init_db()

    print("DB ready")

    async with SessionLocal() as session:
        result = await session.execute(
            select(Project.id).where(Project.status.in_(["pending", "processing"]))
        )
        resumable_project_ids = [str(row[0]) for row in result.all()]

    for project_id in resumable_project_ids:
        asyncio.create_task(process_project(project_id))

    yield
