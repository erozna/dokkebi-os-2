"""Bridge 세션 manifest."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.subscription_bridge.paths import MANIFEST_PATH, ensure_handoff_dirs
from app.subscription_bridge.roles import ROUND_ORDER


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest() -> dict[str, Any]:
    ensure_handoff_dirs()
    if not MANIFEST_PATH.is_file():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict[str, Any]) -> None:
    ensure_handoff_dirs()
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def new_manifest(topic: str) -> dict[str, Any]:
    return {
        "mode": "subscription_bridge",
        "topic": topic,
        "created_at": _now(),
        "updated_at": _now(),
        "round_order": list(ROUND_ORDER),
        "current_index": 0,
        "rounds": {},
    }


def round_key(index: int, role_id: str) -> str:
    return f"round{index + 1}_{role_id}"


def get_current_role(manifest: dict[str, Any]) -> str | None:
    order = manifest.get("round_order") or list(ROUND_ORDER)
    idx = int(manifest.get("current_index") or 0)
    if idx >= len(order):
        return None
    return str(order[idx])
