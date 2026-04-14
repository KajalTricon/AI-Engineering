"""
Project processing pipeline
"""

import re
import shutil
import uuid
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.agents.doc_agent import generate_project_documentation
from app.chunker.module_chunker import chunk_repository
from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.documentation import Documentation
from app.models.project import Project
from app.models.repository import Repository
from app.services.git_service import get_local_head_commit, get_remote_head_commit
from app.services.module_service import (
    analyze_modules,
    get_repository_module_summaries,
    store_modules,
)
from app.services.status_service import refresh_project_status, set_project_status, set_repository_status
from app.utils.clone_helper import clone_repo


logger = get_logger("codebase_documentor.pipeline")


async def process_project(project_id: str) -> None:
    logger.info("pipeline_start project_id=%s", project_id)
    await set_project_status(project_id, "processing", None)

    all_module_summaries: list[dict] = []
    repository_profiles: list[dict] = []

    try:
        async with SessionLocal() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            repositories = await _load_project_repositories(session, project_id)

        for repository in repositories:
            repository_name = repository.name or repository.github_url.rstrip("/").split("/")[-1]

            # Check if repository is already completed
            if repository.status == "completed":
                # If we have a stored commit SHA, check if there are new commits
                if repository.commit_sha:
                    try:
                        remote_commit = await get_remote_head_commit(repository.github_url)
                        
                        # No new commits, skip processing
                        if remote_commit == repository.commit_sha:
                            existing_summaries = await get_repository_module_summaries(str(repository.id), repository_name)
                            all_module_summaries.extend(existing_summaries)
                            repository_profiles.append(
                                _build_repository_profile(repository_name, repository.github_url, existing_summaries)
                            )
                            logger.info(
                                "pipeline_repository_skip project_id=%s repo_id=%s reason=already_completed_no_new_commits commit=%s",
                                project_id,
                                repository.id,
                                repository.commit_sha[:8],
                            )
                            continue
                        else:
                            # New commits detected, reprocess the repository
                            logger.info(
                                "pipeline_repository_reprocess project_id=%s repo_id=%s reason=new_commits old_commit=%s new_commit=%s",
                                project_id,
                                repository.id,
                                repository.commit_sha[:8],
                                remote_commit[:8],
                            )
                            await set_repository_status(str(repository.id), "pending", None)
                    except Exception as exc:
                        logger.warning(
                            "pipeline_repository_commit_check_failed project_id=%s repo_id=%s error=%s continuing_with_reprocess",
                            project_id,
                            repository.id,
                            str(exc),
                        )
                        # If we can't check remote commit, reprocess to be safe
                        await set_repository_status(str(repository.id), "pending", None)
                else:
                    # Completed but no commit SHA stored, use existing summaries
                    existing_summaries = await get_repository_module_summaries(str(repository.id), repository_name)
                    all_module_summaries.extend(existing_summaries)
                    repository_profiles.append(
                        _build_repository_profile(repository_name, repository.github_url, existing_summaries)
                    )
                    logger.info(
                        "pipeline_repository_skip project_id=%s repo_id=%s reason=already_completed_no_commit_sha",
                        project_id,
                        repository.id,
                    )
                    continue

            # Process repositories that are not completed or need reprocessing
            await set_repository_status(str(repository.id), "processing", None)
            await refresh_project_status(project_id)

            module_summaries = await _process_repository(project_id, repository)
            all_module_summaries.extend(module_summaries)
            repository_profiles.append(
                _build_repository_profile(repository_name, repository.github_url, module_summaries)
            )

        _attach_cross_repository_dependencies(repository_profiles, all_module_summaries)

        async with SessionLocal() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            docs = await generate_project_documentation(
                project_name=project.name if project else "Project",
                repositories=repository_profiles,
                module_summaries=all_module_summaries,
                project_id=project_id,
            )

            existing = await session.execute(
                select(Documentation).where(Documentation.project_id == uuid.UUID(project_id))
            )
            current_doc = existing.scalar_one_or_none()
            payload = docs.json(indent=2)

            if current_doc:
                current_doc.content = payload
            else:
                session.add(Documentation(project_id=uuid.UUID(project_id), content=payload))

            await session.commit()

        await set_project_status(project_id, "completed", None)
        await refresh_project_status(project_id)
        logger.info(
            "pipeline_complete project_id=%s repository_count=%s module_count=%s",
            project_id,
            len(repository_profiles),
            len(all_module_summaries),
        )
    except Exception as exc:
        await set_project_status(project_id, "failed", str(exc))
        logger.exception("project_processing_failed project_id=%s", project_id)
        raise


async def _process_repository(project_id: str, repository: Repository) -> list[dict]:
    repo_id = str(repository.id)
    repository_name = repository.name or repository.github_url.rstrip("/").split("/")[-1]
    clone_path: str | None = None

    try:
        existing_summaries = await get_repository_module_summaries(repo_id, repository_name)
        if existing_summaries:
            logger.info(
                "pipeline_repository_resume project_id=%s repo_id=%s existing_summary_count=%s",
                project_id,
                repo_id,
                len(existing_summaries),
            )

        clone_path = await clone_repo(repository.github_url, repo_id)
        commit_sha = await get_local_head_commit(clone_path)
        chunks = chunk_repository(clone_path, repository_name)
        stored_modules = await store_modules(project_id, repo_id, repository_name, chunks)
        module_summaries = await analyze_modules(project_id, repo_id, repository_name, stored_modules)

        async with SessionLocal() as session:
            repository_row = await session.get(Repository, repository.id)
            if repository_row:
                repository_row.commit_sha = commit_sha
                repository_row.status = "completed"
                repository_row.error_message = None
                await session.commit()

        return module_summaries
    except Exception as exc:
        await set_repository_status(repo_id, "failed", str(exc))
        await refresh_project_status(project_id)
        logger.exception(
            "project_repository_failed project_id=%s repo_id=%s github_url=%s",
            project_id,
            repository.id,
            repository.github_url,
        )
        raise
    finally:
        if clone_path:
            shutil.rmtree(clone_path, ignore_errors=True)


async def _load_project_repositories(session, project_id: str) -> list[Repository]:
    result = await session.execute(
        select(Repository).where(Repository.project_id == uuid.UUID(project_id)).order_by(Repository.created_at)
    )
    return list(result.scalars().all())


def _build_repository_profile(repository_name: str, github_url: str, module_summaries: list[dict]) -> dict:
    top_modules = module_summaries[:6]
    summary_parts = [item["summary"] for item in top_modules if item.get("summary")]
    summary = " ".join(summary_parts[:3]).strip() or f"Repository {repository_name} contains {len(module_summaries)} documented modules."

    return {
        "name": repository_name,
        "github_url": github_url,
        "summary": summary,
        "key_modules": [item["name"] for item in top_modules],
        "depends_on": [],
    }


def _attach_cross_repository_dependencies(repository_profiles: list[dict], module_summaries: list[dict]) -> None:
    repository_tokens: dict[str, set[str]] = {}
    profile_by_name = {profile["name"]: profile for profile in repository_profiles}

    for profile in repository_profiles:
        repository_tokens[profile["name"]] = _name_tokens(profile["name"])

    dependencies_by_repo: dict[str, set[str]] = defaultdict(set)

    for module in module_summaries:
        source_repo = module["repository"]
        evidence = " ".join(module.get("dependencies", []) + [module.get("summary", "")]).lower()
        for target_repo, tokens in repository_tokens.items():
            if target_repo == source_repo:
                continue
            if any(token and re.search(rf"\b{re.escape(token)}\b", evidence) for token in tokens):
                dependencies_by_repo[source_repo].add(target_repo)

    for repository_name, targets in dependencies_by_repo.items():
        if repository_name in profile_by_name:
            profile_by_name[repository_name]["depends_on"] = sorted(targets)


def _name_tokens(name: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", name.lower())
        if token and len(token) > 2
    }
 