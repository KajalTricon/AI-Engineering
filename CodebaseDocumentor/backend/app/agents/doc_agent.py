"""
Documentation agent
"""

from typing import List, Dict

from app.core.ai import generate_structured_output
from app.schemas.generated_content import ProjectDocumentationOutput


async def generate_project_documentation(
    project_name: str,
    github_url: str,
    module_summaries: List[Dict],
    repo_id: str,
) -> ProjectDocumentationOutput:

    block = "\n\n".join(
        "\n".join(
            [
                f"Module: {m['name']}",
                f"Path: {m['path']}",
                f"Summary: {m['summary']}",
                f"Dependencies: {', '.join(m.get('dependencies', []))}",
                f"Files: {', '.join(m.get('source_files', [])[:12])}",
            ]
        )
        for m in module_summaries
    )

    prompt = f"""
Create structured project documentation for this repository.
Use only the information provided below.
If module name is coming as "." then Generate a clear, descriptive title based on the module's PRIMARY purpose.
Do not invent frameworks, libraries, databases, or app names that are not directly supported by the module summaries below.
If evidence is limited, say so briefly instead of guessing.
Include Mermaid diagrams that are syntactically valid and conservative.
Use only `flowchart TD` diagrams.
Use simple node ids like A, B, C.
Use quoted labels inside brackets, for example: A["API Router"].
Do not use parentheses, curly braces, HTML, or markdown fences inside Mermaid labels.
Architecture diagram should show only components clearly supported by the module summaries.
Flow diagram should show the actual processing flow of this repository only if supported by the summaries. Otherwise provide a minimal high-level flow based on the available evidence.
Do not wrap Mermaid in markdown fences.

Project: {project_name}

Repo: {github_url}

Modules:
{block}
"""

    return await generate_structured_output(
        prompt=prompt,
        schema=ProjectDocumentationOutput,
        label="project_documentation",
        repo_id=repo_id,
    )
