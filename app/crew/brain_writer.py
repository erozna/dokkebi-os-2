"""합의안 → SHARED_BRAIN entries 기록."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import ROOT, SHARED_BRAIN_SOURCES

PROJECT_COPY = ROOT / "SHARED_BRAIN.json"


def _targets() -> list[Path]:
    paths: list[Path] = []
    if PROJECT_COPY.is_file():
        paths.append(PROJECT_COPY)
    for path in SHARED_BRAIN_SOURCES:
        if path.is_file() and path not in paths:
            paths.append(path)
    return paths


def record_consensus(
    topic: str,
    consensus: str,
    *,
    transcript: str = "",
    source: str = "crew_debate",
) -> str:
    """entries에 합의안 추가. entry_id 반환."""
    ts = datetime.now(timezone.utc).isoformat()
    entry_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_crew_consensus")
    entry = {
        "entry_id": entry_id,
        "timestamp": ts,
        "action": "CrewAI_합의안",
        "actor": "cursor",
        "task_id": "WEEK2_CREW",
        "payload": {
            "topic": topic,
            "consensus": consensus,
            "transcript_excerpt": (transcript or "")[:2000],
            "source": source,
        },
    }

    for path in _targets():
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("entries", []).append(entry)
        if "총_항목수" in data:
            data["총_항목수"] = len(data["entries"])
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return entry_id
