"""
Module analyzer agent
"""

from langgraph.graph import END, START, StateGraph

from app.agents.state import ModuleAnalysisState
from app.core.ai import generate_structured_output, invoke_llm
from app.schemas.generated_content import ModuleSummaryOutput
from app.vector.vector_store import search_modules


async def retrieve_context(state: ModuleAnalysisState):
    query = " ".join(
        [
            state["repository_name"],
            state["module_name"],
            state["module_path"],
            *state["source_files"][:6],
        ]
    )
    results = await search_modules(
        project_id=state["project_id"],
        query=query,
        k=6,
    )

    context = [
        (
            f"[{result['repository_name']}/{result['module_path']} "
            f"chunk {result.get('chunk_index', 0) + 1}/{result.get('chunk_count', 1)}]\n"
            f"{result['full_content'][:900]}"
        )
        for result in results
    ]

    return {"retrieved_context": context}


def build_module_excerpt(full_content: str) -> str:
    if len(full_content) <= 5000:
        return full_content

    head = full_content[:1800]
    middle_start = max(0, (len(full_content) // 2) - 700)
    middle = full_content[middle_start:middle_start + 1400]
    tail = full_content[-1800:]
    return "\n\n--- MIDDLE SAMPLE ---\n\n".join([head, middle, tail])


async def analyze_module(state: ModuleAnalysisState):
    prompt = f"""
You are analyzing one code module inside a larger software project that may contain multiple repositories.
Stay grounded in the supplied code and context only.
Do not invent service names, APIs, data stores, dependencies, or runtime flows.

Project scope id: {state['project_id']}
Repository: {state['repository_name']}
Module name: {state['module_name']}
Module path: {state['module_path']}
Primary language: {state['language']}
Files in module: {', '.join(state['source_files'][:20])}

Representative code:
{build_module_excerpt(state['full_content'])}

Related project context:
{chr(10).join(state['retrieved_context'])}

Write factual analysis covering:
- module purpose
- key responsibilities
- major files or entry points
- internal integrations inside this repo or other repos if clearly evidenced
- external libraries or infrastructure only when explicit in the code
- visible risks, TODOs, or gaps
"""

    analysis = await invoke_llm(
        prompt,
        label="module_analysis",
        scope_id=state["project_id"],
        model_tier="primary",
    )

    return {
        "analysis": analysis,
        "iterations": state["iterations"] + 1,
    }


async def generate_summary(state: ModuleAnalysisState):
    prompt = f"""
Convert the grounded analysis into concise structured output.
Only include details supported by the analysis.
Prefer repository-aware dependency names when possible.
Keep the summary short enough to be reused later in project-level synthesis.

Repository: {state['repository_name']}
Module name: {state['module_name']}
Module path: {state['module_path']}
Files: {', '.join(state['source_files'][:20])}

Analysis:
{state['analysis']}
"""

    result = await generate_structured_output(
        prompt=prompt,
        schema=ModuleSummaryOutput,
        label="module_summary",
        scope_id=state["project_id"],
        model_tier="primary",
    )

    cleaned_dependencies: list[str] = []
    for dependency in result.dependencies[:10]:
        candidate = dependency.strip()
        if not candidate or candidate == ".":
            continue
        cleaned_dependencies.append(candidate)

    return {
        "title": result.title,
        "summary": result.summary,
        "dependencies": list(dict.fromkeys(cleaned_dependencies)),
        "responsibilities": result.responsibilities[:6],
        "important_files": result.important_files[:8],
    }


def route_after_summary(_: ModuleAnalysisState):
    return "done"


def build_analyzer_agent():
    graph = StateGraph(ModuleAnalysisState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("analyze_module", analyze_module)
    graph.add_node("generate_summary", generate_summary)
    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "analyze_module")
    graph.add_edge("analyze_module", "generate_summary")
    graph.add_conditional_edges(
        "generate_summary",
        route_after_summary,
        {"done": END},
    )
    return graph.compile()
