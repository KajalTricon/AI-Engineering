"""
LangGraph Module Analyzer Agent
---------------------------------
Graph:

    START
      │
      ▼
  retrieve_context   ← PGVector similarity_search filtered by repo_id
      │                finds 3 most related modules in the same repo
      ▼
  analyze_module     ← Gemini Flash: reads full_content + context
      │
      ▼
  generate_summary   ← Gemini Flash: formats into structured markdown
      │
      ▼ (conditional)
  quality ok or iterations >= 3?
      ├── yes → END
      └── no  → analyze_module  (refine with same context)
"""

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

from .state import ModuleAnalysisState
from .vector_store import search_modules
from config import settings


_llm = ChatGoogleGenerativeAI(
    model       = "gemini-2.5-flash",
    google_api_key = settings.GEMINI_API_KEY,
    temperature = 0.2,
)

# ── Prompts ────────────────────────────────────────────────────────────────────

_ANALYZE_PROMPT = """\
You are an expert software engineer analyzing a module in a codebase to write documentation.

Module   : {module_name}
Path     : {module_path}
Language : {language}

━━━ FULL SOURCE CODE OF THIS MODULE ━━━
{full_content}

━━━ RELATED MODULES FROM THE SAME REPO (for cross-reference) ━━━
{retrieved_context}

Analyze this module thoroughly:
1. What is the purpose and responsibility of this module?
2. What are the key functions, classes, or components and what does each do?
3. What data flows in and out?
4. Which other modules does it depend on, and how?
5. What patterns or design decisions are worth noting?

Be specific. Reference actual function/class names from the code.\
"""

_SUMMARY_PROMPT = """\
Using the analysis below, write a clean structured markdown summary for the `{module_name}` module.

{analysis}

Use exactly these sections:

# {module_name}

## Purpose
One or two sentences: what this module does.

## Key Components
Bullet list of the main functions/classes and what each one does.

## Dependencies
What other modules or libraries this module relies on.

## Data Flow
How data enters and exits this module.

## Notes
Patterns, caveats, or anything a new developer must know.

Keep it under 400 words. Be precise and developer-friendly.\
"""


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def retrieve_context(state: ModuleAnalysisState) -> dict:
    """
    Use PGVector similarity search to find the 3 most related modules
    in the same repo. Filter by repo_id ensures repo isolation.

    Query = module name + first 400 chars of its source (enough for semantics).
    """
    query   = f"{state['module_name']} {state['language']}\n{state['full_content'][:400]}"
    results = await search_modules(
        repo_id = state["repo_id"],
        query   = query,
        k       = 3,
    )

    # Exclude this module itself from context (in case it comes back)
    context = [
        f"[{r['module_name']} — {r['module_path']}]\n{r['full_content'][:800]}"
        for r in results
        if r["module_name"] != state["module_name"]
    ]

    return {"retrieved_context": context}


async def analyze_module(state: ModuleAnalysisState) -> dict:
    """Feed the full module source + cross-module context to Gemini for analysis."""
    context_block = (
        "\n\n---\n\n".join(state.get("retrieved_context", []))
        or "No related modules found yet."
    )

    prompt = _ANALYZE_PROMPT.format(
        module_name       = state["module_name"],
        module_path       = state["module_path"],
        language          = state["language"],
        full_content      = state["full_content"][:8000],
        retrieved_context = context_block[:3000],
    )

    response = await _llm.ainvoke(prompt)
    return {
        "analysis":   response.content,
        "iterations": state.get("iterations", 0) + 1,
    }


async def generate_summary(state: ModuleAnalysisState) -> dict:
    """Format the analysis into a structured markdown summary."""
    prompt = _SUMMARY_PROMPT.format(
        module_name = state["module_name"],
        analysis    = state["analysis"],
    )

    response = await _llm.ainvoke(prompt)
    summary  = response.content

    # Extract likely dependency references from the analysis text
    deps = [
        line.strip()
        for line in state["analysis"].splitlines()
        if ("import" in line.lower() or "depend" in line.lower())
        and len(line.strip()) < 120
    ][:10]

    return {"summary": summary, "dependencies": deps}


# ── Conditional edge ───────────────────────────────────────────────────────────

def _route_after_summary(state: ModuleAnalysisState) -> str:
    summary    = state.get("summary", "")
    iterations = state.get("iterations", 0)

    quality_ok = (
        "## Purpose"    in summary and
        "## Key"        in summary and
        len(summary)    > 200
    )
    return "done" if (quality_ok or iterations >= 3) else "refine"


# ── Build graph ────────────────────────────────────────────────────────────────

def build_analyzer_agent():
    """
    Compile and return the LangGraph module analyzer.
    No db_factory needed — vector search goes through PGVector (vector_store.py).
    """
    graph = StateGraph(ModuleAnalysisState)

    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("analyze_module",   analyze_module)
    graph.add_node("generate_summary", generate_summary)

    graph.add_edge(START,              "retrieve_context")
    graph.add_edge("retrieve_context", "analyze_module")
    graph.add_edge("analyze_module",   "generate_summary")

    graph.add_conditional_edges(
        "generate_summary",
        _route_after_summary,
        {"done": END, "refine": "analyze_module"},
    )

    return graph.compile()