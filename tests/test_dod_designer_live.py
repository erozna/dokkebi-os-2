"""DoD Auto-Designer 실 LLM 평가 (모킹 아님) — 헌법 3조 STEP 2.

기본 pytest 실행에서 제외(`pyproject.toml addopts = -m 'not live'`).
수동 실행:  pytest -m live tests/test_dod_designer_live.py -s

GEMINI/ANTHROPIC API 키(ALL_CREDENTIALS.json 또는 환경변수)가 없으면 자동 skip.
"""

from __future__ import annotations

import os

import pytest

from app.config import ensure_env_from_credentials
from app.routers.dod_designer import design_dod
from app.routers.intent_extractor import IntentResult

pytestmark = pytest.mark.live

# "유튜브 엔진" 의도 (평가 #1 통과본 기반)
INTENT_1 = IntentResult(
    surface_goal="유튜브 수익 검증 엔진 제작",
    true_intent="수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
    hidden_constraints=["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
    confidence=0.87,
    needs_confirmation=False,
)

_MEASURABLE_UNITS = ("%", "분", "시간", "일", "건", "개", "회", "원", "$", "tier", "무료", "정확도")


def _has_key() -> bool:
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


@pytest.mark.skipif(
    not _has_key(),
    reason="GEMINI/ANTHROPIC API 키 미설정. 사장님 [D] 키 준비 필요.",
)
def test_design_dod_live_dataset1() -> None:
    """데이터셋 #1: 유튜브 엔진 의도 → 정량 완료조건 3~5개."""
    result = design_dod(INTENT_1)

    # criteria 3~5개
    assert 3 <= len(result.criteria) <= 5, f"criteria 개수 이탈: {len(result.criteria)}"

    # 모든 criteria가 측정 가능 단위 포함 (정성 표현 아님)
    for c in result.criteria:
        assert any(u in c for u in _MEASURABLE_UNITS), f"측정 단위 없음: {c!r}"
    assert result.measurable is True

    # 사장님 직감 정답 후보와 의미 일치도 (3개 이상 매칭)
    joined = " ".join(result.criteria)
    matches = 0
    if any(k in joined for k in ("100", "수집")) and any(k in joined for k in ("영상", "필터", "80")):
        matches += 1
    if "추출" in joined and any(k in joined for k in ("3", "실행", "건")):
        matches += 1
    if any(k in joined for k in ("검토", "10")) and any(k in joined for k in ("분", "회")):
        matches += 1
    if any(k in joined for k in ("무료", "비용")) and any(k in joined for k in ("0", "tier", "원")):
        matches += 1
    if any(k in joined for k in ("도입", "7")) and any(k in joined for k in ("일", "수익")):
        matches += 1
    assert matches >= 3, f"정답 일치 부족({matches}/5): {result.criteria!r}"

    assert result.confidence >= 0.7, f"confidence 낮음: {result.confidence}"
