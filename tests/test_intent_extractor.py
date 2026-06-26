"""Intent Extractor 테스트 — 헌법 3조 STEP 1."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.routers.intent_extractor import IntentResult, extract_intent

# 평가 데이터셋 #1 — "유튜브 엔진 만들어줘" 정답지 (헌법/dialogue 박제)
_DATASET_1_LLM = json.dumps(
    {
        "surface_goal": "유튜브 수익 검증 엔진 제작",
        "true_intent": "수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
        "hidden_constraints": ["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
        "confidence": 0.82,
        "reasoning": "표면은 엔진 제작이나 진짜 목적은 시간절감과 신뢰 필터. ROI 관점 정액제·무료 도구 중심.",
    },
    ensure_ascii=False,
)


def test_extract_intent_dataset_1():
    with patch("app.routers.intent_extractor.call_llm") as mocked:
        mocked.return_value = (_DATASET_1_LLM, "anthropic/claude-sonnet-4-6")
        result = extract_intent("유튜브 엔진 만들어줘")

    assert isinstance(result, IntentResult)
    assert result.surface_goal == "유튜브 수익 검증 엔진 제작"
    assert "시간" in result.true_intent
    assert "정액제 활용" in result.hidden_constraints
    assert len(result.hidden_constraints) == 3
    assert result.confidence == 0.82
    assert result.needs_confirmation is False  # 0.82 >= 0.7


def test_low_confidence_triggers_confirmation():
    low = json.dumps(
        {
            "surface_goal": "뭔가 만들어줘",
            "true_intent": "불명확",
            "hidden_constraints": [],
            "confidence": 0.4,
            "reasoning": "입력이 모호함.",
        },
        ensure_ascii=False,
    )
    with patch("app.routers.intent_extractor.call_llm") as mocked:
        mocked.return_value = (low, "anthropic/claude-sonnet-4-6")
        result = extract_intent("뭔가 해줘")

    assert result.confidence == 0.4
    assert result.needs_confirmation is True  # 0.4 < 0.7


def test_empty_input_no_llm_call():
    with patch("app.routers.intent_extractor.call_llm") as mocked:
        result = extract_intent("   ")

    mocked.assert_not_called()
    assert result.needs_confirmation is True
    assert result.confidence == 0.0
    assert result.surface_goal == ""


def test_json_with_code_fence():
    fenced = "```json\n" + _DATASET_1_LLM + "\n```"
    with patch("app.routers.intent_extractor.call_llm") as mocked:
        mocked.return_value = (fenced, "gemini/gemini-1.5-flash")
        result = extract_intent("유튜브 엔진 만들어줘")

    assert result.surface_goal == "유튜브 수익 검증 엔진 제작"
    assert result.confidence == 0.82


def test_malformed_json_safe_default():
    with patch("app.routers.intent_extractor.call_llm") as mocked:
        mocked.return_value = ("죄송합니다, JSON이 아닙니다.", "groq/llama-3.3-70b-versatile")
        result = extract_intent("아무거나")

    assert result.confidence == 0.0
    assert result.needs_confirmation is True
