"""
Project service
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import bad_request, not_found
from app.models.module import Module
from app.models.project import Project
from app.models.repository import Repository
from app.schemas.module import ModuleSummary, ModulesResponse
from app.schemas.project import ProjectStatusResponse, SubmittedRepository, SubmitProjectResponse
from app.services import repository_service


@dataclass
class ProjectSubmissionResult:
    project: Project
    repositories: list[Repository]


async def submit_project(db: AsyncSession, project_name: str | None, github_urls: list[str]) -> ProjectSubmissionResult:
    normalized_urls = repository_service.validate_submission_urls(github_urls)
    display_name = (project_name or normalized_urls[0].rstrip("/").split("/")[-1]).strip()

    project = Project(
        name=display_name,
        status="pending",
        repository_count=len(normalized_urls),
    )
    db.add(project)
    await db.flush()

    repositories: list[Repository] = []
    for normalized_url in normalized_urls:
        repo_name = normalized_url.rstrip("/").split("/")[-1]
        commit_sha = await repository_service.try_get_remote_commit(normalized_url)
        repository = Repository(
            project_id=project.id,
            github_url=normalized_url,
            normalized_url=normalized_url,
            name=repo_name,
            commit_sha=commit_sha,
            status="pending",
        )
        db.add(repository)
        repositories.append(repository)

    await db.commit()

    for item in [project, *repositories]:
        await db.refresh(item)

    return ProjectSubmissionResult(project=project, repositories=repositories)


async def get_project(db: AsyncSession, project_id: str) -> Project:
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as exc:
        raise bad_request("Invalid project id.") from exc

    result = await db.execute(select(Project).where(Project.id == project_uuid))
    project = result.scalar_one_or_none()
    if not project:
        raise not_found("Project not found.")
    return project


def require_completed(project: Project) -> None:
    if project.status == "failed":
        raise bad_request(project.error_message or "Project processing failed.")
    if project.status != "completed":
        raise bad_request("Project documentation is not ready yet.")


async def get_status(db: AsyncSession, project_id: str) -> ProjectStatusResponse:
    project = await get_project(db, project_id)
    repositories = await _get_project_repositories(db, project.id)

    return ProjectStatusResponse(
        project_id=str(project.id),
        name=project.name,
        status=project.status,
        error_message=project.error_message,
        repository_count=project.repository_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
        repositories=[
            SubmittedRepository(
                repo_id=str(repository.id),
                github_url=repository.github_url,
                name=repository.name,
                status=repository.status,
                commit_sha=repository.commit_sha,
            )
            for repository in repositories
        ],
    )


async def get_modules(db: AsyncSession, project_id: str) -> ModulesResponse:
    project = await get_project(db, project_id)
    modules = await _get_project_modules(db, project.id)

    return ModulesResponse(
        project_id=str(project.id),
        total_modules=len(modules),
        modules=[
            ModuleSummary(
                module_id=str(module.id),
                repository_id=str(module.repository_id),
                repository_name=module.repository_name,
                name=module.name,
                path=module.path,
                language=module.language,
                summary=module.summary,
                dependencies=module.dependencies or [],
            )
            for module in modules
        ],
    )


async def list_project_repositories(db: AsyncSession, project_id: str) -> list[Repository]:
    project = await get_project(db, project_id)
    return await _get_project_repositories(db, project.id)


async def build_submit_response(result: ProjectSubmissionResult) -> SubmitProjectResponse:
    return SubmitProjectResponse(
        project_id=str(result.project.id),
        name=result.project.name,
        status=result.project.status,
        message="Project processing started",
        repositories=[
            SubmittedRepository(
                repo_id=str(repository.id),
                github_url=repository.github_url,
                name=repository.name,
                status=repository.status,
                commit_sha=repository.commit_sha,
            )
            for repository in result.repositories
        ],
        total_repositories=len(result.repositories),
    )


async def _get_project_repositories(db: AsyncSession, project_uuid: uuid.UUID) -> list[Repository]:
    result = await db.execute(
        select(Repository).where(Repository.project_id == project_uuid).order_by(Repository.created_at)
    )
    return list(result.scalars().all())


async def _get_project_modules(db: AsyncSession, project_uuid: uuid.UUID) -> list[Module]:
    result = await db.execute(
        select(Module).where(Module.project_id == project_uuid).order_by(Module.repository_name, Module.path)
    )
    return list(result.scalars().all())
