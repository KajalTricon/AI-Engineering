"""
Project documentation agent
"""

from typing import Dict, List

from langchain_core.pydantic_v1 import BaseModel, Field

from app.core.ai import generate_structured_output
from app.schemas.generated_content import DiagramSection, ProjectDocumentationOutput


class ProjectTopLevelOutput(BaseModel):
    title: str
    overview: str
    architecture: DiagramSection
    flow: DiagramSection
    setup_notes: list[str] = Field(default_factory=list)
    operational_notes: list[str] = Field(default_factory=list)


def _compact(text: str, limit: int = 280) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


async def generate_project_documentation(
    *,
    project_name: str,
    repositories: List[Dict],
    module_summaries: List[Dict],
    project_id: str,
) -> ProjectDocumentationOutput:
    repository_block = "\n\n".join(
        "\n".join(
            [
                f"Repository: {repo['name']}",
                f"GitHub URL: {repo['github_url']}",
                f"Summary: {_compact(repo['summary'], 320)}",
                f"Key modules: {', '.join(repo.get('key_modules', [])[:8])}",
                f"Depends on: {', '.join(repo.get('depends_on', [])[:8]) or 'None clearly evidenced'}",
            ]
        )
        for repo in repositories
    )

    module_block = "\n".join(
        f"- {item['repository']}::{item['path']} -> {_compact(item['summary'])} | deps: {', '.join(item.get('dependencies', [])[:5]) or 'none'}"
        for item in module_summaries[:60]
    )

    prompt = f"""
Create top-level documentation for a software project that may contain one repository or multiple microservice repositories.
Use only the supplied repository and module summaries.
Do not invent infrastructure, protocols, databases, or service calls.
If evidence is weak, say so briefly and keep the diagrams conservative.

Return:
- a strong project title
- a short overview
- an overall architecture diagram for the whole project
- an end-to-end flow diagram for the project
- setup notes
- operational notes

Mermaid rules:
- use only `flowchart TD`
- use quoted labels in square brackets, like A["Gateway"]
- do not include markdown fences
- keep diagrams simple and syntactically valid
- for multi-repo projects, represent services and major interactions
- for single-repo projects, represent major modules/components

Project name: {project_name}
Repository count: {len(repositories)}

Repository summaries:
{repository_block}

Representative module summaries:
{module_block}
"""

    top_level = await generate_structured_output(
        prompt=prompt,
        schema=ProjectTopLevelOutput,
        label="project_documentation",
        scope_id=project_id,
        model_tier="documentation",
    )

    return ProjectDocumentationOutput(
        title=top_level.title,
        overview=top_level.overview,
        architecture=DiagramSection(**top_level.architecture.dict()),
        flow=DiagramSection(**top_level.flow.dict()),
        setup_notes=top_level.setup_notes,
        repositories=repositories,
        modules=module_summaries,
        operational_notes=top_level.operational_notes,
    )
