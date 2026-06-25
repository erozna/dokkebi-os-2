"""CLI: Subscription Bridge 다음 라운드."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.subscription_bridge import bridge_next, bridge_status  # noqa: E402


def main() -> int:
    status = bridge_status()
    if not status.get("active"):
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 1
    result = bridge_next()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
