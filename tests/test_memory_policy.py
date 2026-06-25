"""Mem0 recall 트리거 정책 테스트."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.supervisor import run_supervisor

_FAKE_HITS = [{"memory": "hit-one", "score": 0.9}]


@pytest.fixture()
def mock_mem_and_llm():
    with patch("app.supervisor.search_memories", return_value=_FAKE_HITS):
        with patch("app.supervisor.search_web", return_value={"answer": "", "results": []}):
            with patch("app.supervisor.save_to_mem0", return_value={"result": {"results": []}}):
                with patch("app.supervisor.call_llm") as llm:
                    llm.return_value = ("ok", "gemini/gemini-1.5-flash")
                    yield llm


@pytest.mark.parametrize(
    "user_input,router_intent,thread_id",
    [
        ("이전 대화 요약해줘", None, "mem-trigger-1"),
        ("Day 6 회고 한 줄", None, "mem-trigger-2"),
        ("지금까지 진행 정리", None, "mem-trigger-3"),
        ("회고해줘", None, "mem-trigger-4"),
        ("dummy", "recall", "mem-trigger-5"),
        ("dummy", "review", "mem-trigger-6"),
        ("요약 부탁", "summary", "mem-trigger-7"),
    ],
)
def test_memory_triggers_fill_hits(mock_mem_and_llm, user_input, router_intent, thread_id):
    """7개 트리거 — memory_hits > 0."""
    kwargs: dict = {"thread_id": thread_id}
    if router_intent:
        kwargs["router_intent"] = router_intent
    result = run_supervisor(user_input, **kwargs)
    assert result.get("memory_hits", 0) > 0


def test_no_trigger_skips_memory(mock_mem_and_llm):
    """일반 입력은 memory_hits=0."""
    with patch("app.supervisor.search_memories") as mem:
        mem.return_value = _FAKE_HITS
        result = run_supervisor("hello world test", thread_id="mem-none")
    mem.assert_not_called()
    assert result.get("memory_hits", 0) == 0
