"""
Application settings
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Environment configuration.
    """

    DATABASE_URL: str
    PGVECTOR_URL: str
    GROQ_API_KEY: str

    EMBEDDING_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"
    GROQ_MODEL_PRIMARY: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_MODEL_DOCUMENTATION: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_RETRIES: int = 6
    GROQ_PRIMARY_MIN_INTERVAL_SECONDS: float = 2.0
    GROQ_DOCUMENTATION_MIN_INTERVAL_SECONDS: float = 4.0
    PROJECT_QUERY_TOP_K: int = 5
    VECTOR_CHUNK_SIZE: int = 5000
    VECTOR_CHUNK_OVERLAP: int = 500

    CLONE_BASE_DIR: str = "/tmp/repos"
    STATIC_DIR: str = "static"
    STATIC_URL_PREFIX: str = "http://localhost:8000/static"

    APP_TITLE: str = "Autonomous Codebase Documenter"
    APP_VERSION: str = "2.0.0"
    ENABLE_LLM_LOGS: bool = True

    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_TRACING_V2: str | None = None
    LANGCHAIN_PROJECT: str | None = None

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def static_path(self) -> Path:
        return self.project_root / self.STATIC_DIR


settings = Settings()

if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY

if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2

if settings.LANGCHAIN_PROJECT:
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
