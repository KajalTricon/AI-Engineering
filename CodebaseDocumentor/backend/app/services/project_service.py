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
    individual_projects: list[Project] = None  # Individual projects for each repo

    def __post_init__(self):
        if self.individual_projects is None:
            self.individual_projects = []


async def submit_project(db: AsyncSession, project_name: str | None, github_urls: list[str]) -> ProjectSubmissionResult:
    normalized_urls = repository_service.validate_submission_urls(github_urls)
    
    # For single repo, check if we can reuse existing
    if len(normalized_urls) == 1:
        commit_sha = await repository_service.try_get_remote_commit(normalized_urls[0])
        if commit_sha:
            existing_repo = await repository_service.find_existing_completed_repository(db, normalized_urls[0])
            if existing_repo and existing_repo.commit_sha == commit_sha and existing_repo.project_id:
                existing_project = await db.get(Project, existing_repo.project_id)
                if existing_project and existing_project.status == "completed":
                    await db.refresh(existing_project)
                    await db.refresh(existing_repo)
                    return ProjectSubmissionResult(
                        project=existing_project,
                        repositories=[existing_repo],
                        individual_projects=[]
                    )
    
    individual_projects = []
    individual_repos_map = {}  # project_id -> repo
    
    # If multiple repos, create individual projects for each
    if len(normalized_urls) > 1:
        for normalized_url in normalized_urls:
            commit_sha = await repository_service.try_get_remote_commit(normalized_url)
            existing_repo = await repository_service.find_existing_completed_repository(db, normalized_url)
            
            # Check if we can reuse existing individual project
            if existing_repo and existing_repo.commit_sha == commit_sha and existing_repo.project_id:
                existing_project = await db.get(Project, existing_repo.project_id)
                # Only reuse if it's a single-repo project (not a combined one)
                if existing_project and existing_project.status == "completed" and existing_project.repository_count == 1:
                    await db.refresh(existing_project)
                    await db.refresh(existing_repo)
                    individual_projects.append(existing_project)
                    individual_repos_map[str(existing_project.id)] = existing_repo
                    continue
            
            # Create new individual project for this repo
            repo_name = normalized_url.rstrip("/").split("/")[-1]
            individual_project = Project(
                name=repo_name,
                status="pending",
                repository_count=1,
            )
            db.add(individual_project)
            await db.flush()
            
            # Determine status based on existing repo
            status = "pending"
            if existing_repo and existing_repo.commit_sha and commit_sha:
                if existing_repo.commit_sha == commit_sha:
                    status = "completed"
            
            individual_repo = Repository(
                project_id=individual_project.id,
                github_url=normalized_url,
                normalized_url=normalized_url,
                name=repo_name,
                commit_sha=commit_sha,
                status=status,
            )
            db.add(individual_repo)
            await db.flush()
            
            individual_projects.append(individual_project)
            individual_repos_map[str(individual_project.id)] = individual_repo
    
    # Create combined project with proper naming
    if len(normalized_urls) > 1:
        if project_name:
            display_name = project_name
        else:
            # Extract repo names and join them (without "Combined")
            repo_names = [url.rstrip("/").split("/")[-1] for url in normalized_urls]
            display_name = "+".join(repo_names)
    else:
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
        
        # Check if this repository was already completed
        existing_repo = await repository_service.find_existing_completed_repository(db, normalized_url)
        
        # Determine initial status
        if existing_repo and existing_repo.commit_sha and commit_sha:
            if existing_repo.commit_sha == commit_sha:
                status = "completed"
            else:
                status = "pending"
        else:
            status = "pending"
        
        repository = Repository(
            project_id=project.id,
            github_url=normalized_url,
            normalized_url=normalized_url,
            name=repo_name,
            commit_sha=commit_sha,
            status=status,
        )
        db.add(repository)
        repositories.append(repository)

    await db.commit()

    # Refresh all objects to get IDs and latest state
    await db.refresh(project)
    for repo in repositories:
        await db.refresh(repo)
    for individual_project in individual_projects:
        await db.refresh(individual_project)
    for repo in individual_repos_map.values():
        await db.refresh(repo)

    return ProjectSubmissionResult(
        project=project,
        repositories=repositories,
        individual_projects=individual_projects
    )


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
    from app.schemas.project import ProjectSummary
    
    related_projects = []
    if result.individual_projects:
        for proj in result.individual_projects:
            related_projects.append(ProjectSummary(
                project_id=str(proj.id),
                name=proj.name,
                status=proj.status,
                repository_count=proj.repository_count
            ))
    
    # Add combined project
    related_projects.append(ProjectSummary(
        project_id=str(result.project.id),
        name=result.project.name,
        status=result.project.status,
        repository_count=result.project.repository_count
    ))
    
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
        related_projects=related_projects if len(related_projects) > 1 else None
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
 