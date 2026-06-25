"""텔레그램 봇 — /ping, /memory, /goal."""

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
from app.supervisor import run_supervisor

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
    except Exception as exc:  # noqa: BLE001
        logger.exception("memory 검색 실패")
        await update.message.reply_text(f"검색 중 오류: {exc}")


async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Supervisor LangGraph 파이프라인 실행."""
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text("사용법: /goal <한국어 목표>\n예) /goal 오늘 날씨 알려줘")
        return

    chat_id = str(update.effective_chat.id) if update.effective_chat else "telegram"
    try:
        result = run_supervisor(text, thread_id=f"tg-{chat_id}")
        await update.message.reply_text(result.get("response") or "응답 없음")
    except Exception as exc:  # noqa: BLE001
        logger.exception("/goal 실패")
        await update.message.reply_text(f"처리 중 오류: {exc}")


def main() -> None:
    """폴링 봇 기동."""
    ensure_env_from_credentials()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("memory", memory))
    app.add_handler(CommandHandler("goal", goal))
    logger.info("Telegram bot polling started (/ping, /memory, /goal)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
