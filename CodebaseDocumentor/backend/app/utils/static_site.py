"""
Generate static HTML from markdown
"""

import re
import uuid

import markdown

from app.core.settings import settings
from app.schemas.generated_content import ProjectDocumentationOutput


def create_static_site(content: str | ProjectDocumentationOutput) -> str:
    settings.static_path.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_name = f"site_{file_id}.html"
    file_path = settings.static_path / file_name

    if isinstance(content, ProjectDocumentationOutput):
        content = render_documentation_markdown(content)

    html = render_markdown(content)
    page = f"""
    <html>
    <body>
    {html}
    </body>
    </html>
    """

    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(page)

    return f"{settings.STATIC_URL_PREFIX}/{file_name}"


def render_documentation_markdown(document: ProjectDocumentationOutput, *, include_diagrams: bool = True) -> str:
    parts = [f"# {document.title}", document.overview]

    if include_diagrams:
        architecture_mermaid = normalize_mermaid(document.architecture.mermaid)
        flow_mermaid = normalize_mermaid(document.flow.mermaid)
        parts.extend(
            [
                "## Architecture",
                document.architecture.description,
                "```mermaid",
                architecture_mermaid,
                "```",
                "## Flow",
                document.flow.description,
                "```mermaid",
                flow_mermaid,
                "```",
            ]
        )
    else:
        parts.extend([
            "## Architecture",
            document.architecture.description,
            "## Flow",
            document.flow.description,
        ])

    if document.setup_notes:
        parts.append("## Setup Notes")
        parts.extend(f"- {note}" for note in document.setup_notes)

    if document.repositories:
        parts.append("## Repositories")
        for repository in document.repositories:
            parts.append(f"### {repository.name}")
            parts.append(f"`{repository.github_url}`")
            parts.append(repository.summary)
            if repository.key_modules:
                parts.append("Key modules:")
                parts.extend(f"- {item}" for item in repository.key_modules)
            if repository.depends_on:
                parts.append("Depends on:")
                parts.extend(f"- {item}" for item in repository.depends_on)

    if document.modules:
        parts.append("## Modules")
        for module in document.modules:
            parts.append(f"### {module.repository} / {module.name}")
            parts.append(f"`{module.path}`")
            parts.append(module.summary)
            if module.responsibilities:
                parts.append("Responsibilities:")
                parts.extend(f"- {item}" for item in module.responsibilities)
            if module.important_files:
                parts.append("Important files:")
                parts.extend(f"- `{item}`" for item in module.important_files)
            if module.dependencies:
                parts.append("Dependencies:")
                parts.extend(f"- {item}" for item in module.dependencies)

    if document.operational_notes:
        parts.append("## Operational Notes")
        parts.extend(f"- {note}" for note in document.operational_notes)

    return "\n\n".join(parts)


def render_markdown(content: str) -> str:
    mermaid_blocks: list[str] = []

    def replace_mermaid(match: re.Match[str]) -> str:
        mermaid_blocks.append(match.group(1).strip())
        return f"MERMAID_BLOCK_{len(mermaid_blocks) - 1}"

    content_without_mermaid = re.sub(
        r"```mermaid\s*(.*?)```",
        replace_mermaid,
        content,
        flags=re.DOTALL,
    )

    html = markdown.markdown(content_without_mermaid, extensions=["fenced_code", "tables"])

    for index, block in enumerate(mermaid_blocks):
        html = html.replace(
            f"<p>MERMAID_BLOCK_{index}</p>",
            f'<pre class="mermaid">{block}</pre>',
        )

    return (
        html
        + """
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({ startOnLoad: true });
</script>
"""
    )


def normalize_mermaid(mermaid: str) -> str:
    stripped = mermaid.strip().replace("```mermaid", "").replace("```", "").strip()

    if not stripped:
        return 'flowchart TD\nA["Diagram unavailable"]'

    if not stripped.startswith("flowchart TD"):
        if stripped.startswith("graph TD"):
            stripped = stripped.replace("graph TD", "flowchart TD", 1)
        else:
            stripped = "flowchart TD\n" + stripped

    return stripped
