import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import get_db
from .models import Repository, Module, Documentation
from .pipeline import process_repository, query_repository
from .schemas import (
    SubmitRepoRequest, SubmitRepoResponse,
    RepoStatusResponse,
    ModulesResponse, ModuleSummary,
    DocumentationResponse,
    QueryRequest, QueryResponse, QuerySource,
)
from app.website_generator import create_static_site

router = APIRouter(prefix="/api/v1")


# ── 1. Submit repository ───────────────────────────────────────────────────────

@router.post("/repositories", response_model=SubmitRepoResponse, status_code=202)
async def submit_repository(
    body:             SubmitRepoRequest,
    background_tasks: BackgroundTasks,
    db:               AsyncSession = Depends(get_db),
):
    """Submit a GitHub URL. Processing starts immediately in the background."""
    name = body.github_url.rstrip("/").split("/")[-1]

    repo = Repository(github_url=body.github_url, name=name, status="pending")
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    background_tasks.add_task(process_repository, str(repo.id), body.github_url)

    return SubmitRepoResponse(
        repo_id = str(repo.id),
        status  = "pending",
        message = "Submitted. Poll GET /api/v1/repositories/{repo_id} for status.",
    )


# ── 2. Repository status ───────────────────────────────────────────────────────

@router.get("/repositories/{repo_id}", response_model=RepoStatusResponse)
async def get_status(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Poll the processing status of a submitted repository."""
    repo = await _get_repo_or_404(db, repo_id)
    return RepoStatusResponse(
        repo_id       = str(repo.id),
        github_url    = repo.github_url,
        name          = repo.name,
        status        = repo.status,
        error_message = repo.error_message,
        created_at    = repo.created_at,
        updated_at    = repo.updated_at,
    )


# ── 3. List modules + summaries ────────────────────────────────────────────────

@router.get("/repositories/{repo_id}/modules", response_model=ModulesResponse)
async def get_modules(repo_id: str, db: AsyncSession = Depends(get_db)):
    """
    List all analyzed modules and their summaries.
    Summaries are populated progressively as the agent works through each module.
    """
    await _get_repo_or_404(db, repo_id)

    result  = await db.execute(
        select(Module).where(Module.repository_id == uuid.UUID(repo_id))
    )
    modules = result.scalars().all()

    return ModulesResponse(
        repo_id       = repo_id,
        total_modules = len(modules),
        modules       = [
            ModuleSummary(
                module_id    = str(m.id),
                name         = m.name,
                path         = m.path,
                language     = m.language,
                summary      = m.summary,
                dependencies = m.dependencies or [],
            )
            for m in modules
        ],
    )


# ── 4. Final documentation ─────────────────────────────────────────────────────

@router.get("/repositories/{repo_id}/documentation", response_model=DocumentationResponse)
async def get_documentation(repo_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the synthesized project documentation (markdown).
    Only available once status = 'completed'.
    """
    repo = await _get_repo_or_404(db, repo_id)

    if repo.status != "completed":
        raise HTTPException(
            status_code = 202,
            detail      = f"Not ready yet. Current status: '{repo.status}'.",
        )

    result = await db.execute(
        select(Documentation).where(Documentation.repository_id == uuid.UUID(repo_id))
    )
    docs = result.scalar_one_or_none()
    if not docs:
        raise HTTPException(status_code=404, detail="Documentation record not found.")
    site_url = create_static_site(docs.content)

    return DocumentationResponse(
        repo_id    = repo_id,
        url = site_url,
        created_at = docs.created_at,
    )


# ── 5. RAG Q&A ─────────────────────────────────────────────────────────────────

@router.post("/repositories/{repo_id}/query", response_model=QueryResponse)
async def query_repo(
    repo_id: str,
    body:    QueryRequest,
    db:      AsyncSession = Depends(get_db),
):
    """
    Ask a natural language question about the codebase.
    pgvector finds the most relevant modules; Gemini answers from actual code.

    Works once at least some modules are embedded (status = processing or completed).
    """
    repo = await _get_repo_or_404(db, repo_id)
    if repo.status == "pending":
        raise HTTPException(
            status_code = 400,
            detail      = "Repository has not started processing yet.",
        )

    result = await query_repository(repo_id, body.question)

    return QueryResponse(
        answer  = result["answer"],
        sources = [QuerySource(**s) for s in result["sources"]],
    )


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _get_repo_or_404(db: AsyncSession, repo_id: str) -> Repository:
    try:
        uid = uuid.UUID(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo_id format.")

    result = await db.execute(select(Repository).where(Repository.id == uid))
    repo   = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo