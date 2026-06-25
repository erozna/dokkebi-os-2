"""Day 2 완료 요약을 SHARED_BRAIN.json에 기록."""

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
        "entry_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_day2"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Day2_chroma_server_mem0_router",
        "actor": "cursor",
        "task_id": "DAY2_20260625",
        "payload": {
            "project": "shared-brain-day1",
            "path": str(ROOT),
            "checks": {
                "docker_compose": "ok",
                "chroma_local_to_server": "173건 무손실",
                "mem0_router": "ok",
                "telegram_memory": "ok",
                "reboot_test": "ok",
                "github_push": "pending_remote_url",
            },
        },
    }

    data.setdefault("entries", []).append(entry)
    data["총_항목수"] = len(data["entries"])
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recorded Day 2 entry in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
