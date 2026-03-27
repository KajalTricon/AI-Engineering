"""
Embedding model loader
"""

from functools import lru_cache

from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
)

from app.core.settings import settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load nomic embedding model once.
    """

    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
            "trust_remote_code": True,
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )