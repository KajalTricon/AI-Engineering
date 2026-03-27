"""
Repository routes
"""

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    Response,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.repository import (
    SubmitRepoRequest,
    SubmitRepoResponse,
    RepoStatusResponse,
)

from app.schemas.module import (
    ModulesResponse,
)

from app.schemas.documentation import (
    DocumentationResponse,
)

from app.schemas.query import (
    QueryRequest,
    QueryResponse,
)

from app.services import (
    repository_service,
    pipeline_service,
    query_service,
    documentation_service,
)


router = APIRouter(
    prefix="/repositories",
    tags=["repositories"],
)


# ----------------------------------------
# submit repo
# ----------------------------------------

@router.post(
    "",
    response_model=SubmitRepoResponse,
    status_code=202,
)
async def submit_repository(
    body: SubmitRepoRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await repository_service.submit_repository(
        db,
        body.github_url,
    )

    if result.should_process:
        response.status_code = 202
        background_tasks.add_task(
            pipeline_service.process_repository,
            str(result.repository.id),
            result.repository.github_url,
        )
    else:
        response.status_code = 200

    return SubmitRepoResponse(
        repo_id=str(result.repository.id),
        status=result.repository.status,
        message=result.message,
        reused=result.reused,
        commit_sha=result.commit_sha,
    )


# ----------------------------------------
# status
# ----------------------------------------

@router.get(
    "/{repo_id}",
    response_model=RepoStatusResponse,
)
async def get_status(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):

    return await repository_service.get_status(
        db,
        repo_id,
    )


# ----------------------------------------
# modules
# ----------------------------------------

@router.get(
    "/{repo_id}/modules",
    response_model=ModulesResponse,
)
async def get_modules(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):

    return await repository_service.get_modules(
        db,
        repo_id,
    )


# ----------------------------------------
# docs
# ----------------------------------------

@router.get(
    "/{repo_id}/documentation",
    response_model=DocumentationResponse,
)
async def get_docs(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):

    return await documentation_service.get_docs(
        db,
        repo_id,
    )


# ----------------------------------------
# query
# ----------------------------------------

@router.post(
    "/{repo_id}/query",
    response_model=QueryResponse,
)
async def query_repo(
    repo_id: str,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
):

    return await query_service.query_repo(
        db,
        repo_id,
        body.question,
    )
