"""
Shared AI client helpers.
"""

from functools import lru_cache
from typing import Any, TypeVar

from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.pydantic_v1 import BaseModel

from app.core.logging import get_logger
from app.core.settings import settings


ModelT = TypeVar("ModelT", bound=BaseModel)
logger = get_logger("codebase_documentor.llm")
_CALL_COUNTER = 0
_QUOTA_ERROR_MESSAGE = "AI quota exceeded for this project. Please retry later or check billing/API limits."


class UserFacingAIError(RuntimeError):
    """
    AI error that is safe to show directly in the UI.
    """


def _extract_user_facing_ai_error(exc: Exception) -> str | None:
    raw_message = " ".join(
        str(part)
        for part in getattr(exc, "args", ())
        if part is not None
    ).strip() or str(exc)

    normalized = raw_message.lower()
    quota_markers = (
        "quota exceeded",
        "rate limit",
        "rate limits",
        "resourceexhausted",
        "too many requests",
        "429",
        "generate_content_free_tier_requests",
    )

    if isinstance(exc, (ResourceExhausted, TooManyRequests)):
        return _QUOTA_ERROR_MESSAGE

    if any(marker in normalized for marker in quota_markers):
        return _QUOTA_ERROR_MESSAGE

    return None


def _raise_if_user_facing_ai_error(exc: Exception) -> None:
    message = _extract_user_facing_ai_error(exc)

    if message:
        raise UserFacingAIError(message) from exc


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )


def _next_call_id() -> int:
    global _CALL_COUNTER
    _CALL_COUNTER += 1
    return _CALL_COUNTER


def _extract_usage(message: Any) -> dict[str, Any]:
    usage = getattr(message, "usage_metadata", None) or {}
    response_metadata = getattr(message, "response_metadata", None) or {}

    if not usage and isinstance(response_metadata, dict):
        usage = (
            response_metadata.get("token_usage")
            or response_metadata.get("usage_metadata")
            or {}
        )

    return usage if isinstance(usage, dict) else {"raw_usage": usage}


def _log_llm_call(
    *,
    call_id: int,
    label: str,
    repo_id: str | None,
    usage: dict[str, Any],
) -> None:
    if not settings.ENABLE_LLM_LOGS:
        return

    logger.info(
        "llm_call id=%s label=%s repo_id=%s usage=%s",
        call_id,
        label,
        repo_id or "-",
        usage or {},
    )


async def invoke_llm(
    prompt: str,
    *,
    label: str,
    repo_id: str | None = None,
) -> str:
    call_id = _next_call_id()
    logger.info(
        "llm_call_start id=%s label=%s repo_id=%s",
        call_id,
        label,
        repo_id or "-",
    )
    try:
        response = await get_llm().ainvoke(prompt)
    except Exception as exc:
        logger.exception(
            "llm_call_failed id=%s label=%s repo_id=%s",
            call_id,
            label,
            repo_id or "-",
        )
        _raise_if_user_facing_ai_error(exc)
        raise

    _log_llm_call(
        call_id=call_id,
        label=label,
        repo_id=repo_id,
        usage=_extract_usage(response),
    )
    return response.content


async def generate_structured_output(
    prompt: str,
    schema: type[ModelT],
    *,
    label: str,
    repo_id: str | None = None,
) -> ModelT:
    parser = JsonOutputParser(pydantic_object=schema)
    prompt_template = PromptTemplate(
        template="{task}\n\n{format_instructions}",
        input_variables=["task"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
        },
    )
    rendered_prompt = await prompt_template.ainvoke({"task": prompt})
    call_id = _next_call_id()
    logger.info(
        "llm_structured_call_start id=%s label=%s repo_id=%s schema=%s",
        call_id,
        label,
        repo_id or "-",
        schema.__name__,
    )
    try:
        response = await get_llm().ainvoke(rendered_prompt)
    except Exception as exc:
        logger.exception(
            "llm_structured_call_failed id=%s label=%s repo_id=%s schema=%s",
            call_id,
            label,
            repo_id or "-",
            schema.__name__,
        )
        _raise_if_user_facing_ai_error(exc)
        raise

    _log_llm_call(
        call_id=call_id,
        label=label,
        repo_id=repo_id,
        usage=_extract_usage(response),
    )
    payload = parser.parse(response.content)
    return schema.parse_obj(payload)
