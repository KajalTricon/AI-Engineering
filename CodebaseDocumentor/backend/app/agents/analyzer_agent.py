"""
Module analyzer agent
"""

from langgraph.graph import StateGraph, START, END

from app.agents.state import ModuleAnalysisState
from app.core.ai import generate_structured_output, invoke_llm
from app.schemas.generated_content import ModuleSummaryOutput
from app.vector.vector_store import search_modules


# ----------------------------------------
# retrieve context
# ----------------------------------------


async def retrieve_context(
    state: ModuleAnalysisState,
):
    query = " ".join(
        [
            state["module_name"],
            state["module_path"],
            *state["source_files"][:8],
        ]
    )
    results = await search_modules(
        repo_id=state["repo_id"],
        query=query,
        k=6,
    )

    ctx = [
        f"[{r['module_path']} chunk {r.get('chunk_index', 0)}/{r.get('chunk_count', 1)}]\n{r['full_content'][:1200]}"
        for r in results
    ]

    return {
        "retrieved_context": ctx,
    }


def build_module_excerpt(full_content: str) -> str:
    if len(full_content) <= 7000:
        return full_content

    head = full_content[:2500]
    middle_start = max(0, (len(full_content) // 2) - 1000)
    middle = full_content[middle_start:middle_start + 2000]
    tail = full_content[-2500:]

    return "\n\n--- MIDDLE SAMPLE ---\n\n".join([head, middle, tail])


# ----------------------------------------
# analyze
# ----------------------------------------
from langsmith import traceable

@traceable(name="module_analysis")
async def analyze_module(
    state: ModuleAnalysisState,
):
    prompt = f"""
You are analyzing one module from a software repository.
Produce grounded notes only from the supplied code and retrieved context.
Do not invent files, APIs, flows, or dependencies.

Module name: {state["module_name"]}
Module path: {state["module_path"]}
Primary language: {state["language"]}
Files in module: {", ".join(state["source_files"][:20])}

Representative code:
{build_module_excerpt(state["full_content"])}

Related repository context:
{chr(10).join(state["retrieved_context"])}

Write a detailed factual analysis of:
- the module purpose
- major responsibilities
- key files and entry points
- external dependencies and internal integrations
- risks, gaps, or TODOs visible from the code
"""

    res = await invoke_llm(
        prompt,
        label="module_analysis",
        repo_id=state["repo_id"],
    )

    return {
        "analysis": res,
        "iterations": state["iterations"] + 1,
    }


# ----------------------------------------
# summary
# ----------------------------------------

@traceable(name="summary_generation")
async def generate_summary(
    state: ModuleAnalysisState,
):
    prompt = f"""
Convert the module analysis into structured output.
Keep it concise, accurate, and grounded in the supplied analysis.
If information is not supported by the analysis, omit it.

IMPORTANT for the 'title' field:
- Generate a clear, descriptive title based on the module's PRIMARY purpose
- Use 2-4 words that describe what this module does (e.g., "API Routes", "Database Models", "User Authentication", "Core Utilities")
- DO NOT use the module path or technical identifiers
- Make it human-readable and meaningful

Module name: {state["module_name"]}
Module path: {state["module_path"]}
Files: {", ".join(state["source_files"][:20])}

Analysis:
{state["analysis"]}
"""

    res = await generate_structured_output(
        prompt=prompt,
        schema=ModuleSummaryOutput,
        label="module_summary",
        repo_id=state["repo_id"],
    )
    # Filter out dots and clean up dependencies
    cleaned_dependencies = []
    for dep in res.dependencies[:10]:
        if dep == ".":
            # Replace dot with parent directory name from module path
            parent = state["module_path"].split("/")[0] if "/" in state["module_path"] else state["module_name"].split(".")[0]
            if parent and parent != ".":
                cleaned_dependencies.append(parent)
        elif dep.strip():
            cleaned_dependencies.append(dep)

    return {
        "title": res.title,
        "summary": res.summary,
        "dependencies": list(dict.fromkeys(cleaned_dependencies)),  # Remove duplicates while preserving order
    }


# ----------------------------------------
# router
# ----------------------------------------


def route_after_summary(
    state: ModuleAnalysisState,
):
    return "done"


# ----------------------------------------
# build graph
# ----------------------------------------


def build_analyzer_agent():

    graph = StateGraph(ModuleAnalysisState)

    graph.add_node(
        "retrieve_context",
        retrieve_context,
    )

    graph.add_node(
        "analyze_module",
        analyze_module,
    )

    graph.add_node(
        "generate_summary",
        generate_summary,
    )

    graph.add_edge(
        START,
        "retrieve_context",
    )

    graph.add_edge(
        "retrieve_context",
        "analyze_module",
    )

    graph.add_edge(
        "analyze_module",
        "generate_summary",
    )

    graph.add_conditional_edges(
        "generate_summary",
        route_after_summary,
        {
            "done": END,
            "refine": "analyze_module",
        },
    )

    return graph.compile()
