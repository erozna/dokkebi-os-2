"""pytest 공통 — CI 환경 분기."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _ci_environment(monkeypatch):
    """GitHub Actions: embedded Chroma + LLM mock."""
    if os.environ.get("CI") != "1":
        yield
        return

    monkeypatch.setenv("USE_CHROMA_SERVER", "0")

    def _fake_llm(
        user_input: str,
        *,
        router_intent: str = "default",
        system_prompt=None,
        max_tokens=800,
    ):
        return f"[ci-mock:{router_intent}] {user_input[:60]}", "anthropic/claude-sonnet-4-6"

    with patch("app.supervisor.call_llm", side_effect=_fake_llm):
        yield
