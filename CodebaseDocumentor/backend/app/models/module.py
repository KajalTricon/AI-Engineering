"""
Module model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Module(Base):
    """
    One row per directory-level module.
    """

    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    repository_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    repository_name = Column(String(200), nullable=True)
    name = Column(String(300), nullable=False)
    path = Column(String(500), nullable=False)
    language = Column(String(50), nullable=True)
    full_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    dependencies = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
