from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SubmitRepoRequest(BaseModel):
    github_url: str


class QueryRequest(BaseModel):
    question: str


class SubmitRepoResponse(BaseModel):
    repo_id: str
    status:  str
    message: str


class RepoStatusResponse(BaseModel):
    repo_id:       str
    github_url:    str
    name:          Optional[str]
    status:        str
    error_message: Optional[str]
    created_at:    datetime
    updated_at:    datetime


class ModuleSummary(BaseModel):
    module_id:    str
    name:         str
    path:         str
    language:     Optional[str]
    summary:      Optional[str]
    dependencies: Optional[List[str]]


class ModulesResponse(BaseModel):
    repo_id:       str
    total_modules: int
    modules:       List[ModuleSummary]


class DocumentationResponse(BaseModel):
    repo_id: str
    url: str
    created_at: datetime


class QuerySource(BaseModel):
    module: str
    path:   str


class QueryResponse(BaseModel):
    answer:  str
    sources: List[QuerySource]