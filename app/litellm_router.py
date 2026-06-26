"""LiteLLM 모델 자동 선택 라우터."""

from __future__ import annotations

import os
import re
from typing import Literal

from litellm import completion

from app.config import ensure_env_from_credentials

RouterIntent = Literal["code", "summary", "short", "bulk", "verification", "default"]

# 의도별 1차 모델
_INTENT_MODEL: dict[str, str] = {
    "code": "anthropic/claude-sonnet-4-6",
    "summary": "gemini/gemini-2.5-flash",
    "short": "gemini/gemini-2.5-flash",
    "bulk": "groq/llama-3.3-70b-versatile",
    "verification": "groq/llama-3.3-70b-versatile",
    "default": "anthropic/claude-sonnet-4-6",
}

# 실패 시 폴백 순서
_FALLBACK_CHAIN = (
    "anthropic/claude-sonnet-4-6",
    "gemini/gemini-2.5-flash",
    "groq/llama-3.3-70b-versatile",
)

_DAY_PATTERN = re.compile(r"Day\s*\d+", re.IGNORECASE)


def map_parser_intent(parser_intent: str, user_input: str) -> RouterIntent:
    """supervisor input_parser 의도 → 라우터 의도."""
    text = (user_input or "").lower()
    if "요약" in user_input or "summary" in text:
        return "summary"
    if "회고" in user_input or "지금까지" in user_input:
        return "recall"  # type: ignore[return-value]
    if _DAY_PATTERN.search(user_input):
        return "review"  # type: ignore[return-value]
    if parser_intent == "code":
        return "code"
    if parser_intent == "search":
        return "short"
    if parser_intent == "dialogue":
        return "short"
    if parser_intent in ("bulk", "verification"):
        return parser_intent  # type: ignore[return-value]
    return "default"


def economy_mode() -> bool:
    return os.environ.get("ECONOMY_MODE", "").lower() in ("1", "true", "yes")


def select_model(router_intent: RouterIntent) -> str:
    """의도에 맞는 litellm 모델 문자열."""
    if economy_mode() and router_intent == "default":
        return _INTENT_MODEL["short"]
    return _INTENT_MODEL.get(router_intent, _INTENT_MODEL["default"])


def _model_chain(primary: str) -> list[str]:
    """중복 없이 primary + 폴백."""
    chain = [primary]
    for model in _FALLBACK_CHAIN:
        if model not in chain:
            chain.append(model)
    return chain


def call_llm(
    user_input: str,
    *,
    router_intent: RouterIntent = "default",
    system_prompt: str | None = None,
    max_tokens: int = 800,
) -> tuple[str, str]:
    """LLM 호출. (응답텍스트, 사용모델) 반환."""
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

    primary = select_model(router_intent)
    system = system_prompt or "당신은 도깨비 OS 어시스턴트입니다. 한국어로 간결히 답하세요."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_input},
    ]

    last_error: Exception | None = None
    for model in _model_chain(primary):
        try:
            response = completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            text = (response.choices[0].message.content or "").strip()
            return text, model
        except Exception as exc:  # noqa: BLE001 — 폴백 체인
            last_error = exc
            continue

    raise RuntimeError(f"모든 모델 호출 실패: {last_error}")
