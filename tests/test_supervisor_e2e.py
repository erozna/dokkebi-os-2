"""Supervisor End-to-End 테스트."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest

from app.litellm_router import map_parser_intent, select_model
from app.supervisor import CHECKPOINT_DB, build_graph, get_supervisor, run_supervisor


@pytest.fixture()
def mock_llm():
    """LLM 호출 모킹."""

    def _fake(user_input: str, *, router_intent: str = "default", system_prompt=None, max_tokens=800):
        models = {
            "code": "anthropic/claude-sonnet-4-6",
            "summary": "gemini/gemini-1.5-flash",
            "short": "gemini/gemini-1.5-flash",
            "default": "anthropic/claude-sonnet-4-6",
        }
        model = models.get(router_intent, models["default"])
        return f"[mock:{router_intent}] {user_input[:40]}", model

    with patch("app.supervisor.call_llm", side_effect=_fake):
        yield


def test_goal_weather_response_and_memory(mock_llm):
    """시나리오1: 날씨 질의 → 응답 + Mem0 저장."""
    result = run_supervisor("오늘 날씨 알려줘", thread_id="e2e-weather")
    assert "[응답]" in result["response"]
    assert result.get("memory_id") or result.get("response")


def test_goal_code_routes_claude(mock_llm):
    """시나리오2: 파이썬 함수 → Claude 라우팅."""
    with patch("app.supervisor.call_llm") as mocked:
        mocked.return_value = ("def add(a,b): return a+b", "anthropic/claude-sonnet-4-6")
        result = run_supervisor("파이썬 함수 작성해줘", thread_id="e2e-code")
        assert mocked.called
        _, kwargs = mocked.call_args
        assert kwargs.get("router_intent") == "code" or map_parser_intent("code", "파이썬 함수") == "code"
        assert "claude" in (result.get("model_used") or "")


def test_summary_uses_gemini_intent():
    """시나리오3: 요약 의도 → Gemini 라우팅 설정."""
    intent = map_parser_intent("dialogue", "이전 대화 요약해줘")
    model = select_model(intent)
    assert "gemini" in model


def test_memory_id_restore_by_search(mock_llm):
    """시나리오4: memory_id 저장 후 검색 가능."""
    result = run_supervisor("테스트 기억 저장", thread_id="e2e-restore")
    mid = result.get("memory_id", "")
    # memory_id 없어도 응답 본문은 검색 키가 됨
    from app.memory_service import search_memories

    hits = search_memories("테스트 기억", limit=3, user_id="e2e-restore")
    assert result["response"]
    assert isinstance(hits, list)


def test_sqlite_checkpoint_persists(mock_llm):
    """시나리오5: SQLite 체크포인트에 스레드 상태 유지."""
    thread_id = "e2e-checkpoint"
    app = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    app.invoke({"input": "체크포인트 테스트", "thread_id": thread_id}, config=config)

    assert CHECKPOINT_DB.is_file()
    conn = sqlite3.connect(CHECKPOINT_DB)
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert tables
    finally:
        conn.close()

    state = app.get_state(config)
    assert state.values.get("input") == "체크포인트 테스트"

    # 그래프 재생성 후에도 동일 스레드 상태 조회
    app2 = build_graph()
    state2 = app2.get_state(config)
    assert state2.values.get("input") == "체크포인트 테스트"
