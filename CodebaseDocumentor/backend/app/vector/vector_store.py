"""
PGVector store wrapper
"""

import asyncio
from functools import lru_cache
from typing import List, Dict

from langchain_postgres import PGVector
from langchain_core.documents import Document

from app.core.settings import settings
from app.vector.embeddings import get_embeddings


# ----------------------------
# store instance
# ----------------------------


@lru_cache(maxsize=1)
def get_store() -> PGVector:
    """
    Create PGVector store once
    """

    return PGVector(
        embeddings=get_embeddings(),
        collection_name="module_embeddings",
        connection=settings.PGVECTOR_URL,
        use_jsonb=True,
    )


def split_text(
    text: str,
    chunk_size: int = 3500,
    overlap: int = 400,
) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks


# ----------------------------
# store module
# ----------------------------


async def store_module(
    repo_id: str,
    module_id: str,
    module_name: str,
    module_path: str,
    language: str,
    full_content: str,
):
    """
    Embed + store the full module as multiple overlapping chunks.
    """
    content_chunks = split_text(full_content)
    documents = [
        Document(
            page_content=chunk,
            metadata={
                "repo_id": repo_id,
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

    store = get_store()

    loop = asyncio.get_running_loop()

    await loop.run_in_executor(
        None,
        store.add_documents,
        documents,
    )


# ----------------------------
# search
# ----------------------------


async def search_modules(
    repo_id: str,
    query: str,
    k: int = 5,
) -> List[Dict]:

    store = get_store()

    loop = asyncio.get_running_loop()

    results = await loop.run_in_executor(
        None,
        lambda: store.similarity_search(
            query,
            k=k,
            filter={
                "repo_id": repo_id,
            },
        ),
    )

    out = []

    for doc in results:

        out.append(
            {
                "module_name": doc.metadata.get(
                    "module_name",
                ),
                "module_path": doc.metadata.get(
                    "module_path",
                ),
                "language": doc.metadata.get(
                    "language",
                ),
                "chunk_index": doc.metadata.get(
                    "chunk_index",
                ),
                "chunk_count": doc.metadata.get(
                    "chunk_count",
                ),
                "full_content": doc.page_content,
            }
        )

    return out
