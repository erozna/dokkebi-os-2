"""Intent Extractor — 헌법 3조 STEP 1.

사장님 입력에서 표면 목표가 아닌 진짜 의도를 추출한다.
LiteLLM 경유 Claude Sonnet(router_intent="code") 호출. 정액제 Claude는
공식 클라이언트에서만 사용하고, 코드 경로는 API 키 기반(헌법 8조).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache

from app.config import ROOT
from app.litellm_router import call_llm

_PROMPT_PATH = ROOT / "prompts" / "intent_extractor.md"
_DEFAULT_THRESHOLD = 0.7
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class IntentResult:
    """의도 추출 결과."""

    surface_goal: str
    true_intent: str
    hidden_constraints: list[str] = field(default_factory=list)
    confidence: float = 0.0
    needs_confirmation: bool = True
    reasoning: str = ""
    model_used: str = ""
    raw: str = ""


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    """prompts/intent_extractor.md 로드 (헌법 2조 9목표 prefix 포함)."""
    if _PROMPT_PATH.is_file():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "사장님 입력의 진짜 의도를 JSON으로 추출하세요."


def _parse_json(text: str) -> dict:
    """LLM 응답에서 JSON 객체 추출 (코드펜스 허용)."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = re.sub(r"^json\s*", "", cleaned, flags=re.IGNORECASE).strip()
    match = _JSON_BLOCK.search(cleaned)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _coerce_constraints(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_confidence(value: object) -> float:
    try:
        conf = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, conf))


def extract_intent(
    user_input: str,
    *,
    confidence_threshold: float = _DEFAULT_THRESHOLD,
    max_tokens: int = 600,
) -> IntentResult:
    """표면/진짜/제약/이유 4분리 + confidence 기반 확인 필요 여부.

    confidence < threshold → needs_confirmation=True (헌법 STEP 1 사장님 확인 [C]).
    빈 입력은 LLM 호출 없이 즉시 확인 필요로 반환.
    """
    text = (user_input or "").strip()
    if not text:
        return IntentResult(
            surface_goal="",
            true_intent="",
            hidden_constraints=[],
            confidence=0.0,
            needs_confirmation=True,
            reasoning="빈 입력 — 추출할 의도 없음.",
        )

    response, model_used = call_llm(
        text,
        router_intent="code",
        system_prompt=_load_system_prompt(),
        max_tokens=max_tokens,
    )
    data = _parse_json(response)
    confidence = _coerce_confidence(data.get("confidence"))

    return IntentResult(
        surface_goal=str(data.get("surface_goal", "")).strip(),
        true_intent=str(data.get("true_intent", "")).strip(),
        hidden_constraints=_coerce_constraints(data.get("hidden_constraints")),
        confidence=confidence,
        needs_confirmation=confidence < confidence_threshold,
        reasoning=str(data.get("reasoning", "")).strip(),
        model_used=model_used,
        raw=response,
    )
