"""
Query service (RAG)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import get_llm
from app.schemas.query import (
    QueryResponse,
    QuerySource,
)
from app.services import repository_service
from app.vector.vector_store import search_modules


async def query_repo(
    db: AsyncSession,
    repo_id: str,
    question: str,
) -> QueryResponse:
    repo = await repository_service.get_repository(db, repo_id)
    repository_service.require_completed(repo)

    results = await search_modules(
        repo_id=repo_id,
        query=question,
        k=5,
    )

    if not results:
        return QueryResponse(
            answer="No data",
            sources=[],
        )

    context = "\n\n".join(
        f"[{r['module_path']} chunk {r.get('chunk_index', 0)}/{r.get('chunk_count', 1)}]\n{r['full_content'][:1400]}"
        for r in results
    )

    prompt = f"""
Answer the repository question using only the retrieved repository context.
If the answer is incomplete, say what is missing instead of guessing.
Prefer concrete file/module references when possible.

Question: {question}

Retrieved context:
{context}
"""

    res = await get_llm().ainvoke(prompt)

    return QueryResponse(
        answer=res.content,
        sources=[
            QuerySource(
                module=r["module_name"],
                path=r["module_path"],
            )
            for r in results
        ],
    )
