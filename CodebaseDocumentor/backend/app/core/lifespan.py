"""
FastAPI lifespan
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown
    """

    await init_db()

    print("DB ready")

    yield