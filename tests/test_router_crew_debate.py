"""CrewAI 4역할 토론 (router) 테스트 — 헌법 3조 STEP 3. 모킹."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.routers.crew_debate import DebateResult, run_debate
from app.routers.dod_designer import DoDResult
from app.routers.intent_extractor import IntentResult
from app.routers.jangin_via_cowork import JanginResult
from app.routers.red_team import RedTeamResult

_INTENT = IntentResult(
    surface_goal="유튜브 수익 검증 엔진 제작",
    true_intent="수동 검색 시간 0화 + 사기 필터 + 실행 가능 항목 추출",
    hidden_constraints=["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
    confidence=0.87,
    needs_confirmation=False,
)
_DOD = DoDResult(
    criteria=["주 100건 수집 필터 80%", "검토 10분 이하", "도입 7일 이내"],
    measurable=True,
    confidence=0.9,
)

_JANGIN = JanginResult(
    design="유튜브 API 수집 파이프라인 구축",
    model_used="anthropic/claude-sonnet-4-6",
    via="api",
    usage={"usd": 0.002, "total_tokens": 100},
)
_JAEPANJANG_JSON = json.dumps(
    {
        "consensus": ["주 100건 수집 필터 85%", "검토 10분 이하", "도입 7일 이내"],
        "confidence": 0.85,
        "reasoning": "심판자 약점 반영 후 정량 기준 유지.",
    },
    ensure_ascii=False,
)


def _fake_call_llm(captured):
    def _inner(user_input, *, system_prompt=None, max_tokens=800, model=None, fallback=None, return_usage=False):
        captured.append({"model": model, "input": user_input})
        if model == "zai/glm-4.5-flash":
            text = "[비용] 약점1 비용 초과\n[리스크] 약점2 수집 누락\n[시간] 약점3 지연"
        elif model == "groq/llama-3.3-70b-versatile":
            text = "수집 주 100건 가능\n검토 10분 이하\n실현 가능성: 높음"
        elif model == "gemini/gemini-2.5-pro":
            text = _JAEPANJANG_JSON
        else:
            text = "기타"
        usage = {"usd": 0.001, "prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        return (text, model, usage) if return_usage else (text, model)

    return _inner


def test_run_debate_four_roles_sequential_and_context():
    captured: list[dict] = []
    rt = RedTeamResult(proceed=True, steps_complete=True, needs_user_intuition=False)
    with patch("app.routers.crew_debate.run_jangin", return_value=_JANGIN), patch(
        "app.routers.crew_debate.call_llm", side_effect=_fake_call_llm(captured)
    ), patch("app.routers.crew_debate._append_dialogue") as mocked_log, patch(
        "app.routers.crew_debate.run_red_team_pass", return_value=rt
    ):
        result = run_debate(_INTENT, _DOD)

    assert isinstance(result, DebateResult)
    # 4역할 모두 결과
    assert result.jangin == "유튜브 API 수집 파이프라인 구축"
    assert "약점" in result.simpanja
    assert "실현 가능성" in result.geomsakwan
    assert len(result.consensus) == 3
    assert result.confidence == 0.85
    # 모델 매핑
    assert result.models_used["simpanja"] == "zai/glm-4.5-flash"
    assert result.models_used["jaepanjang"] == "gemini/gemini-2.5-pro"
    # 라운드 간 컨텍스트 전달: 심판자 입력에 장인 설계, 검사관 입력에 심판자 약점, 재판장 입력에 검사관
    assert "유튜브 API 수집 파이프라인" in captured[0]["input"]  # simpanja
    assert "약점1 비용 초과" in captured[1]["input"]  # geomsakwan
    assert "실현 가능성: 높음" in captured[2]["input"]  # jaepanjang
    # dialogue append 4회 (장인+심판자+검사관+재판장)
    assert mocked_log.call_count == 4
    # 합의 통과 → 확인 불필요
    assert result.needs_confirmation is False
    assert result.total_usd > 0


def test_run_debate_empty_intent_no_calls():
    empty = IntentResult(surface_goal="", true_intent="")
    with patch("app.routers.crew_debate.run_jangin") as mocked_j, patch(
        "app.routers.crew_debate.call_llm"
    ) as mocked_llm:
        result = run_debate(empty, _DOD)

    mocked_j.assert_not_called()
    mocked_llm.assert_not_called()
    assert result.needs_confirmation is True
    assert result.consensus == []


def test_run_debate_red_team_restart_on_missing_steps():
    """Red Team 강제 단계 누락(steps_complete=False) → 최대 2회 재시작."""
    captured: list[dict] = []
    rt_fail = RedTeamResult(proceed=False, steps_complete=False, needs_user_intuition=True)
    with patch("app.routers.crew_debate.run_jangin", return_value=_JANGIN) as mocked_j, patch(
        "app.routers.crew_debate.call_llm", side_effect=_fake_call_llm(captured)
    ), patch("app.routers.crew_debate._append_dialogue"), patch(
        "app.routers.crew_debate.run_red_team_pass", return_value=rt_fail
    ):
        result = run_debate(_INTENT, _DOD, max_restarts=2)

    assert result.restarts == 2
    # 최초 1회 + 재시작 2회 = 장인 3회 호출
    assert mocked_j.call_count == 3
    assert result.needs_confirmation is True


def test_run_debate_pending_user_does_not_restart():
    """강제 단계 완료 + 사장님 확인 대기는 정상 종료(재시작 없음)."""
    captured: list[dict] = []
    rt_pending = RedTeamResult(proceed=False, steps_complete=True, needs_user_intuition=True)
    with patch("app.routers.crew_debate.run_jangin", return_value=_JANGIN) as mocked_j, patch(
        "app.routers.crew_debate.call_llm", side_effect=_fake_call_llm(captured)
    ), patch("app.routers.crew_debate._append_dialogue"), patch(
        "app.routers.crew_debate.run_red_team_pass", return_value=rt_pending
    ):
        result = run_debate(_INTENT, _DOD)

    assert result.restarts == 0
    assert mocked_j.call_count == 1
    assert result.needs_confirmation is True  # rt.proceed=False → 보류
