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

# 헌법 3조 STEP 3 — 4역할 토론 모델 로스터 (사장님 (가) 승인, 2026-06-27)
# 4개 제공자(Anthropic/Z.ai/Groq/Google)로 사각지대 다양성 1.0 충족(STEP 5c).
DEBATE_ROLE_MODELS: dict[str, str] = {
    "jangin": "anthropic/claude-sonnet-4-6",       # 장인(설계) — Claude Desktop/Cowork 우선
    "simpanja": "zai/glm-4.6",                       # 심판자(약점) — Z.ai GLM
    "geomsakwan": "groq/llama-3.3-70b-versatile",    # 검사관(실현성) — Groq
    "jaepanjang": "gemini/gemini-2.5-pro",           # 재판장(합의) — Gemini Pro
}
# 역할별 폴백 (분당 한도/미가용 대응)
DEBATE_ROLE_FALLBACK: dict[str, str] = {
    "jaepanjang": "zai/glm-4.6",            # Gemini Pro 분당 5회 초과 시 GLM 우회
    "jangin": "gemini/gemini-2.5-pro",      # Cowork 타임아웃 시 임시 대체
}

# Z.ai(GLM) OpenAI 호환 엔드포인트
_ZAI_API_BASE = "https://api.z.ai/api/paas/v4"

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


def _zai_kwargs(model_str: str) -> tuple[str, dict]:
    """Z.ai(GLM) 모델이면 OpenAI 호환 호출로 변환. (호출모델, extra_kwargs)."""
    if model_str.startswith("zai/"):
        key = os.environ.get("ZAI_API_KEY")
        if not key:
            raise RuntimeError("ZAI_API_KEY 미설정 — Z.ai/GLM 호출 불가")
        bare = model_str.split("/", 1)[1]
        return f"openai/{bare}", {
            "api_base": os.environ.get("ZAI_API_BASE", _ZAI_API_BASE),
            "api_key": key,
        }
    return model_str, {}


def _usage_dict(response) -> dict:
    from litellm import completion_cost

    usage = getattr(response, "usage", None)
    try:
        cost = completion_cost(completion_response=response) or 0.0
    except Exception:  # noqa: BLE001
        cost = 0.0
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
        "usd": round(cost, 6),
    }


def call_llm(
    user_input: str,
    *,
    router_intent: RouterIntent = "default",
    system_prompt: str | None = None,
    max_tokens: int = 800,
    model: str | None = None,
    fallback: str | None = None,
    return_usage: bool = False,
):
    """LLM 호출. (응답텍스트, 사용모델) 또는 return_usage 시 (텍스트, 모델, usage) 반환.

    model을 명시하면 router_intent 대신 그 모델을 1차로 쓴다.
    fallback을 명시하면 글로벌 폴백 앞에 우선 삽입(역할별 폴백, 예: 재판장→GLM).
    """
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

    primary = model or select_model(router_intent)
    chain = [primary]
    if fallback and fallback not in chain:
        chain.append(fallback)
    for m in _FALLBACK_CHAIN:
        if m not in chain:
            chain.append(m)

    system = system_prompt or "당신은 도깨비 OS 어시스턴트입니다. 한국어로 간결히 답하세요."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_input},
    ]

    last_error: Exception | None = None
    for model_str in chain:
        try:
            call_model, extra = _zai_kwargs(model_str)
            response = completion(
                model=call_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
                **extra,
            )
            text = (response.choices[0].message.content or "").strip()
            if return_usage:
                return text, model_str, _usage_dict(response)
            return text, model_str
        except Exception as exc:  # noqa: BLE001 — 폴백 체인
            last_error = exc
            continue

    raise RuntimeError(f"모든 모델 호출 실패: {last_error}")
