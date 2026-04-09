"""
Main pipeline
"""

import shutil
import uuid
from pathlib import Path

from app.services.module_service import (
    store_modules,
    analyze_modules,
)
from app.services.status_service import set_status

from app.agents.doc_agent import generate_project_documentation
from app.chunker.module_chunker import chunk_repository
from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.documentation import Documentation
from app.models.repository import Repository
from app.services.git_service import get_local_head_commit
from app.utils.clone_helper import clone_repo


logger = get_logger("codebase_documentor.pipeline")


async def process_repository(
    repo_id: str,
    github_url: str,
):
    clone_path = None

    logger.info(
        "pipeline_start repo_id=%s github_url=%s",
        repo_id,
        github_url,
    )

    try:
        await set_status(repo_id, "processing")
        clone_path = await clone_repo(github_url, repo_id)
        logger.info(
            "pipeline_clone_complete repo_id=%s clone_path=%s",
            repo_id,
            clone_path,
        )
        commit_sha = await get_local_head_commit(clone_path)
        chunks = chunk_repository(clone_path)
        logger.info(
            "pipeline_chunk_complete repo_id=%s chunk_count=%s commit_sha=%s",
            repo_id,
            len(chunks),
            commit_sha,
        )
        modules = await store_modules(repo_id, chunks)
        logger.info(
            "pipeline_store_complete repo_id=%s stored_modules=%s",
            repo_id,
            len(modules),
        )
        summaries = await analyze_modules(repo_id, modules)
        logger.info(
            "pipeline_analysis_complete repo_id=%s summarized_modules=%s",
            repo_id,
            len(summaries),
        )
        name = Path(clone_path).name

        docs = await generate_project_documentation(
            project_name=name,
            github_url=github_url,
            module_summaries=summaries,
            repo_id=repo_id,
        )
        logger.info(
            "pipeline_documentation_complete repo_id=%s module_summary_count=%s",
            repo_id,
            len(summaries),
        )

        async with SessionLocal() as session:
            repository = await session.get(Repository, uuid.UUID(repo_id))
            if repository:
                repository.commit_sha = commit_sha

            session.add(
                Documentation(
                    repository_id=uuid.UUID(repo_id),
                    content=docs.json(indent=2),
                )
            )
            await session.commit()

        await set_status(repo_id, "completed")
        logger.info(
            "pipeline_complete repo_id=%s github_url=%s",
            repo_id,
            github_url,
        )
    except Exception as e:
        await set_status(repo_id, "failed", str(e))
        logger.exception(
            "Repository processing failed repo_id=%s github_url=%s",
            repo_id,
            github_url,
        )
    finally:
        if clone_path:
            shutil.rmtree(clone_path, ignore_errors=True)
