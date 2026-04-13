"""
Project routes
"""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.documentation import DocumentationResponse
from app.schemas.module import ModulesResponse
from app.schemas.project import ProjectStatusResponse, SubmitProjectRequest, SubmitProjectResponse
from app.schemas.query import QueryRequest, QueryResponse
from app.services import documentation_service, pipeline_service, project_service, query_service


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=SubmitProjectResponse, status_code=202)
async def submit_project(body: SubmitProjectRequest, db: AsyncSession = Depends(get_db)):
    result = await project_service.submit_project(db, body.project_name, body.urls)
    asyncio.create_task(pipeline_service.process_project(str(result.project.id)))
    return await project_service.build_submit_response(result)


@router.get("/{project_id}", response_model=ProjectStatusResponse)
async def get_status(project_id: str, db: AsyncSession = Depends(get_db)):
    return await project_service.get_status(db, project_id)


@router.get("/{project_id}/modules", response_model=ModulesResponse)
async def get_modules(project_id: str, db: AsyncSession = Depends(get_db)):
    return await project_service.get_modules(db, project_id)


@router.get("/{project_id}/documentation", response_model=DocumentationResponse)
async def get_docs(project_id: str, db: AsyncSession = Depends(get_db)):
    return await documentation_service.get_docs(db, project_id)


@router.post("/{project_id}/query", response_model=QueryResponse)
async def query_project(project_id: str, body: QueryRequest, db: AsyncSession = Depends(get_db)):
    return await query_service.query_project(db, project_id, body.question)


@router.post("/{project_id}/resume", response_model=ProjectStatusResponse)
async def resume_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await project_service.get_project(db, project_id)
    asyncio.create_task(pipeline_service.process_project(project_id))
    return await project_service.get_status(db, str(project.id))
