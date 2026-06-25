"""Mem0 init + first save/search smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials, mem0_config


def main() -> int:
    ensure_env_from_credentials()

    from mem0 import Memory

    memory = Memory.from_config(mem0_config())
    user_id = "dokkebi-day1"

    memory.add("Day 1 Mem0 smoke test: shared brain online.", user_id=user_id)
    results = memory.search("shared brain", filters={"user_id": user_id}, limit=3)

    print("Mem0 init OK")
    print("Search results:", results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
