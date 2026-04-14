"""
Project schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SubmitProjectRequest(BaseModel):
    project_name: Optional[str] = None
    github_url: Optional[str] = None
    github_urls: Optional[list[str]] = None

    @property
    def urls(self) -> list[str]:
        raw_urls: list[str] = []
        if self.github_url:
            raw_urls.append(self.github_url)
        raw_urls.extend(self.github_urls or [])
        return [item.strip() for item in raw_urls if item and item.strip()]

    @model_validator(mode="after")
    def validate_urls(self) -> "SubmitProjectRequest":
        if not self.urls:
            raise ValueError("Provide github_url or github_urls with at least one repository URL.")
        return self


class SubmittedRepository(BaseModel):
    repo_id: str
    github_url: str
    name: Optional[str] = None
    status: str
    commit_sha: Optional[str] = None


class SubmitProjectResponse(BaseModel):
    project_id: str
    name: str
    status: str
    message: str
    repositories: list[SubmittedRepository]
    total_repositories: int
    related_projects: Optional[list["ProjectSummary"]] = None  # Individual and combined projects


class ProjectSummary(BaseModel):
    project_id: str
    name: str
    status: str
    repository_count: int


class ProjectStatusResponse(BaseModel):
    project_id: str
    name: str
    status: str
    error_message: Optional[str] = None
    repository_count: int
    created_at: datetime
    updated_at: datetime
    repositories: list[SubmittedRepository] = Field(default_factory=list)
 