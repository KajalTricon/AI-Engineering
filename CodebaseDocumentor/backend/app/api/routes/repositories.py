import asyncio

from fastapi import (
    APIRouter,
    Depends,
    Response,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.repository import (
    SubmitRepoRequest,
    SubmitRepoResponse,
    RepoStatusResponse,
    SubmittedRepository,
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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    normalized_urls = repository_service.validate_submission_urls(body.urls)
    results = []

    for github_url in normalized_urls:
        result = await repository_service.submit_repository(
            db,
            github_url,
        )
        results.append(result)

        if result.should_process:
            asyncio.create_task(
                pipeline_service.process_repository(
                    str(result.repository.id),
                    result.repository.github_url,
                )
            )

    submitted_repositories = [
        SubmittedRepository(
            repo_id=str(result.repository.id),
            github_url=result.repository.github_url,
            status=result.repository.status,
            message=result.message,
            reused=result.reused,
            commit_sha=result.commit_sha,
        )
        for result in results
    ]

    primary_repository = (
        submitted_repositories[0]
        if len(submitted_repositories) == 1
        else None
    )

    response.status_code = 202 if any(result.should_process for result in results) else 200

    return SubmitRepoResponse(
        repositories=submitted_repositories,
        total_submitted=len(submitted_repositories),
        total_reused=sum(1 for item in submitted_repositories if item.reused),
        repo_id=primary_repository.repo_id if primary_repository else None,
        status=primary_repository.status if primary_repository else None,
        message=primary_repository.message if primary_repository else None,
        reused=primary_repository.reused if primary_repository else None,
        commit_sha=primary_repository.commit_sha if primary_repository else None,
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
