"""handoff/ 디렉터리 경로."""

from __future__ import annotations

from app.config import ROOT

HANDOFF_ROOT = ROOT / "handoff"
ACTIVE_DIR = HANDOFF_ROOT / "active"
OUTBOX_DIR = HANDOFF_ROOT / "outbox"
INBOX_DIR = HANDOFF_ROOT / "inbox"
# 세션 부팅 문서(handoff/latest.md)와 충돌하지 않도록 bridge 런타임은 하위 폴더 분리
BRIDGE_DIR = HANDOFF_ROOT / "bridge"
MANIFEST_PATH = ACTIVE_DIR / "manifest.json"
LATEST_PATH = BRIDGE_DIR / "latest.md"
IMPLEMENT_PATH = BRIDGE_DIR / "implement.md"


def ensure_handoff_dirs() -> None:
    for path in (ACTIVE_DIR, OUTBOX_DIR, INBOX_DIR, BRIDGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
