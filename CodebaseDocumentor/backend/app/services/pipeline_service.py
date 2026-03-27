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
from app.models.documentation import Documentation
from app.models.repository import Repository
from app.services.git_service import get_local_head_commit
from app.utils.clone_helper import clone_repo


async def process_repository(
    repo_id: str,
    github_url: str,
):
    clone_path = None

    try:
        await set_status(repo_id, "processing")
        clone_path = await clone_repo(github_url, repo_id)
        commit_sha = await get_local_head_commit(clone_path)
        chunks = chunk_repository(clone_path)
        modules = await store_modules(repo_id, chunks)
        summaries = await analyze_modules(repo_id, modules)
        name = Path(clone_path).name

        docs = await generate_project_documentation(
            project_name=name,
            github_url=github_url,
            module_summaries=summaries,
            repo_id=repo_id,
        )
        print("Generated documentation:", docs)

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
    except Exception as e:
        await set_status(repo_id, "failed", str(e))
        raise
    finally:
        if clone_path:
            shutil.rmtree(clone_path, ignore_errors=True)
