"""Executor STEP 7 테스트 — 헌법 3조. 화이트리스트 분기 + 클립보드 게이팅. 모킹."""

from __future__ import annotations

from unittest.mock import patch

from app.routers.capability_router import RouteDecision
from app.routers.executor import _detect_tool, execute
from app.tools.whitelist import WhitelistResult


def test_detect_tool_youtube_url():
    tool, arg = _detect_tool("https://youtube.com/@somechannel 분석")
    assert tool == "yt-dlp"
    assert arg.startswith("https://youtube.com")


def test_detect_tool_pytest():
    tool, _ = _detect_tool("pytest 회귀 테스트 실행")
    assert tool == "pytest"


def test_detect_tool_chroma():
    tool, _ = _detect_tool("사장님 과거 관심사 매칭")
    assert tool == "chromadb"


def test_detect_tool_default_tavily():
    tool, arg = _detect_tool("유튜브 부업 채널 유형 분석")
    assert tool == "tavily"
    assert arg


def test_auto_live_false_is_plan_only():
    d = RouteDecision(route="A", reason="r", task="유튜브 분석", prompt_or_action="유튜브 분석")
    with patch("app.routers.executor.run_whitelisted") as mocked:
        res = execute(d, live=False)
    mocked.assert_not_called()
    assert res.status == "pending"
    assert res.tool == "tavily"


def test_auto_live_true_runs_whitelist():
    d = RouteDecision(route="A", reason="r", task="유튜브 분석", prompt_or_action="유튜브 분석")
    with patch(
        "app.routers.executor.run_whitelisted",
        return_value=WhitelistResult("tavily", True, summary="검색 결과 3건", artifact_path="data/x.json"),
    ) as mocked:
        res = execute(d, live=True)
    mocked.assert_called_once()
    assert res.status == "done"
    assert "검색 결과" in res.detail
    assert res.artifact_path == "data/x.json"


def test_auto_live_true_whitelist_failure():
    d = RouteDecision(route="A", reason="r", task="x", prompt_or_action="x")
    with patch(
        "app.routers.executor.run_whitelisted",
        return_value=WhitelistResult("tavily", False, error="키 없음"),
    ):
        res = execute(d, live=True)
    assert res.status == "error"
    assert "실패" in res.detail


def test_bridge_writes_file_and_clipboard_gated(tmp_path):
    d = RouteDecision(route="B", reason="r", task="요약", target_channel="Claude.ai", prompt_or_action="요약 프롬프트")
    # live=False → 클립보드 미동작
    with patch("app.routers.executor._copy_to_clipboard") as mocked:
        res = execute(d, live=False)
    mocked.assert_not_called()
    assert res.status == "pending"
    assert res.artifact_path

    # live=True → 클립보드 복사 호출
    with patch("app.routers.executor._copy_to_clipboard", return_value=True) as mocked2:
        res2 = execute(d, live=True)
    mocked2.assert_called_once()
    assert "클립보드" in res2.detail


def test_ask_returns_question():
    d = RouteDecision(route="C", reason="r", task="결정", prompt_or_action="GLM 도입할까?")
    res = execute(d)
    assert res.question == "GLM 도입할까?"
