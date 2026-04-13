"""
Module processing
"""

import uuid
from typing import Iterable

from sqlalchemy import select, update

from app.agents.analyzer_agent import build_analyzer_agent
from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.module import Module
from app.vector.vector_store import store_module


logger = get_logger("codebase_documentor.modules")


async def store_modules(project_id: str, repo_id: str, repository_name: str, chunks) -> list[dict]:
    project_uuid = uuid.UUID(project_id)
    repository_uuid = uuid.UUID(repo_id)

    logger.info(
        "store_modules_start project_id=%s repo_id=%s chunk_count=%s",
        project_id,
        repo_id,
        len(chunks),
    )

    async with SessionLocal() as session:
        result = await session.execute(
            select(Module).where(Module.repository_id == repository_uuid)
        )
        existing_modules = {
            module.path: module
            for module in result.scalars().all()
        }

        stored_modules: list[dict] = []

        for index, chunk in enumerate(chunks, start=1):
            clean_content = chunk.full_content.replace("\x00", "")
            existing = existing_modules.get(chunk.path)

            if existing is None:
                logger.info(
                    "store_module_row project_id=%s repo_id=%s index=%s/%s repo=%s path=%s action=insert",
                    project_id,
                    repo_id,
                    index,
                    len(chunks),
                    repository_name,
                    chunk.path,
                )
                existing = Module(
                    project_id=project_uuid,
                    repository_id=repository_uuid,
                    repository_name=repository_name,
                    name=chunk.name,
                    path=chunk.path,
                    language=chunk.language,
                    full_content=clean_content,
                )
                session.add(existing)
                await session.flush()
                await store_module(
                    project_id=project_id,
                    repo_id=repo_id,
                    repository_name=repository_name,
                    module_id=str(existing.id),
                    module_name=existing.name,
                    module_path=existing.path,
                    language=existing.language or "unknown",
                    full_content=clean_content,
                )
            else:
                logger.info(
                    "store_module_row project_id=%s repo_id=%s index=%s/%s repo=%s path=%s action=reuse",
                    project_id,
                    repo_id,
                    index,
                    len(chunks),
                    repository_name,
                    chunk.path,
                )
                if not existing.full_content:
                    existing.full_content = clean_content
                if not existing.language:
                    existing.language = chunk.language
                if not existing.repository_name:
                    existing.repository_name = repository_name

            stored_modules.append(
                {
                    "project_id": project_id,
                    "repository_id": repo_id,
                    "repository_name": repository_name,
                    "module_id": str(existing.id),
                    "module_name": existing.name,
                    "module_path": existing.path,
                    "language": existing.language or chunk.language or "unknown",
                    "full_content": existing.full_content or clean_content,
                    "source_files": chunk.source_files,
                    "summary": existing.summary,
                    "dependencies": existing.dependencies or [],
                }
            )

        await session.commit()

    return stored_modules


async def analyze_modules(project_id: str, repo_id: str, repository_name: str, modules: Iterable[dict]) -> list[dict]:
    agent = build_analyzer_agent()
    module_list = list(modules)
    summaries: list[dict] = []

    logger.info(
        "analyze_modules_start project_id=%s repo_id=%s module_count=%s",
        project_id,
        repo_id,
        len(module_list),
    )

    for index, module in enumerate(module_list, start=1):
        if module.get("summary"):
            summaries.append(
                {
                    "repository": repository_name,
                    "repository_id": repo_id,
                    "name": module["module_name"],
                    "path": module["module_path"],
                    "summary": module["summary"],
                    "dependencies": module.get("dependencies", []),
                    "responsibilities": module.get("responsibilities", []),
                    "important_files": module.get("important_files", []),
                    "source_files": module.get("source_files", []),
                }
            )
            logger.info(
                "module_analysis_skip project_id=%s repo_id=%s index=%s/%s path=%s reason=already_summarized",
                project_id,
                repo_id,
                index,
                len(module_list),
                module["module_path"],
            )
            continue

        result = await agent.ainvoke(
            {
                "project_id": project_id,
                "repository_id": repo_id,
                "repository_name": repository_name,
                "module_id": module["module_id"],
                "module_name": module["module_name"],
                "module_path": module["module_path"],
                "language": module["language"],
                "full_content": module["full_content"],
                "source_files": module.get("source_files", []),
                "retrieved_context": [],
                "analysis": "",
                "title": "",
                "summary": "",
                "dependencies": [],
                "responsibilities": [],
                "important_files": [],
                "iterations": 0,
            }
        )

        async with SessionLocal() as session:
            await session.execute(
                update(Module)
                .where(Module.id == uuid.UUID(module["module_id"]))
                .values(
                    name=result["title"],
                    summary=result["summary"],
                    dependencies=result["dependencies"],
                    repository_name=repository_name,
                )
            )
            await session.commit()

        summaries.append(
            {
                "repository": repository_name,
                "repository_id": repo_id,
                "name": result["title"],
                "path": module["module_path"],
                "summary": result["summary"],
                "dependencies": result["dependencies"],
                "responsibilities": result.get("responsibilities", []),
                "important_files": result.get("important_files", []),
                "source_files": module.get("source_files", []),
            }
        )

        logger.info(
            "module_analysis_complete project_id=%s repo_id=%s index=%s/%s path=%s summary_chars=%s",
            project_id,
            repo_id,
            index,
            len(module_list),
            module["module_path"],
            len(result["summary"] or ""),
        )

    return summaries


async def get_repository_module_summaries(repo_id: str, repository_name: str) -> list[dict]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Module).where(Module.repository_id == uuid.UUID(repo_id)).order_by(Module.path)
        )
        modules = list(result.scalars().all())

    return [
        {
            "repository": repository_name,
            "repository_id": repo_id,
            "name": module.name,
            "path": module.path,
            "summary": module.summary or "",
            "dependencies": module.dependencies or [],
            "responsibilities": [],
            "important_files": [],
            "source_files": [],
        }
        for module in modules
        if module.summary
    ]
