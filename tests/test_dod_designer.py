"""DoD Auto-Designer 테스트 (모킹) — 헌법 3조 STEP 2."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.routers.dod_designer import DoDResult, design_dod
from app.routers.intent_extractor import IntentResult

_INTENT_1 = IntentResult(
    surface_goal="유튜브 수익 검증 엔진 제작",
    true_intent="수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
    hidden_constraints=["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
    confidence=0.85,
    needs_confirmation=False,
)

_DOD_1_LLM = json.dumps(
    {
        "criteria": [
            "주 100개 이상 영상 자동 수집, 사기 필터 정확도 80% 이상",
            "실행 가능 항목 주 3건 이상 추출",
            "사장님 검토 시간 회당 10분 이하",
            "월 운영 비용 무료 tier 내 0원 유지",
            "수익 모델 1건 도입까지 평균 7일 이내",
        ],
        "measurable": True,
        "confidence": 0.83,
        "reasoning": "검토 10분·도입 7일·비용 0원으로 시간절감과 ROI를 정량 고정.",
    },
    ensure_ascii=False,
)


def test_design_dod_format_and_count():
    with patch("app.routers.dod_designer.call_llm") as mocked:
        mocked.return_value = (_DOD_1_LLM, "gemini/gemini-2.5-flash")
        result = design_dod(_INTENT_1)

    assert isinstance(result, DoDResult)
    assert 3 <= len(result.criteria) <= 5
    assert result.measurable is True
    assert isinstance(result.reasoning, str) and result.reasoning
    assert isinstance(result.confidence, float)
    assert result.confidence == 0.83
    assert result.needs_confirmation is False
    assert result.model_used == "gemini/gemini-2.5-flash"


def test_design_dod_count_out_of_range_flags_confirmation():
    too_few = json.dumps(
        {
            "criteria": ["주 3건 추출", "검토 10분 이하"],
            "measurable": True,
            "confidence": 0.9,
            "reasoning": "근거.",
        },
        ensure_ascii=False,
    )
    with patch("app.routers.dod_designer.call_llm") as mocked:
        mocked.return_value = (too_few, "gemini/gemini-2.5-flash")
        result = design_dod(_INTENT_1)

    assert len(result.criteria) == 2
    assert result.measurable is False  # 개수 이탈 → 측정가능 불인정
    assert result.needs_confirmation is True


def test_design_dod_empty_intent_no_llm_call():
    empty = IntentResult(surface_goal="", true_intent="", hidden_constraints=[])
    with patch("app.routers.dod_designer.call_llm") as mocked:
        result = design_dod(empty)

    mocked.assert_not_called()
    assert result.criteria == []
    assert result.measurable is False
    assert result.needs_confirmation is True


def test_design_dod_malformed_json_safe_default():
    with patch("app.routers.dod_designer.call_llm") as mocked:
        mocked.return_value = ("죄송합니다, JSON이 아닙니다.", "gemini/gemini-2.5-flash")
        result = design_dod(_INTENT_1)

    assert result.criteria == []
    assert result.measurable is False
    assert result.confidence == 0.0
    assert result.needs_confirmation is True


def test_design_dod_red_team_hook_holds_when_not_proceed():
    """STEP 5 후크: red_team=True → run_red_team_pass 호출, proceed=False면 합의 보류."""
    from app.routers.red_team import RedTeamResult

    rt = RedTeamResult(proceed=False, steps_complete=True, needs_user_intuition=True)
    with patch("app.routers.dod_designer.call_llm") as mocked_llm, patch(
        "app.routers.dod_designer.run_red_team_pass", return_value=rt
    ) as mocked_rt:
        mocked_llm.return_value = (_DOD_1_LLM, "gemini/gemini-2.5-flash")
        result = design_dod(_INTENT_1, red_team=True)

    mocked_rt.assert_called_once()
    assert result.red_team is rt
    assert result.needs_confirmation is True  # proceed=False → 보류


def test_design_dod_no_red_team_by_default():
    """기본(red_team=False)은 run_red_team_pass 미호출 — 기존 동작 보존."""
    with patch("app.routers.dod_designer.call_llm") as mocked_llm, patch(
        "app.routers.dod_designer.run_red_team_pass"
    ) as mocked_rt:
        mocked_llm.return_value = (_DOD_1_LLM, "gemini/gemini-2.5-flash")
        result = design_dod(_INTENT_1)

    mocked_rt.assert_not_called()
    assert result.red_team is None
