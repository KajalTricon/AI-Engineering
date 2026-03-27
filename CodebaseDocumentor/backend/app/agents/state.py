"""
LangGraph state
"""

from typing import TypedDict, List


class ModuleAnalysisState(TypedDict):

    repo_id: str

    module_id: str

    module_name: str

    module_path: str

    language: str

    full_content: str

    source_files: List[str]

    retrieved_context: List[str]

    analysis: str

    iterations: int

    summary: str

    dependencies: List[str]
