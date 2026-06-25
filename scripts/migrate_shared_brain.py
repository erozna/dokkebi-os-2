"""Migrate SHARED_BRAIN.json entries into Mem0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import SHARED_BRAIN_SOURCES, ensure_env_from_credentials
from app.mem0_router import save_to_mem0


def _entry_text(entry: dict) -> str:
    parts = [
        f"action={entry.get('action') or entry.get('작업')}",
        f"actor={entry.get('actor') or entry.get('담당', '')}",
        f"task_id={entry.get('task_id', '')}",
        f"timestamp={entry.get('timestamp') or entry.get('시각', '')}",
    ]
    payload = entry.get("payload")
    if payload:
        parts.append(f"payload={json.dumps(payload, ensure_ascii=False)}")
    for key in ("감지문제수", "결과파일", "상태"):
        if key in entry:
            parts.append(f"{key}={entry[key]}")
    return " | ".join(p for p in parts if p and not p.endswith("="))


def load_all_entries() -> list[dict]:
    entries: list[dict] = []
    for path in SHARED_BRAIN_SOURCES:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data.get("entries"), list):
            entries.extend(data["entries"])
        if isinstance(data.get("done_history"), list):
            entries.extend(data["done_history"])
    return entries


def main() -> int:
    ensure_env_from_credentials()

    entries = load_all_entries()
    if not entries:
        print("No SHARED_BRAIN entries found.")
        return 1

    user_id = "shared-brain-migration"

    migrated = 0
    for entry in entries:
        text = _entry_text(entry)
        if not text.strip():
            continue
        save_to_mem0(
            text,
            user_id=user_id,
            extra_metadata={"source": "SHARED_BRAIN.json"},
        )
        migrated += 1

    print(f"Migrated {migrated}/{len(entries)} entries to Mem0")
    return 0 if migrated == len(entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
