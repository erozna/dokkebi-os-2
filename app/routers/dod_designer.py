"""DoD Auto-Designer — 헌법 3조 STEP 2.

Intent Extractor의 진짜 의도를 받아, 정량 판정 가능한 완료조건(DoD) 3~5개를 설계한다.
평가 모델은 Gemini(LiteLLM 경유). 정성 표현 금지·측정 단위 강제는 prompts/dod_designer.md에서.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from app.config import ROOT
from app.litellm_router import call_llm
from app.routers.intent_extractor import IntentResult, _parse_json

_PROMPT_PATH = ROOT / "prompts" / "dod_designer.md"
_DEFAULT_THRESHOLD = 0.7
# gemini-2.0-flash-exp는 2026년 retired(404). Intent 평가에서 검증된 2.5-flash 사용.
_DOD_MODEL = "gemini/gemini-2.5-flash"
_MIN_CRITERIA = 3
_MAX_CRITERIA = 5


@dataclass
class DoDResult:
    """완료조건(Definition of Done) 설계 결과."""

    criteria: list[str] = field(default_factory=list)
    measurable: bool = False
    confidence: float = 0.0
    reasoning: str = ""
    needs_confirmation: bool = True
    model_used: str = ""
    raw: str = ""


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    if _PROMPT_PATH.is_file():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "진짜 의도를 받아 측정 가능한 완료조건 3~5개를 JSON으로 설계하세요."


def _build_user_input(intent: IntentResult) -> str:
    constraints = ", ".join(intent.hidden_constraints) or "(명시 없음)"
    return (
        f"표면 목표: {intent.surface_goal}\n"
        f"진짜 의도: {intent.true_intent}\n"
        f"숨은 제약: {constraints}"
    )


def _coerce_criteria(value: object) -> list[str]:
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


def design_dod(
    intent_result: IntentResult,
    *,
    confidence_threshold: float = _DEFAULT_THRESHOLD,
    max_tokens: int = 2048,  # gemini-2.5-flash는 thinking 토큰 소모 → 넉넉히
    model: str = _DOD_MODEL,
) -> DoDResult:
    """진짜 의도 → 정량 완료조건 3~5개.

    의도가 비었으면 LLM 호출 없이 확인 필요로 반환.
    confidence < threshold 또는 criteria 개수 이탈 시 needs_confirmation=True.
    """
    if intent_result is None or not (intent_result.surface_goal or intent_result.true_intent).strip():
        return DoDResult(
            criteria=[],
            measurable=False,
            confidence=0.0,
            reasoning="빈 의도 — DoD 설계 불가.",
            needs_confirmation=True,
        )

    response, model_used = call_llm(
        _build_user_input(intent_result),
        system_prompt=_load_system_prompt(),
        max_tokens=max_tokens,
        model=model,
    )
    data = _parse_json(response)

    criteria = _coerce_criteria(data.get("criteria"))
    confidence = _coerce_confidence(data.get("confidence"))
    count_ok = _MIN_CRITERIA <= len(criteria) <= _MAX_CRITERIA
    measurable = bool(data.get("measurable")) and count_ok
    needs_confirmation = confidence < confidence_threshold or not count_ok or not measurable

    return DoDResult(
        criteria=criteria,
        measurable=measurable,
        confidence=confidence,
        reasoning=str(data.get("reasoning", "")).strip(),
        needs_confirmation=needs_confirmation,
        model_used=model_used,
        raw=response,
    )
