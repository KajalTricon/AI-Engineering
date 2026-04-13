"""
Main API router
"""

from fastapi import APIRouter

from app.api.routes.projects import router as projects_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(projects_router)
