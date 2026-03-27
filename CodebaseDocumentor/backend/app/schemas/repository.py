"""
Repository schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubmitRepoRequest(BaseModel):
    """
    Request to submit a GitHub repo
    """

    github_url: str


class SubmitRepoResponse(BaseModel):
    repo_id: str
    status: str
    message: str
    reused: bool = False
    commit_sha: Optional[str] = None


class RepoStatusResponse(BaseModel):

    repo_id: str
    github_url: str

    name: Optional[str]
    normalized_url: Optional[str]
    commit_sha: Optional[str]

    status: str

    error_message: Optional[str]

    created_at: datetime
    updated_at: datetime
