"""
Documentation Agent
--------------------
Called once after ALL modules have been analyzed.
Feeds every module summary to Gemini Pro and synthesizes full project docs.
"""

from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

# Pro for final synthesis — needs large context to reason across all summaries
_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.2,
)

_PROMPT = """\
You are generating complete developer documentation for a software project.

Project   : {project_name}
Repository: {github_url}
Modules   : {module_count}

Below are the AI-generated summaries for every module in the codebase:

{module_summaries}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate comprehensive project documentation in markdown using these sections:

# {project_name}

## Overview
What this project does and the problem it solves (3–5 sentences).

## Architecture
The big picture — how the system is structured and how modules relate.

## Module Guide
For each module: one sentence on its role and when a developer would look at it.

## Data Flow
Step-by-step: how a typical request/operation moves through the system.

## Setup & Development
Likely setup steps inferred from the modules (dependencies, env config, running the app).

## Key Concepts
3–5 design decisions or conventions a new developer must understand.

---

Write for developers who are new to this codebase but experienced with software.\
"""


async def generate_project_documentation(
    project_name:     str,
    github_url:       str,
    module_summaries: List[Dict[str, str]],   # [{name, path, summary}, ...]
) -> str:
    """
    Synthesize all module summaries into complete project documentation.

    Returns the full documentation as a markdown string.
    """
    summaries_block = "\n\n---\n\n".join(
        f"### `{m['name']}` ({m['path']})\n{m['summary']}"
        for m in module_summaries
    )

    # Respect Gemini Pro's context window for very large repos
    summaries_block = summaries_block[:20_000]

    prompt = _PROMPT.format(
        project_name     = project_name,
        github_url       = github_url,
        module_count     = len(module_summaries),
        module_summaries = summaries_block,
    )

    response = await _llm.ainvoke(prompt)
    return response.content