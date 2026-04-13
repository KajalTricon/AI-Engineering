"""
Project query service (RAG)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import UserFacingAIError, invoke_llm
from app.core.exceptions import service_unavailable
from app.core.settings import settings
from app.schemas.query import QueryResponse, QuerySource
from app.services import project_service
from app.vector.vector_store import search_modules


async def query_project(db: AsyncSession, project_id: str, question: str) -> QueryResponse:
    project = await project_service.get_project(db, project_id)
    project_service.require_completed(project)

    results = await search_modules(
        project_id=project_id,
        query=question,
        k=settings.PROJECT_QUERY_TOP_K,
    )

    if not results:
        return QueryResponse(answer="No indexed project context was found.", sources=[])

    context = "\n\n".join(
        (
            f"[{result['repository_name']}/{result['module_path']} chunk {result.get('chunk_index', 0) + 1}/{result.get('chunk_count', 1)}]\n"
            f"{result['full_content'][:1500]}"
        )
        for result in results
    )

    prompt = f"""
Answer the project question using only the retrieved project context.
This project may span multiple repositories that work together as microservices.
When relevant, connect evidence across repositories, but do not guess.
If the evidence is incomplete, clearly state what is missing.
Prefer concrete repository/module references in the answer.

Question: {question}

Retrieved project context:
{context}
"""

    try:
        answer = await invoke_llm(
            prompt,
            label="project_query",
            scope_id=project_id,
            model_tier="documentation",
        )
    except UserFacingAIError as exc:
        raise service_unavailable(str(exc)) from exc

    return QueryResponse(
        answer=answer,
        sources=[
            QuerySource(
                repository=result["repository_name"] or "unknown",
                module=result["module_name"],
                path=result["module_path"],
            )
            for result in results
        ],
    )
