"""Sandbox runner tests (CI uses mock)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.tools.sandbox import SandboxError, run_in_sandbox


def test_run_in_sandbox_mock_ci():
    os.environ["CI"] = "1"
    with patch("app.tools.sandbox.subprocess.run") as mocked:
        mocked.return_value.stdout = '{"ok": true, "locals": {"x": "1"}}'
        mocked.return_value.stderr = ""
        mocked.return_value.returncode = 0
        result = run_in_sandbox("x = 1")
    assert result["ok"] is True


def test_run_in_sandbox_error():
    with patch("app.tools.sandbox.subprocess.run") as mocked:
        mocked.return_value.stdout = '{"ok": false, "error": "boom"}'
        mocked.return_value.stderr = ""
        mocked.return_value.returncode = 0
        with pytest.raises(SandboxError, match="boom"):
            run_in_sandbox("bad()")
