"""handoff/ 디렉터리 경로."""

from __future__ import annotations

from app.config import ROOT

HANDOFF_ROOT = ROOT / "handoff"
ACTIVE_DIR = HANDOFF_ROOT / "active"
OUTBOX_DIR = HANDOFF_ROOT / "outbox"
INBOX_DIR = HANDOFF_ROOT / "inbox"
MANIFEST_PATH = ACTIVE_DIR / "manifest.json"
LATEST_PATH = HANDOFF_ROOT / "latest.md"
IMPLEMENT_PATH = HANDOFF_ROOT / "implement.md"


def ensure_handoff_dirs() -> None:
    for path in (ACTIVE_DIR, OUTBOX_DIR, INBOX_DIR):
        path.mkdir(parents=True, exist_ok=True)
