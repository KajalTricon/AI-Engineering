"""
Repository schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class SubmitRepoRequest(BaseModel):
    """
    Request to submit one or more GitHub repos
    """

    github_url: Optional[str] = None
    github_urls: Optional[list[str]] = None

    @property
    def urls(self) -> list[str]:
        raw_urls: list[str] = []

        if self.github_url:
            raw_urls.append(self.github_url)

        raw_urls.extend(self.github_urls or [])

        return [
            github_url.strip()
            for github_url in raw_urls
            if github_url and github_url.strip()
        ]

    @model_validator(mode="after")
    def validate_urls(self) -> "SubmitRepoRequest":
        if not self.urls:
            raise ValueError("Provide github_url or github_urls with at least one repository URL.")

        return self


class SubmittedRepository(BaseModel):
    repo_id: str
    github_url: str
    status: str
    message: str
    reused: bool = False
    commit_sha: Optional[str] = None


class SubmitRepoResponse(BaseModel):
    repositories: list[SubmittedRepository]
    total_submitted: int
    total_reused: int
    repo_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    reused: Optional[bool] = None
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
