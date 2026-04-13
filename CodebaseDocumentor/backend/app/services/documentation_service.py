"""
Documentation service
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.documentation import Documentation
from app.schemas.documentation import DocumentationResponse
from app.schemas.generated_content import ProjectDocumentationOutput
from app.services import project_service
from app.utils.static_site import create_static_site, render_documentation_markdown


async def get_docs(db: AsyncSession, project_id: str) -> DocumentationResponse:
    project = await project_service.get_project(db, project_id)
    project_service.require_completed(project)

    result = await db.execute(select(Documentation).where(Documentation.project_id == project.id))
    docs = result.scalar_one()
    content = docs.content

    parsed_model = None
    markdown = None

    try:
        parsed_model = ProjectDocumentationOutput.parse_obj(json.loads(content))
        markdown = render_documentation_markdown(parsed_model, include_diagrams=False)
        parsed_content = parsed_model
    except Exception:
        parsed_content = content
        markdown = content if isinstance(content, str) else None

    url = create_static_site(parsed_content)

    return DocumentationResponse(
        project_id=project_id,
        url=url,
        created_at=docs.created_at,
        markdown=markdown,
        content=parsed_model.dict() if parsed_model else None,
    )
