"""
Application settings
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Environment configuration
    """

    DATABASE_URL: str

    PGVECTOR_URL: str

    GEMINI_API_KEY: str

    EMBEDDING_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"

    CLONE_BASE_DIR: str = "/tmp/repos"

    STATIC_DIR: str = "static"
    STATIC_URL_PREFIX: str = "http://localhost:8000/static"

    APP_TITLE: str = "Autonomous Codebase Documenter"
    APP_VERSION: str = "1.0.0"
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

import os

if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY

if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2

if settings.LANGCHAIN_PROJECT:
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    
    
print(settings.LANGCHAIN_API_KEY)
