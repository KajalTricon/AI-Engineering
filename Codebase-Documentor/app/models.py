"""
Schema — 3 tables managed by SQLAlchemy.

repositories   → one row per submitted GitHub repo
modules        → one row per directory-level module
                 full_content stored as TEXT for the LLM to read
                 NO embedding column — PGVector owns that in its own table
documentation  → one row per repo, final synthesized markdown

Vector storage is handled entirely by langchain_postgres.PGVector.
It creates and manages a 'langchain_pg_embedding' table internally.
Each stored vector carries metadata: {repo_id, module_id, module_name, module_path, language}
Repo isolation is enforced by filtering on metadata["repo_id"] at search time.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_url    = Column(String(500), nullable=False)
    name          = Column(String(200))
    # pending → processing → completed | failed
    status        = Column(String(50), default="pending")
    error_message = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Module(Base):
    __tablename__ = "modules"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name          = Column(String(300), nullable=False)   # e.g. "src.auth"
    path          = Column(String(500), nullable=False)   # e.g. "src/auth"
    language      = Column(String(50))

    # Full concatenated source of the module — used by the LLM agent
    full_content  = Column(Text, nullable=False)

    # Filled by the LangGraph agent after analysis
    summary       = Column(Text)
    dependencies  = Column(JSON, default=list)

    created_at    = Column(DateTime, default=datetime.utcnow)


class Documentation(Base):
    __tablename__ = "documentation"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        unique=True,
    )
    content       = Column(Text)    # final markdown from doc agent
    created_at    = Column(DateTime, default=datetime.utcnow)