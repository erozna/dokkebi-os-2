"""Append Day 1 completion summary to SHARED_BRAIN.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TARGET = Path(r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json")


def main() -> int:
    if not TARGET.is_file():
        print(f"Missing {TARGET}")
        return 1

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    entry = {
        "entry_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_day1"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Day1_shared_brain_gateway",
        "actor": "cursor",
        "task_id": "DAY1_20260625",
        "payload": {
            "project": "shared-brain-day1",
            "path": str(ROOT),
            "checks": {
                "api_keys": "ok_via_ALL_CREDENTIALS",
                "venv": "python3.12",
                "litellm_3_models": "ok",
                "mem0_init": "ok",
                "shared_brain_migration": "85/85",
                "fastapi_ping": "ok",
                "docker_compose": "pending_docker_desktop",
                "telegram_ping": "bot_ready_not_verified",
                "github_push": "pending_remote",
            },
        },
    }

    data.setdefault("entries", []).append(entry)
    data["총_항목수"] = len(data["entries"])
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recorded Day 1 entry in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
