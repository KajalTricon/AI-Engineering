from typing import TypedDict, List


class ModuleAnalysisState(TypedDict):
    """
    State flowing through the LangGraph module analyzer agent.

    Set before invoking the agent:
        repo_id           UUID of the repository
        module_id         UUID of the module row (already stored in DB)
        module_name       e.g. "src.auth"
        module_path       e.g. "src/auth"
        language          dominant language
        full_content      entire concatenated source of this module

    Populated by agent nodes:
        retrieved_context full_content snippets from semantically similar
                          modules in the SAME repo (from pgvector search)
        analysis          intermediate LLM reasoning pass
        iterations        loop counter (max 3)

    Output:
        summary           final structured markdown summary
        dependencies      list of other module names referenced in the code
    """

    # ── inputs ─────────────────────────────────────────────────────────────
    repo_id:           str
    module_id:         str
    module_name:       str
    module_path:       str
    language:          str
    full_content:      str          # entire module source code

    # ── working ────────────────────────────────────────────────────────────
    retrieved_context: List[str]    # related module snippets from pgvector
    analysis:          str
    iterations:        int

    # ── output ─────────────────────────────────────────────────────────────
    summary:           str
    dependencies:      List[str]