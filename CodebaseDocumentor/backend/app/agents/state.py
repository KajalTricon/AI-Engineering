"""
LangGraph state
"""

from typing import List, TypedDict


class ModuleAnalysisState(TypedDict):
    project_id: str
    repository_id: str
    repository_name: str
    module_id: str
    module_name: str
    module_path: str
    language: str
    full_content: str
    source_files: List[str]
    retrieved_context: List[str]
    analysis: str
    iterations: int
    title: str
    summary: str
    dependencies: List[str]
    responsibilities: List[str]
    important_files: List[str]
