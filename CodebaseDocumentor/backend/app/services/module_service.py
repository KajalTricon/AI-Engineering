"""
Module processing
"""

import uuid
from typing import Iterable

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models.module import Module

from app.vector.vector_store import store_module
from app.agents.analyzer_agent import build_analyzer_agent


async def store_modules(
    repo_id: str,
    chunks,
) -> list[dict]:
    repository_id = uuid.UUID(repo_id)
    stored_modules: list[dict] = []

    async with SessionLocal() as session:
        for chunk in chunks:
            clean_content = chunk.full_content.replace("\x00", "")
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

    for module in stored_modules:
        await store_module(
            repo_id=repo_id,
            module_id=module["module_id"],
            module_name=module["module_name"],
            module_path=module["module_path"],
            language=module["language"] or "unknown",
            full_content=module["full_content"],
        )

    return stored_modules


async def analyze_modules(
    repo_id: str,
    modules: Iterable[dict],
) -> list[dict]:
    agent = build_analyzer_agent()
    summaries = []

    for module in modules:
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
                "summary": "",
                "dependencies": [],
                "iterations": 0,
            }
        )

        summary = result["summary"]
        deps = result["dependencies"]

        async with SessionLocal() as session:
            await session.execute(
                update(Module)
                .where(
                    Module.id
                    == uuid.UUID(module["module_id"])
                )
                .values(
                    summary=summary,
                    dependencies=deps,
                )
            )

            await session.commit()

        summaries.append(
            {
                "name": module["module_name"],
                "path": module["module_path"],
                "summary": summary,
                "dependencies": deps,
                "source_files": module.get("source_files", []),
            }
        )

    return summaries
