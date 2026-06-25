"""CrewAI 토론 + LangGraph 연동 테스트."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.crew.brain_writer import record_consensus
from app.crew.debate import CrewDebateResult, run_crew_debate
from app.supervisor import _needs_crew_debate, run_supervisor


def test_needs_crew_debate_keywords():
    assert _needs_crew_debate("default", "Week 2 토론 주제")
    assert _needs_crew_debate("debate", "아무거나")
    assert not _needs_crew_debate("default", "오늘 날씨")


def test_run_crew_debate_ci_mock(monkeypatch):
    monkeypatch.setenv("CI", "1")
    result = run_crew_debate("테스트 주제")
    assert isinstance(result, CrewDebateResult)
    assert "[ci-mock 합의]" in result.consensus
    assert "[장인]" in result.transcript


def test_supervisor_debate_route(monkeypatch, tmp_path):
    monkeypatch.setenv("CI", "1")
    with patch("app.supervisor.record_consensus") as mocked_record:
        mocked_record.return_value = "test_entry_123"
        result = run_supervisor("CrewAI 착수 순서", router_intent="debate", thread_id="crew-e2e")
    assert "[CrewAI]" in result["response"]
    assert "[SHARED_BRAIN]" in result["response"]
    mocked_record.assert_called_once()


def test_record_consensus_appends_entry(tmp_path, monkeypatch):
    brain = tmp_path / "SHARED_BRAIN.json"
    brain.write_text(
        json.dumps({"entries": [], "총_항목수": 0}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.crew.brain_writer.PROJECT_COPY", brain)
    monkeypatch.setattr("app.crew.brain_writer.SHARED_BRAIN_SOURCES", ())

    entry_id = record_consensus("주제", "합의안 본문", transcript="토론 요약")
    data = json.loads(brain.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 1
    assert data["entries"][0]["entry_id"] == entry_id
    assert data["entries"][0]["payload"]["consensus"] == "합의안 본문"
