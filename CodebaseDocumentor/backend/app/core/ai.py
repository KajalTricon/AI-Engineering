"""
Shared AI client helpers.
"""

import asyncio
import json
import re
import time
from functools import lru_cache
from typing import Any, TypeVar

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel
from langchain_groq import ChatGroq

from app.core.logging import get_logger
from app.core.settings import settings


ModelT = TypeVar("ModelT", bound=BaseModel)
logger = get_logger("codebase_documentor.llm")
_CALL_COUNTER = 0
_QUOTA_ERROR_MESSAGE = "AI quota or rate limit reached for this project. Please retry after a short delay."
_RATE_LIMIT_LOCK = asyncio.Lock()
_LAST_CALL_AT: dict[str, float] = {"primary": 0.0, "documentation": 0.0}


class UserFacingAIError(RuntimeError):
    """
    AI error that is safe to show directly in the UI.
    """


def _extract_exception_message(exc: Exception) -> str:
    return " ".join(
        str(part)
        for part in getattr(exc, "args", ())
        if part is not None
    ).strip() or str(exc)


def _extract_user_facing_ai_error(exc: Exception) -> str | None:
    normalized = _extract_exception_message(exc).lower()
    quota_markers = (
        "quota",
        "rate limit",
        "too many requests",
        "429",
        "tokens per minute",
        "requests per minute",
        "requests per day",
        "resource exhausted",
    )

    if any(marker in normalized for marker in quota_markers):
        return _QUOTA_ERROR_MESSAGE

    return None


def _raise_if_user_facing_ai_error(exc: Exception) -> None:
    message = _extract_user_facing_ai_error(exc)
    if message:
        raise UserFacingAIError(message) from exc


@lru_cache(maxsize=4)
def get_llm(model_name: str) -> ChatGroq:
    return ChatGroq(
        model=model_name,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=settings.GROQ_TEMPERATURE,
        max_retries=0,
    )


@lru_cache(maxsize=1)
def _retry_regex() -> re.Pattern[str]:
    return re.compile(r"try again in\s+([0-9]+(?:\.[0-9]+)?)s", re.IGNORECASE)


def _next_call_id() -> int:
    global _CALL_COUNTER
    _CALL_COUNTER += 1
    return _CALL_COUNTER


def _extract_usage(message: Any) -> dict[str, Any]:
    usage = getattr(message, "usage_metadata", None) or {}
    response_metadata = getattr(message, "response_metadata", None) or {}

    if not usage and isinstance(response_metadata, dict):
        usage = response_metadata.get("token_usage") or response_metadata.get("usage") or {}

    return usage if isinstance(usage, dict) else {"raw_usage": usage}


def _log_llm_call(*, call_id: int, label: str, scope_id: str | None, usage: dict[str, Any], model_name: str) -> None:
    if not settings.ENABLE_LLM_LOGS:
        return

    logger.info(
        "llm_call id=%s label=%s scope_id=%s model=%s usage=%s",
        call_id,
        label,
        scope_id or "-",
        model_name,
        usage or {},
    )


def _model_name(model_tier: str) -> str:
    if model_tier == "documentation":
        return settings.GROQ_MODEL_DOCUMENTATION
    return settings.GROQ_MODEL_PRIMARY


def _min_interval_seconds(model_tier: str) -> float:
    if model_tier == "documentation":
        return settings.GROQ_DOCUMENTATION_MIN_INTERVAL_SECONDS
    return settings.GROQ_PRIMARY_MIN_INTERVAL_SECONDS


async def _throttle_model(model_tier: str) -> None:
    async with _RATE_LIMIT_LOCK:
        now = time.monotonic()
        wait_seconds = max(0.0, _LAST_CALL_AT[model_tier] + _min_interval_seconds(model_tier) - now)
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        _LAST_CALL_AT[model_tier] = time.monotonic()


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or {}

    retry_after = headers.get("retry-after") if hasattr(headers, "get") else None
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except (TypeError, ValueError):
            pass

    match = _retry_regex().search(_extract_exception_message(exc))
    if match:
        try:
            return max(float(match.group(1)), 0.0)
        except ValueError:
            return None

    return None


def _extract_json_candidate(text: str) -> str:
    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1)

    object_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if object_match:
        return object_match.group(1)

    return text


def _repair_json_candidate(text: str) -> str:
    candidate = _extract_json_candidate(text).strip()

    def replace_mermaid(match: re.Match[str]) -> str:
        mermaid_body = match.group(1).strip()
        return f'"mermaid": {json.dumps(mermaid_body)}'

    candidate = re.sub(
        r'"mermaid"\s*:\s*`(.*?)`',
        replace_mermaid,
        candidate,
        flags=re.DOTALL,
    )

    return candidate


def _parse_structured_payload(parser: JsonOutputParser, text: str) -> dict[str, Any]:
    try:
        payload = parser.parse(text)
        return payload if isinstance(payload, dict) else dict(payload)
    except Exception:
        repaired = _repair_json_candidate(text)
        return json.loads(repaired)


async def _invoke_with_retries(prompt: Any, *, label: str, scope_id: str | None, model_tier: str) -> Any:
    model_name = _model_name(model_tier)
    call_id = _next_call_id()

    logger.info(
        "llm_call_start id=%s label=%s scope_id=%s model=%s",
        call_id,
        label,
        scope_id or "-",
        model_name,
    )

    last_error: Exception | None = None
    for attempt in range(1, settings.GROQ_MAX_RETRIES + 1):
        await _throttle_model(model_tier)
        try:
            response = await get_llm(model_name).ainvoke(prompt)
            _log_llm_call(
                call_id=call_id,
                label=label,
                scope_id=scope_id,
                usage=_extract_usage(response),
                model_name=model_name,
            )
            return response
        except Exception as exc:
            last_error = exc
            retry_after_seconds = _extract_retry_after_seconds(exc)
            logger.exception(
                "llm_call_failed id=%s label=%s scope_id=%s model=%s attempt=%s retry_after=%s",
                call_id,
                label,
                scope_id or "-",
                model_name,
                attempt,
                retry_after_seconds,
            )
            if attempt >= settings.GROQ_MAX_RETRIES:
                _raise_if_user_facing_ai_error(exc)
                raise

            sleep_seconds = retry_after_seconds + 1 if retry_after_seconds is not None else min(2 ** (attempt - 1), 20)
            await asyncio.sleep(sleep_seconds)

    if last_error:
        _raise_if_user_facing_ai_error(last_error)
        raise last_error

    raise RuntimeError("Unexpected LLM invocation state.")


async def invoke_llm(prompt: str, *, label: str, scope_id: str | None = None, model_tier: str = "primary") -> str:
    response = await _invoke_with_retries(
        prompt,
        label=label,
        scope_id=scope_id,
        model_tier=model_tier,
    )
    return response.content if isinstance(response.content, str) else str(response.content)


async def generate_structured_output(
    prompt: str,
    schema: type[ModelT],
    *,
    label: str,
    scope_id: str | None = None,
    model_tier: str = "primary",
) -> ModelT:
    parser = JsonOutputParser(pydantic_object=schema)
    prompt_template = PromptTemplate(
        template="{task}\n\n{format_instructions}",
        input_variables=["task"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    rendered_prompt = await prompt_template.ainvoke({"task": prompt})
    response = await _invoke_with_retries(
        rendered_prompt,
        label=label,
        scope_id=scope_id,
        model_tier=model_tier,
    )
    try:
        payload = _parse_structured_payload(parser, response.content)
    except Exception:
        logger.exception(
            "llm_structured_parse_failed label=%s scope_id=%s model_tier=%s",
            label,
            scope_id or "-",
            model_tier,
        )
        repair_prompt = (
            "Convert the following response into valid JSON only. "
            "Return a single JSON object with no markdown fences, no commentary, "
            "and ensure all string values use valid JSON quoting.\n\n"
            f"Response to repair:\n{response.content}"
        )
        repair_response = await _invoke_with_retries(
            repair_prompt,
            label=f"{label}_repair",
            scope_id=scope_id,
            model_tier=model_tier,
        )
        payload = _parse_structured_payload(parser, repair_response.content)
    return schema.parse_obj(payload)
