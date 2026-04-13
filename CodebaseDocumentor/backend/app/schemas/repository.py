"""
Repository schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RepoStatusResponse(BaseModel):
    repo_id: str
    project_id: Optional[str]
    github_url: str
    name: Optional[str]
    normalized_url: Optional[str]
    commit_sha: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
