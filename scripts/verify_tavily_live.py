"""Tavily 실호출 1회 검증 (Day 6 마감)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.pop("CI", None)

from app.tools.web_search import WebSearchError, search_web  # noqa: E402


def main() -> int:
    if not os.environ.get("TAVILY_API_KEY", "").strip():
        print(json.dumps({"ok": False, "error": "TAVILY_API_KEY missing"}, ensure_ascii=False))
        return 1
    try:
        data = search_web("AI news 2026", max_results=3)
        out = {
            "ok": True,
            "result_count": len(data.get("results") or []),
            "has_answer": bool(data.get("answer")),
            "first_title": (data.get("results") or [{}])[0].get("title", ""),
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0 if out["result_count"] > 0 or out["has_answer"] else 1
    except WebSearchError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
