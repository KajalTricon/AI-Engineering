"""
Repository model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Repository(Base):
    """
    One row per submitted GitHub repository
    """

    __tablename__ = "repositories"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    github_url = Column(
        String(500),
        nullable=False,
    )

    normalized_url = Column(
        String(500),
        nullable=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=True,
    )

    commit_sha = Column(
        String(64),
        nullable=True,
        index=True,
    )

    status = Column(
        String(50),
        default="pending",
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
