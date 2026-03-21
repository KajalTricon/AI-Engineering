"""
Pipeline Service
-----------------
Full processing flow as a FastAPI BackgroundTask:

  1. Clone the repo (git clone --depth=1)
  2. Chunk into modules (one per directory, full_content = all files concatenated)
  3. For each module:
       a. Insert Module row in PostgreSQL (full_content, metadata)
       b. Call store_module() → PGVector embeds + stores with repo_id in metadata
  4. LangGraph analyzer agent on each module
       (retrieve_context uses PGVector search_modules filtered by repo_id)
  5. Doc agent synthesizes all summaries → project documentation
  6. Store Documentation row, mark repo completed
"""

import asyncio
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from .connection import AsyncSessionLocal
from .models import Repository, Module, Documentation
from .module_chunker import chunk_repository, ModuleChunk
from .vector_store import store_module, search_modules
from .analyzer_agent import build_analyzer_agent
from .doc_agent import generate_project_documentation


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _set_status(repo_id: str, status: str, error: str = None) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Repository)
            .where(Repository.id == uuid.UUID(repo_id))
            .values(status=status, error_message=error, updated_at=datetime.utcnow())
        )
        await session.commit()


async def _clone_repo(github_url: str, repo_id: str) -> str:
    clone_dir = str(Path(settings.CLONE_BASE_DIR) / repo_id)
    Path(settings.CLONE_BASE_DIR).mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth=1", github_url, clone_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {stderr.decode().strip()}")

    return clone_dir


# ── Step 3: Store modules in Postgres + PGVector ───────────────────────────────

async def _store_all_modules(
    repo_id:       str,
    module_chunks: List[ModuleChunk],
) -> List[Dict]:
    """
    For each ModuleChunk:
      - Insert a Module row in PostgreSQL (full_content, name, path, language)
      - Call store_module() which embeds full_content and stores the vector
        in PGVector with repo_id in metadata

    Returns list of dicts for the analyzer agent.
    """
    stored: List[Dict] = []

    async with AsyncSessionLocal() as session:
        for chunk in module_chunks:
            # Insert the Module row (no embedding column — PGVector owns that)
            module = Module(
                repository_id = uuid.UUID(repo_id),
                name          = chunk.name,
                path          = chunk.path,
                language      = chunk.language,
                full_content  = chunk.full_content,
            )
            session.add(module)
            await session.flush()    # get module.id before commit
            module_id = str(module.id)
            await session.commit()

        # Re-query to get all modules for this repo
        result  = await session.execute(
            select(Module).where(Module.repository_id == uuid.UUID(repo_id))
        )
        modules = result.scalars().all()

    # Embed and store in PGVector (outside the DB session — these are slow calls)
    for module in modules:
        await store_module(
            repo_id      = repo_id,
            module_id    = str(module.id),
            module_name  = module.name,
            module_path  = module.path,
            language     = module.language or "unknown",
            full_content = module.full_content,
        )

        stored.append({
            "module_id":    str(module.id),
            "module_name":  module.name,
            "module_path":  module.path,
            "language":     module.language or "unknown",
            "full_content": module.full_content,
        })

    return stored


# ── Step 4: Analyze each module with LangGraph agent ──────────────────────────

async def _analyze_all_modules(
    repo_id:        str,
    stored_modules: List[Dict],
) -> List[Dict]:
    """
    Run the LangGraph analyzer on each module sequentially.
    The agent uses PGVector search_modules() for cross-module context retrieval.
    Writes summary + dependencies back to the Module row after each run.
    """
    agent     = build_analyzer_agent()
    summaries: List[Dict] = []

    for mod in stored_modules:
        result = await agent.ainvoke({
            "repo_id":           repo_id,
            "module_id":         mod["module_id"],
            "module_name":       mod["module_name"],
            "module_path":       mod["module_path"],
            "language":          mod["language"],
            "full_content":      mod["full_content"],
            "retrieved_context": [],
            "analysis":          "",
            "summary":           "",
            "dependencies":      [],
            "iterations":        0,
        })

        summary      = result.get("summary", "")
        dependencies = result.get("dependencies", [])

        # Persist summary to PostgreSQL
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Module)
                .where(Module.id == uuid.UUID(mod["module_id"]))
                .values(summary=summary, dependencies=dependencies)
            )
            await session.commit()

        summaries.append({
            "name":    mod["module_name"],
            "path":    mod["module_path"],
            "summary": summary,
        })

    return summaries


# ── Main pipeline ──────────────────────────────────────────────────────────────

async def process_repository(repo_id: str, github_url: str) -> None:
    """Called by FastAPI BackgroundTasks"""
    clone_path = None

    try:
        await _set_status(repo_id, "processing")

        # 1. Clone
        clone_path = await _clone_repo(github_url, repo_id)

        # 2. Chunk
        module_chunks = chunk_repository(clone_path)
        if not module_chunks:
            raise RuntimeError("No supported source files found in this repository.")

        # 3. Store in Postgres + PGVector
        stored_modules = await _store_all_modules(repo_id, module_chunks)

        # 4. Analyze with LangGraph agent (RAG via PGVector)
        module_summaries = await _analyze_all_modules(repo_id, stored_modules)

        # 5. Synthesize full project documentation
        project_name = Path(clone_path).name
        docs_content = await generate_project_documentation(
            project_name     = project_name,
            github_url       = github_url,
            module_summaries = module_summaries,
        )

        # 6. Persist docs + mark completed
        async with AsyncSessionLocal() as session:
            session.add(Documentation(
                repository_id = uuid.UUID(repo_id),
                content       = docs_content,
            ))
            await session.commit()

        await _set_status(repo_id, "completed")

    except Exception as exc:
        await _set_status(repo_id, "failed", str(exc))
        raise

    finally:
        if clone_path:
            shutil.rmtree(clone_path, ignore_errors=True)


# ── RAG Q&A ────────────────────────────────────────────────────────────────────

async def query_repository(repo_id: str, question: str) -> Dict:
    """
    Answer a developer's question using RAG.

    PGVector finds the 5 most semantically relevant modules for this repo.
    Gemini Flash reads their full source and answers the question.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Retrieve relevant modules via PGVector (filtered by repo_id)
    results = await search_modules(repo_id=repo_id, query=question, k=5)

    if not results:
        return {"answer": "No modules found for this repository.", "sources": []}

    context = "\n\n---\n\n".join(
        f"[{r['module_name']} — {r['module_path']}]\n{r['full_content'][:1200]}"
        for r in results
    )

    llm = ChatGoogleGenerativeAI(
        model          = "gemini-2.5-flash",
        google_api_key = settings.GEMINI_API_KEY,
        temperature    = 0.1,
    )

    prompt = f"""\
Answer this question about the codebase using only the code shown below.
Reference specific module names, functions, and classes in your answer.

Question: {question}

Relevant Modules:
{context}

Answer:\
"""
    response = await llm.ainvoke(prompt)
    sources  = [{"module": r["module_name"], "path": r["module_path"]} for r in results]

    return {"answer": response.content, "sources": sources}