"""
PGVector store wrapper
"""

import asyncio
from functools import lru_cache
from typing import Dict, List

from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.core.settings import settings
from app.vector.embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_store() -> PGVector:
    return PGVector(
        embeddings=get_embeddings(),
        collection_name="project_module_embeddings",
        connection=settings.PGVECTOR_URL,
        use_jsonb=True,
    )


def split_text(text: str) -> list[str]:
    chunk_size = settings.VECTOR_CHUNK_SIZE
    overlap = settings.VECTOR_CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text]

    sections = text.split("\n=== ")
    merged: list[str] = []
    current = ""

    for index, section in enumerate(sections):
        normalized = section if index == 0 else f"=== {section}"
        candidate = normalized if not current else f"{current}\n\n{normalized}"
        if current and len(candidate) > chunk_size:
            merged.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{normalized}" if tail else normalized
        else:
            current = candidate

    if current:
        merged.append(current)

    return merged


async def store_module(
    *,
    project_id: str,
    repo_id: str,
    repository_name: str,
    module_id: str,
    module_name: str,
    module_path: str,
    language: str,
    full_content: str,
) -> None:
    content_chunks = split_text(full_content)
    documents = [
        Document(
            page_content=chunk,
            metadata={
                "project_id": project_id,
                "repo_id": repo_id,
                "repository_name": repository_name,
                "module_id": module_id,
                "module_name": module_name,
                "module_path": module_path,
                "language": language,
                "chunk_index": index,
                "chunk_count": len(content_chunks),
            },
        )
        for index, chunk in enumerate(content_chunks)
    ]

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, get_store().add_documents, documents)


async def search_modules(
    *,
    project_id: str,
    query: str,
    k: int = 6,
    repo_id: str | None = None,
) -> List[Dict]:
    filters = {"project_id": project_id}
    if repo_id:
        filters["repo_id"] = repo_id

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        None,
        lambda: get_store().similarity_search(query, k=max(k * 3, 12), filter=filters),
    )

    seen: set[tuple[str, str, int]] = set()
    output: list[dict] = []

    for doc in results:
        key = (
            doc.metadata.get("repository_name", ""),
            doc.metadata.get("module_path", ""),
            int(doc.metadata.get("chunk_index", 0) or 0),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "repository_name": doc.metadata.get("repository_name"),
                "repo_id": doc.metadata.get("repo_id"),
                "module_name": doc.metadata.get("module_name"),
                "module_path": doc.metadata.get("module_path"),
                "language": doc.metadata.get("language"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "chunk_count": doc.metadata.get("chunk_count"),
                "full_content": doc.page_content,
            }
        )
        if len(output) >= k:
            break

    return output
