"""
Embedder
--------
Uses nomic-embed-text-v1.5 (8192-token window, 768-dim vectors).
Runs locally via sentence-transformers — no API key needed.

The model is loaded once (lru_cache) and all calls run in a thread
executor so the sync model never blocks the async event loop.

nomic requires:
  - trust_remote_code=True
  - input text prefixed with "search_document: " for documents
    and "search_query: " for queries (improves retrieval quality)
"""

import asyncio
from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from config import settings


@lru_cache(maxsize=1)
def _load_model() -> HuggingFaceEmbeddings:
    """Load the nomic model once and cache it for the lifetime of the process."""
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
            "trust_remote_code": True,   # required by nomic-embed-text-v1.5
        },
        encode_kwargs={"normalize_embeddings": True},
    )


async def embed_module(content: str) -> List[float]:
    """
    Embed an entire module's source code.
    Prefixed with 'search_document:' as required by nomic for document embedding.
    """
    model = _load_model()
    text  = f"search_document: {content}"
    loop  = asyncio.get_event_loop()
    # embed_documents returns List[List[float]], take first
    result = await loop.run_in_executor(None, model.embed_documents, [text])
    return result[0]


async def embed_query(question: str) -> List[float]:
    """
    Embed a user's search query.
    Prefixed with 'search_query:' as required by nomic for query embedding.
    """
    model = _load_model()
    text  = f"search_query: {question}"
    loop  = asyncio.get_event_loop()
    return await loop.run_in_executor(None, model.embed_query, text)


def to_pg_vector_str(embedding: List[float]) -> str:
    """
    Convert a Python float list to pgvector literal format.
    e.g. [0.1, 0.2] → '[0.1,0.2]'

    Used in raw SQL:  CAST(:vec AS vector)
    """
    return f"[{','.join(str(v) for v in embedding)}]"