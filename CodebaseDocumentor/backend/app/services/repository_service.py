"""
Repository helpers
"""

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, not_found
from app.models.repository import Repository
from app.schemas.repository import RepoStatusResponse
from app.services.git_service import get_remote_head_commit, normalize_github_url


def validate_submission_urls(github_urls: Iterable[str]) -> list[str]:
    normalized_urls: list[str] = []
    seen_urls: set[str] = set()

    for github_url in github_urls:
        try:
            normalized_url = normalize_github_url(github_url)
        except ValueError as exc:
            raise bad_request(str(exc)) from exc

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)
        normalized_urls.append(normalized_url)

    if not normalized_urls:
        raise bad_request("At least one valid GitHub repository URL is required.")

    return normalized_urls


async def get_repository(db: AsyncSession, repo_id: str) -> Repository:
    try:
        repository_uuid = uuid.UUID(repo_id)
    except ValueError as exc:
        raise bad_request("Invalid repository id.") from exc

    result = await db.execute(select(Repository).where(Repository.id == repository_uuid))
    repository = result.scalar_one_or_none()
    if not repository:
        raise not_found("Repository not found.")
    return repository


async def get_status(db: AsyncSession, repo_id: str) -> RepoStatusResponse:
    repository = await get_repository(db, repo_id)
    return RepoStatusResponse(
        repo_id=str(repository.id),
        project_id=str(repository.project_id) if repository.project_id else None,
        github_url=repository.github_url,
        name=repository.name,
        normalized_url=repository.normalized_url,
        commit_sha=repository.commit_sha,
        status=repository.status,
        error_message=repository.error_message,
        created_at=repository.created_at,
        updated_at=repository.updated_at,
    )


async def try_get_remote_commit(normalized_url: str) -> str | None:
    try:
        return await get_remote_head_commit(normalized_url)
    except Exception:
        return None


async def find_existing_completed_repository(db: AsyncSession, normalized_url: str) -> Repository | None:
    """
    Find a completed repository with the same normalized URL from any project.
    Returns the most recently completed repository if found, None otherwise.
    """
    result = await db.execute(
        select(Repository)
        .where(Repository.normalized_url == normalized_url)
        .where(Repository.status == "completed")
        .order_by(Repository.updated_at.desc())
    )
    return result.scalars().first()
 