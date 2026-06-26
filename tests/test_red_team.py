"""Red Team Pass 테스트 (모킹) — 헌법 3조 STEP 5."""

from __future__ import annotations

from unittest.mock import patch

from app.routers.red_team import (
    RedTeamResult,
    diversity_check,
    run_red_team_pass,
)

_CONSENSUS = {
    "surface_goal": "유튜브 수익 검증 엔진 제작",
    "true_intent": "수동 검색 시간 0화 + 사기 필터 + 실행 가능 항목 추출",
    "criteria": ["주 100건 수집 필터 80%", "검토 10분 이하", "도입 7일 이내"],
}


def test_diversity_check_all_distinct():
    score, ok, warning = diversity_check(
        ["anthropic/a", "gemini/b", "groq/c", "zhipu/glm"]
    )
    assert score == 1.0
    assert ok is True
    assert warning == ""


def test_diversity_check_duplicate_provider_warns():
    # 기본 4역할 구성: anthropic 2회(장인·재판장) → distinct 3/4
    score, ok, warning = diversity_check(
        ["anthropic/opus", "gemini/flash", "groq/llama", "anthropic/sonnet"]
    )
    assert score == 0.75
    assert ok is True  # 2개 이상 제공자라 통과
    assert "중복" in warning and "anthropic" in warning


def test_diversity_check_all_same_provider_fails():
    score, ok, warning = diversity_check(
        ["anthropic/a", "anthropic/b", "anthropic/c", "anthropic/d"]
    )
    assert score == 0.25
    assert ok is False
    assert "동일 제공자" in warning


def test_run_red_team_pass_pending_user():
    """강제 단계 완료 + 사장님 미확인 → proceed=False, 직감 [C] 대기."""
    with patch("app.routers.red_team.memory_recall", return_value=(["[dialogue] x"], True)), patch(
        "app.routers.red_team.tool_audit", return_value=(["filesystem"], True)
    ), patch(
        "app.routers.red_team.red_team_debate",
        return_value=(["이유1", "이유2", "이유3"], "anthropic/claude-sonnet-4-6"),
    ):
        result = run_red_team_pass(_CONSENSUS, models=["anthropic/a", "gemini/b", "groq/c", "x/d"])

    assert isinstance(result, RedTeamResult)
    assert result.steps_complete is True
    assert result.proceed is False
    assert result.needs_user_intuition is True
    assert len(result.failure_reasons) == 3


def test_run_red_team_pass_user_confirmed_proceeds():
    with patch("app.routers.red_team.memory_recall", return_value=([], True)), patch(
        "app.routers.red_team.tool_audit", return_value=(["filesystem"], True)
    ), patch(
        "app.routers.red_team.red_team_debate",
        return_value=(["a", "b", "c"], "anthropic/claude-sonnet-4-6"),
    ):
        result = run_red_team_pass(
            _CONSENSUS,
            models=["anthropic/a", "gemini/b", "groq/c", "x/d"],
            user_confirmed=True,
        )

    assert result.proceed is True
    assert result.needs_user_intuition is False


def test_run_red_team_pass_missing_memory_holds():
    """5a 메모리 회수 실패 → 강제 단계 누락 → proceed=False."""
    with patch("app.routers.red_team.memory_recall", return_value=([], False)), patch(
        "app.routers.red_team.tool_audit", return_value=(["filesystem"], True)
    ), patch(
        "app.routers.red_team.red_team_debate",
        return_value=(["a", "b", "c"], "anthropic/claude-sonnet-4-6"),
    ):
        result = run_red_team_pass(
            _CONSENSUS,
            models=["anthropic/a", "gemini/b", "groq/c", "x/d"],
            user_confirmed=True,
        )

    assert result.memory_recall_done is False
    assert result.steps_complete is False
    assert result.proceed is False


def test_run_red_team_pass_insufficient_debate_holds():
    """5c 토론 실패(<3) → debate_done=False → 보류."""
    with patch("app.routers.red_team.memory_recall", return_value=([], True)), patch(
        "app.routers.red_team.tool_audit", return_value=(["filesystem"], True)
    ), patch(
        "app.routers.red_team.red_team_debate",
        return_value=(["하나뿐"], "anthropic/claude-sonnet-4-6"),
    ):
        result = run_red_team_pass(
            _CONSENSUS,
            models=["anthropic/a", "gemini/b", "groq/c", "x/d"],
            user_confirmed=True,
        )

    assert result.debate_done is False
    assert result.steps_complete is False
    assert result.proceed is False
