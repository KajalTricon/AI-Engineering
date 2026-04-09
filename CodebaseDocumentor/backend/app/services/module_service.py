"""
Module processing
"""

import uuid
from typing import Iterable

from sqlalchemy import update

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models.module import Module

from app.vector.vector_store import store_module
from app.agents.analyzer_agent import build_analyzer_agent


logger = get_logger("codebase_documentor.modules")


async def store_modules(
    repo_id: str,
    chunks,
) -> list[dict]:
    repository_id = uuid.UUID(repo_id)
    stored_modules: list[dict] = []
    chunk_count = len(chunks)

    logger.info(
        "store_modules_start repo_id=%s chunk_count=%s",
        repo_id,
        chunk_count,
    )

    async with SessionLocal() as session:
        for index, chunk in enumerate(chunks, start=1):
            clean_content = chunk.full_content.replace("\x00", "")
            logger.info(
                "store_module_row repo_id=%s index=%s/%s path=%s language=%s",
                repo_id,
                index,
                chunk_count,
                chunk.path,
                chunk.language or "unknown",
            )
            module = Module(
                repository_id=repository_id,
                name=chunk.name,
                path=chunk.path,
                language=chunk.language,
                full_content=clean_content,
            )

            session.add(module)
            await session.flush()

            stored_modules.append(
                {
                    "module_id": str(module.id),
                    "module_name": module.name,
                    "module_path": module.path,
                    "language": module.language,
                    "full_content": clean_content,
                    "source_files": chunk.source_files,
                }
            )

        await session.commit()

    for index, module in enumerate(stored_modules, start=1):
        logger.info(
            "store_module_embedding repo_id=%s index=%s/%s module_id=%s path=%s",
            repo_id,
            index,
            len(stored_modules),
            module["module_id"],
            module["module_path"],
        )
        await store_module(
            repo_id=repo_id,
            module_id=module["module_id"],
            module_name=module["module_name"],
            module_path=module["module_path"],
            language=module["language"] or "unknown",
            full_content=module["full_content"],
        )

    logger.info(
        "store_modules_complete repo_id=%s stored_count=%s",
        repo_id,
        len(stored_modules),
    )

    return stored_modules


async def analyze_modules(
    repo_id: str,
    modules: Iterable[dict],
) -> list[dict]:
    agent = build_analyzer_agent()
    summaries = []
    module_list = list(modules)

    logger.info(
        "analyze_modules_start repo_id=%s module_count=%s",
        repo_id,
        len(module_list),
    )

    for index, module in enumerate(module_list, start=1):
        logger.info(
            "module_analysis_start repo_id=%s index=%s/%s module_id=%s path=%s",
            repo_id,
            index,
            len(module_list),
            module["module_id"],
            module["module_path"],
        )
        result = await agent.ainvoke(
            {
                "repo_id": repo_id,
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
                "iterations": 0,
            }
        )

        title = result.get("title", module["module_name"])  # Fallback to original name
        summary = result["summary"]
        deps = result["dependencies"]

        logger.info(
            "module_analysis_complete repo_id=%s index=%s/%s module_id=%s path=%s summary_chars=%s dependency_count=%s",
            repo_id,
            index,
            len(module_list),
            module["module_id"],
            module["module_path"],
            len(summary or ""),
            len(deps or []),
        )

        async with SessionLocal() as session:
            await session.execute(
                update(Module)
                .where(
                    Module.id
                    == uuid.UUID(module["module_id"])
                )
                .values(
                    name=title,
                    summary=summary,
                    dependencies=deps,
                )
            )

            await session.commit()

        summaries.append(
            {
                "name": title,
                "path": module["module_path"],
                "summary": summary,
                "dependencies": deps,
                "source_files": module.get("source_files", []),
            }
        )

    logger.info(
        "analyze_modules_complete repo_id=%s summarized_count=%s",
        repo_id,
        len(summaries),
    )

    return summaries
