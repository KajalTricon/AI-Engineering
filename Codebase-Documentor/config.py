from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SQLAlchemy (async) — uses asyncpg driver
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/codebase_docs"

    # langchain-postgres PGVector — uses psycopg (v3) driver
    # Same database, different driver prefix
    PGVECTOR_URL: str = "postgresql+psycopg://postgres:postgres@localhost/codebase_docs"
    GEMINI_API_KEY: str

    # nomic-embed-text-v1.5 — 8192 token window, 768-dim vectors
    EMBEDDING_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"

    CLONE_BASE_DIR: str = "/tmp/repos"

    class Config:
        env_file = ".env"


settings = Settings()