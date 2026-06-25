"""Subscription Bridge 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.subscription_bridge import bridge_ingest, bridge_next, bridge_prep, bridge_status
from app.subscription_bridge.paths import LATEST_PATH


@pytest.fixture()
def handoff_tmp(monkeypatch, tmp_path: Path):
    root = tmp_path / "handoff"
    active = root / "active"
    outbox = root / "outbox"
    inbox = root / "inbox"
    for d in (active, outbox, inbox):
        d.mkdir(parents=True)
    monkeypatch.setattr("app.subscription_bridge.paths.HANDOFF_ROOT", root)
    monkeypatch.setattr("app.subscription_bridge.paths.ACTIVE_DIR", active)
    monkeypatch.setattr("app.subscription_bridge.paths.OUTBOX_DIR", outbox)
    monkeypatch.setattr("app.subscription_bridge.paths.INBOX_DIR", inbox)
    monkeypatch.setattr("app.subscription_bridge.paths.MANIFEST_PATH", active / "manifest.json")
    monkeypatch.setattr("app.subscription_bridge.paths.LATEST_PATH", root / "latest.md")
    monkeypatch.setattr("app.subscription_bridge.paths.IMPLEMENT_PATH", root / "implement.md")
    monkeypatch.setattr("app.subscription_bridge.session.MANIFEST_PATH", active / "manifest.json")
    return root


def test_bridge_prep_creates_outbox(handoff_tmp, monkeypatch):
    monkeypatch.setattr("app.subscription_bridge.service.search_memories", lambda *a, **k: [])
    monkeypatch.setattr("app.subscription_bridge.service.save_to_mem0", lambda *a, **k: {})
    result = bridge_prep("Week 4 우선순위", thread_id="test")
    assert result["role"] == "장인"
    assert "claude_web" in result["outbox_file"]
    assert (handoff_tmp / "active" / "manifest.json").is_file()
    status = bridge_status()
    assert status["active"] is True


def test_bridge_round_trip(handoff_tmp, monkeypatch):
    monkeypatch.setattr("app.subscription_bridge.service.search_memories", lambda *a, **k: [])
    monkeypatch.setattr("app.subscription_bridge.service.save_to_mem0", lambda *a, **k: {})
    bridge_prep("테스트 주제")
    ing = bridge_ingest("장인 구현안 답변", thread_id="test")
    assert ing["ingested_role"] == "장인"
    assert ing["next"]["role"] == "심판자"
    nxt = bridge_next()
    assert nxt["role"] == "심판자"
    assert "gemini_web" in nxt["outbox_file"]


def test_latest_md_after_ingest(handoff_tmp, monkeypatch):
    monkeypatch.setattr("app.subscription_bridge.service.search_memories", lambda *a, **k: [])
    monkeypatch.setattr("app.subscription_bridge.service.save_to_mem0", lambda *a, **k: {})
    bridge_prep("합의 테스트")
    bridge_ingest("재판장이 아닌 장인 답")
    assert LATEST_PATH.is_file()
    assert "합의 테스트" in LATEST_PATH.read_text(encoding="utf-8")
