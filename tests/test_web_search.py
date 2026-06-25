"""Tavily web search PoC 테스트."""

from __future__ import annotations

from unittest.mock import patch


from app.supervisor import run_supervisor
from app.tools.web_search import WebSearchError, search_web


def test_mock_in_ci(monkeypatch):
    """CI=1 일 때 mock 반환."""
    monkeypatch.setenv("CI", "1")
    data = search_web("테스트 쿼리")
    assert data["answer"]
    assert len(data["results"]) >= 1


def test_keyword_trigger():
    """키워드 입력 시 web_hits 채움."""
    fake = {
        "answer": "뉴스 요약",
        "results": [{"title": "A", "url": "https://a", "content": "본문"}],
    }
    with patch("app.supervisor.search_web", return_value=fake):
        with patch("app.supervisor.save_to_mem0", return_value={"result": {"results": []}}):
            with patch("app.supervisor.call_llm") as llm:
                llm.return_value = ("ok", "gemini/gemini-1.5-flash")
                result = run_supervisor("최신 뉴스 검색해줘", thread_id="web-kw")
    assert result.get("web_hits", 0) >= 1


def test_router_intent_search():
    """router_intent=search 시 web_hits 채움."""
    fake = {
        "answer": "ans",
        "results": [{"title": "B", "url": "https://b", "content": "c"}],
    }
    with patch("app.supervisor.search_web", return_value=fake):
        with patch("app.supervisor.save_to_mem0", return_value={"result": {"results": []}}):
            with patch("app.supervisor.call_llm") as llm:
                llm.return_value = ("ok", "gemini/gemini-1.5-flash")
                result = run_supervisor(
                "테스트",
                thread_id="web-intent",
                router_intent="search",
            )
    assert result.get("web_hits", 0) >= 1


def test_failure_fallback():
    """search_web 실패 시 web_hits=0, 응답 정상."""
    with patch("app.supervisor.search_web", side_effect=WebSearchError("fail")):
        with patch("app.supervisor.save_to_mem0", return_value={"result": {"results": []}}):
            with patch("app.supervisor.call_llm") as llm:
                llm.return_value = ("fallback ok", "anthropic/claude-sonnet-4-6")
                result = run_supervisor("최신 뉴스 검색", thread_id="web-fail")
    assert result.get("web_hits", 0) == 0
    assert "fallback ok" in (result.get("response") or "")
