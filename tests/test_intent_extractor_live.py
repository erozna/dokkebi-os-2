"""Intent Extractor 실 LLM 평가 (모킹 아님) — 헌법 3조 STEP 1.

기본 pytest 실행에서 제외(`pyproject.toml addopts = -m 'not live'`).
수동 실행:  pytest -m live tests/test_intent_extractor_live.py -s

ANTHROPIC_API_KEY(ALL_CREDENTIALS.json 또는 환경변수)가 없으면 자동 skip.
정액제 OAuth가 아닌 별도 API 키만 사용한다(헌법 8조).
"""

from __future__ import annotations

import os

import pytest

from app.config import ensure_env_from_credentials
from app.routers.intent_extractor import extract_intent

pytestmark = pytest.mark.live

DATASET_1_INPUT = (
    "유튜브에서 돈 버는 방법을 검증하는 엔진을 만들어서 자동으로 검색해서 "
    "그 유튜브 컨텐츠를 분석하고, 현실적 검증을 해보고 자동으로 도입할수 있는것들은 "
    "실행하는 프로그램을 만들어줘"
)


def _has_anthropic_key() -> bool:
    ensure_env_from_credentials()
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@pytest.mark.skipif(
    not _has_anthropic_key(),
    reason="ANTHROPIC_API_KEY 미설정 (ALL_CREDENTIALS.json/환경변수). 사장님 [D] 키 준비 필요.",
)
def test_intent_extractor_live_dataset1() -> None:
    """데이터셋 #1: 유튜브 수익 검증 엔진. 의미 일치 메트릭으로 평가."""
    result = extract_intent(DATASET_1_INPUT)

    surface = result.surface_goal
    true_intent = result.true_intent
    constraints = " ".join(result.hidden_constraints)

    # surface_goal: "유튜브" + (엔진/검증/수익) 중 2개 이상
    surface_hits = sum(1 for k in ("유튜브", "엔진", "검증", "수익") if k in surface)
    assert surface_hits >= 2, f"surface_goal 키워드 부족: {surface!r}"

    # true_intent: 핵심 3요소 (의미 일치, 문자 일치 아님)
    time_zero = "시간" in true_intent and any(
        w in true_intent for w in ("0", "절감", "단축", "줄", "제거", "없", "최소")
    )
    g1 = time_zero or "자동" in true_intent
    g2 = any(w in true_intent for w in ("필터", "검증", "거르", "사기", "걸러", "배제", "차단"))
    g3 = "실행" in true_intent or "도입" in true_intent
    assert g1 and g2 and g3, f"true_intent 3요소 미충족 (시간0화={g1},필터={g2},실행={g3}): {true_intent!r}"

    # hidden_constraints: 정액제/무료/1인 중 2개 이상
    c_hits = (
        int("정액" in constraints)
        + int("무료" in constraints or "오픈소스" in constraints)
        + int(any(w in constraints for w in ("1인", "개인", "혼자", "1 인")))
    )
    assert c_hits >= 2, f"hidden_constraints 부족({c_hits}/3): {result.hidden_constraints!r}"

    # confidence 0.7 이상이면 needs_confirmation=False (정상). 미만이면 확인 필요로 동작.
    assert result.confidence >= 0.7, f"confidence 낮음: {result.confidence}"
    assert result.needs_confirmation is False
