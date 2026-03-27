"""
Repository service
"""

import uuid
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, not_found
from app.models.repository import Repository
from app.models.module import Module
from app.services.git_service import (
    get_remote_head_commit,
    normalize_github_url,
)

from app.schemas.repository import RepoStatusResponse
from app.schemas.module import ModulesResponse, ModuleSummary


@dataclass
class RepositorySubmissionResult:
    repository: Repository
    should_process: bool
    reused: bool
    commit_sha: str | None
    message: str


async def submit_repository(
    db: AsyncSession,
    github_url: str,
) -> RepositorySubmissionResult:
    try:
        normalized_url = normalize_github_url(github_url)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    remote_commit = await _try_get_remote_commit(normalized_url)
    existing_repo = None

    if remote_commit:
        existing_repo = await _find_existing_submission(
            db,
            normalized_url=normalized_url,
            commit_sha=remote_commit,
        )

    if existing_repo and existing_repo.status != "failed":
        return RepositorySubmissionResult(
            repository=existing_repo,
            should_process=False,
            reused=True,
            commit_sha=existing_repo.commit_sha,
            message=_build_reuse_message(existing_repo.status),
        )

    name = normalized_url.rstrip("/").split("/")[-1]

    repo = Repository(
        github_url=normalized_url,
        normalized_url=normalized_url,
        name=name,
        status="pending",
        commit_sha=remote_commit,
    )

    db.add(repo)

    await db.commit()
    await db.refresh(repo)

    return RepositorySubmissionResult(
        repository=repo,
        should_process=True,
        reused=False,
        commit_sha=remote_commit,
        message="Processing started",
    )


# ----------------------------
# get status
# ----------------------------

async def get_status(
    db: AsyncSession,
    repo_id: str,
) -> RepoStatusResponse:

    repo = await _get_repo(db, repo_id)

    return RepoStatusResponse(
        repo_id=str(repo.id),
        github_url=repo.github_url,
        name=repo.name,
        normalized_url=repo.normalized_url,
        commit_sha=repo.commit_sha,
        status=repo.status,
        error_message=repo.error_message,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


# ----------------------------
# modules
# ----------------------------

async def get_modules(
    db: AsyncSession,
    repo_id: str,
) -> ModulesResponse:

    repo = await _get_repo(db, repo_id)
    modules = await _get_repo_modules(db, repo.id)

    return ModulesResponse(
        repo_id=repo_id,
        total_modules=len(modules),
        modules=_serialize_modules(modules),
    )


async def get_repository(
    db: AsyncSession,
    repo_id: str,
) -> Repository:
    return await _get_repo(db, repo_id)


def require_completed(repo: Repository) -> None:
    if repo.status == "failed":
        raise bad_request(repo.error_message or "Repository processing failed.")

    if repo.status != "completed":
        raise bad_request("Repository documentation is not ready yet.")


# ----------------------------
# helper
# ----------------------------

async def _get_repo(
    db: AsyncSession,
    repo_id: str,
) -> Repository:
    try:
        uid = uuid.UUID(repo_id)
    except ValueError as exc:
        raise bad_request("Invalid repository id.") from exc

    result = await db.execute(
        select(Repository).where(
            Repository.id == uid
        )
    )

    repo = result.scalar_one_or_none()

    if not repo:
        raise not_found("Repository not found.")

    return repo


async def update_commit_sha(
    db: AsyncSession,
    repo_id: str,
    commit_sha: str,
) -> None:
    repo = await _get_repo(db, repo_id)
    repo.commit_sha = commit_sha
    await db.commit()


async def _find_existing_submission(
    db: AsyncSession,
    normalized_url: str,
    commit_sha: str,
) -> Repository | None:
    result = await db.execute(
        select(Repository)
        .where(Repository.normalized_url == normalized_url)
        .where(Repository.commit_sha == commit_sha)
        .order_by(desc(Repository.updated_at))
    )
    return result.scalars().first()


async def _try_get_remote_commit(normalized_url: str) -> str | None:
    try:
        return await get_remote_head_commit(normalized_url)
    except Exception:
        return None


def _build_reuse_message(status: str) -> str:
    if status == "completed":
        return "Existing documentation reused for the latest commit."

    return "An existing processing run for the latest commit is already in progress."


async def _get_repo_modules(
    db: AsyncSession,
    repository_id: uuid.UUID,
) -> list[Module]:
    result = await db.execute(
        select(Module).where(Module.repository_id == repository_id)
    )
    return list(result.scalars().all())


def _serialize_modules(modules: Iterable[Module]) -> list[ModuleSummary]:
    return [
        ModuleSummary(
            module_id=str(module.id),
            name=module.name,
            path=module.path,
            language=module.language,
            summary=module.summary,
            dependencies=module.dependencies or [],
        )
        for module in modules
    ]
