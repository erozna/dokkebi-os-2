"""텔레그램 봇 — /ping, /memory."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials, use_chroma_server
from app.memory_service import format_memory_results, search_memories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """헬스체크."""
    await update.message.reply_text("pong 🐺")


async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mem0 기억 검색."""
    query = " ".join(context.args).strip() if context.args else ""
    if not query:
        await update.message.reply_text("사용법: /memory <검색어>\n예) /memory 헌법")
        return

    try:
        results = search_memories(
            query,
            limit=5,
            use_server=use_chroma_server(),
        )
        message = format_memory_results(results)
        await update.message.reply_text(message)
    except Exception as exc:  # noqa: BLE001 — 사용자에게 오류 전달
        logger.exception("memory 검색 실패")
        await update.message.reply_text(f"검색 중 오류: {exc}")


def main() -> None:
    """폴링 봇 기동."""
    ensure_env_from_credentials()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("memory", memory))
    logger.info("Telegram bot polling started (/ping, /memory)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
