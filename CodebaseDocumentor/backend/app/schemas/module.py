"""
Module schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class ModuleSummary(BaseModel):

    module_id: str

    name: str

    path: str

    language: Optional[str]

    summary: Optional[str]

    dependencies: Optional[List[str]]


class ModulesResponse(BaseModel):

    repo_id: str

    total_modules: int

    modules: List[ModuleSummary]