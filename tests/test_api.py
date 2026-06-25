"""FastAPI /goal 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_goal_post_matches_telegram_format():
    with patch("app.supervisor.call_llm") as mocked:
        mocked.return_value = ("ping test ok", "anthropic/claude-sonnet-4-6")
        resp = client.post("/goal", json={"user_input": "ping test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "[응답]" in data["response"]
    assert "[메모리]" in data["response"]
    assert "[모델]" in data["response"]
    assert "[시간]" in data["response"]
    assert data["model"] == "anthropic/claude-sonnet-4-6"
    assert isinstance(data["memory_hits"], int)
    assert isinstance(data["elapsed_seconds"], float)
