"""Economy mode routing."""

from __future__ import annotations

from app.litellm_router import economy_mode, select_model


def test_economy_mode_default_to_gemini(monkeypatch):
    monkeypatch.setenv("ECONOMY_MODE", "1")
    assert economy_mode() is True
    assert "gemini" in select_model("default")


def test_economy_mode_code_still_sonnet(monkeypatch):
    monkeypatch.setenv("ECONOMY_MODE", "1")
    assert "claude" in select_model("code")
