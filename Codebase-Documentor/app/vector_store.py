"""
Vector Store
-------------
Wraps langchain_postgres.PGVector so the rest of the codebase never
touches raw SQL or embedding logic directly.

PGVector internally:
  - Creates a 'langchain_pg_embedding' table with a vector(768) column
  - Builds an HNSW index automatically
  - Stores document metadata as JSONB

Each module is stored as one Document:
  page_content = full_content  (entire module source, up to 8192 tokens)
  metadata     = {
      "repo_id":      "...",   ← used for repo isolation in every search
      "module_id":    "...",
      "module_name":  "src.auth",
      "module_path":  "src/auth",
      "language":     "python",
  }

Repo isolation:
  Every similarity_search call passes filter={"repo_id": repo_id}
  PGVector translates this to a JSONB WHERE clause before ranking by distance.
  Repos never bleed into each other.

Async note:
  PGVector uses psycopg (sync). All calls run in a thread executor
  so they don't block the async event loop.
"""

import asyncio
from functools import lru_cache
from typing import List, Dict
from langchain_postgres import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import settings


# ── Embedding model (loaded once) ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load nomic-embed-text-v1.5 once and cache it.
    8192-token window means entire module source embeds in one pass.
    trust_remote_code=True is required by the nomic model.
    """
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
            "trust_remote_code": True,
        },
        encode_kwargs={"normalize_embeddings": True},
    )


# ── PGVector store (loaded once) ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_store() -> PGVector:
    """
    Create the PGVector store once.
    - collection_name becomes the table namespace inside langchain_pg_embedding
    - use_jsonb=True stores metadata as JSONB — required for metadata filtering
    - PGVector creates its own tables and HNSW index on first use
    """
    return PGVector(
        embeddings      = _get_embeddings(),
        collection_name = "module_embeddings",
        connection      = settings.PGVECTOR_URL,
        use_jsonb       = True,
    )


# ── Public interface ───────────────────────────────────────────────────────────

async def store_module(
    repo_id:      str,
    module_id:    str,
    module_name:  str,
    module_path:  str,
    language:     str,
    full_content: str,
) -> None:
    """
    Embed a module's full source and store it in PGVector.

    nomic prepends 'search_document:' internally via the embedding model
    for correct instruction-tuned behaviour.

    Runs the sync PGVector call in a thread so the event loop stays free.
    """
    doc = Document(
        page_content = full_content,
        metadata     = {
            "repo_id":     repo_id,
            "module_id":   module_id,
            "module_name": module_name,
            "module_path": module_path,
            "language":    language,
        },
    )

    store = _get_store()
    loop  = asyncio.get_event_loop()
    await loop.run_in_executor(None, store.add_documents, [doc])


async def search_modules(
    repo_id:  str,
    query:    str,
    k:        int = 5,
) -> List[Dict]:
    """
    Semantic similarity search over modules in a specific repo.

    Args:
        repo_id: Restricts search to this repo only.
        query:   Natural language question or module description.
        k:       Number of results to return.

    Returns:
        List of dicts: {module_name, module_path, language, full_content}
    """
    store = _get_store()
    loop  = asyncio.get_event_loop()

    # filter={"repo_id": repo_id} → PGVector adds a JSONB WHERE clause
    # before cosine distance ranking — repo isolation is guaranteed
    results = await loop.run_in_executor(
        None,
        lambda: store.similarity_search(
            query,
            k      = k,
            filter = {"repo_id": repo_id},
        ),
    )

    return [
        {
            "module_name":  doc.metadata.get("module_name", ""),
            "module_path":  doc.metadata.get("module_path", ""),
            "language":     doc.metadata.get("language", ""),
            "full_content": doc.page_content,
        }
        for doc in results
    ]