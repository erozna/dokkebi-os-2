"""봇 핸들러 실전 검증 — Telegram과 동일 코드 경로."""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials, use_chroma_server
from app.memory_service import format_memory_results, search_memories
from bot.telegram_bot import _parse_memory_args, goal, memory, ping

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "]",
    flags=re.UNICODE,
)


def _mock_update(args: list[str] | None = None) -> tuple[MagicMock, MagicMock]:
    update = MagicMock()
    update.effective_chat.id = 999001
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = args or []
    return update, context


async def _run_all() -> dict:
    ensure_env_from_credentials()
    report: dict = {}

    # 1) /ping
    upd, ctx = _mock_update()
    await ping(upd, ctx)
    ping_text = upd.message.reply_text.await_args.args[0]
    report["ping"] = {
        "ok": ping_text == "pong" and not _EMOJI_RE.search(ping_text),
        "text": ping_text,
    }

    # 2) /goal
    upd, ctx = _mock_update(["Day", "4", "회고", "한", "줄"])
    await goal(upd, ctx)
    goal_text = upd.message.reply_text.await_args.args[0]
    has_korean = bool(re.search(r"[가-힣]", goal_text))
    has_roi = any(k in goal_text for k in ("ROI", "비용", "시간", "절감"))
    report["goal"] = {
        "ok": has_korean and not _EMOJI_RE.search(goal_text) and "[응답]" in goal_text,
        "has_roi_trace": has_roi,
        "preview": goal_text[:400],
    }

    # 3) /memory 헌법
    upd, ctx = _mock_update(["헌법"])
    await memory(upd, ctx)
    mem_text = upd.message.reply_text.await_args.args[0]
    report["memory"] = {
        "ok": "검색" in mem_text or "기억" in mem_text,
        "preview": mem_text[:300],
    }

    # 4) /memory --episodic 헌법
    cat, q = _parse_memory_args(["--episodic", "헌법"])
    assert cat == "episodic" and q == "헌법"
    results = search_memories("헌법", category="episodic", limit=5, use_server=use_chroma_server())
    episodic_msg = format_memory_results(results, category="episodic")
    report["memory_episodic"] = {
        "ok": "없습니다" in episodic_msg or "episodic" in episodic_msg,
        "count": len(results),
        "text": episodic_msg,
    }

    return report


def main() -> int:
    report = asyncio.run(_run_all())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    all_ok = all(
        report[k]["ok"]
        for k in ("ping", "goal", "memory", "memory_episodic")
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
