"""텔레그램 봇 — /ping, /memory, /goal, /debate, /bridge."""

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
from app.routers.crew_debate import run_debate
from app.routers.dod_designer import design_dod
from app.routers.intent_extractor import extract_intent
from app.subscription_bridge import bridge_ingest, bridge_next, bridge_prep, bridge_status
from app.supervisor import run_supervisor

_MEMORY_CATEGORIES = frozenset({"episodic", "semantic", "procedural", "preference"})


def _parse_memory_args(args: list[str]) -> tuple[str | None, str]:
    """--episodic 등 카테고리 플래그와 검색어 분리."""
    if not args:
        return None, ""
    category: str | None = None
    rest = list(args)
    if rest[0].startswith("--"):
        flag = rest[0].lstrip("-").lower()
        if flag in _MEMORY_CATEGORIES:
            category = flag
            rest = rest[1:]
    elif rest[0].lower() in _MEMORY_CATEGORIES:
        category = rest[0].lower()
        rest = rest[1:]
    return category, " ".join(rest).strip()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """헬스체크."""
    await update.message.reply_text("pong")


async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mem0 기억 검색."""
    category, query = _parse_memory_args(list(context.args or []))
    if not query:
        await update.message.reply_text(
            "사용법: /memory <검색어>\n"
            "       /memory --episodic <검색어>\n"
            "예) /memory 헌법\n"
            "예) /memory --semantic 선호"
        )
        return

    try:
        results = search_memories(
            query,
            category=category,
            limit=5,
            use_server=use_chroma_server(),
        )
        message = format_memory_results(results, category=category)
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


async def debate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intent → DoD → 4역할 토론 → Red Team 한방 (헌법 3조 STEP 1·2·3·5)."""
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "사용법: /debate <문장>\n예) /debate 유튜브 수익 검증 엔진 만들어줘"
        )
        return

    await update.message.reply_text("4역할 토론 진행 중… (장인→심판자→검사관→재판장, 약 1분)")
    try:
        intent_result = extract_intent(text)
        dod_result = design_dod(intent_result, red_team=False)  # 토론에서 Red Team 일괄 실행
        result = run_debate(intent_result, dod_result, with_red_team=True, log_dialogue=True)
    except Exception as exc:  # noqa: BLE001
        logger.exception("/debate 실패")
        await update.message.reply_text(f"토론 중 오류: {exc}")
        return

    consensus = "\n".join(f"  {i}. {c}" for i, c in enumerate(result.consensus, 1)) or "  - (없음)"
    lines = [
        "[4역할 토론 합의안 — 헌법 3조 STEP 3]",
        f"진짜 의도: {intent_result.true_intent or '-'}",
        "최종 완료조건:",
        consensus,
        f"확신도: {result.confidence:.2f}  비용: ${result.total_usd:.4f}",
        f"[모델] 장인 {result.models_used.get('jangin','-')} / 심판자 {result.models_used.get('simpanja','-')}"
        f" / 검사관 {result.models_used.get('geomsakwan','-')} / 재판장 {result.models_used.get('jaepanjang','-')}",
    ]

    rt = result.red_team
    if rt is not None:
        lines.append("")
        lines.append("[Red Team Pass — STEP 5]")
        if rt.failure_reasons:
            lines.append("6개월 후 실패 이유:")
            lines.extend(f"  - {r}" for r in rt.failure_reasons[:3])
        lines.append(
            f"모델 다양성: {rt.diversity_score:.2f}"
            + (f"  ⚠ {rt.diversity_warning}" if rt.diversity_warning else "")
        )

    if result.needs_confirmation:
        lines.append("")
        if rt is not None and rt.needs_user_intuition:
            lines.append(rt.user_question)
        else:
            lines.append("확신도/완료조건 미확정. 사장님 확인 요청: 위 합의안이 맞습니까? (예/아니오)")
    await update.message.reply_text("\n".join(lines)[:4000])


async def intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intent Extractor — 표면/진짜/제약 4분리 (헌법 3조 STEP 1)."""
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "사용법: /intent <문장>\n예) /intent 유튜브 엔진 만들어줘"
        )
        return

    try:
        result = extract_intent(text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("/intent 실패")
        await update.message.reply_text(f"의도 추출 오류: {exc}")
        return

    constraints = "\n".join(f"  - {c}" for c in result.hidden_constraints) or "  - (없음)"
    lines = [
        "[의도 추출]",
        f"표면 목표: {result.surface_goal or '-'}",
        f"진짜 의도: {result.true_intent or '-'}",
        "숨은 제약:",
        constraints,
        f"근거: {result.reasoning or '-'}",
        f"확신도: {result.confidence:.2f}  [모델] {result.model_used or '-'}",
    ]
    if result.needs_confirmation:
        lines.append("")
        lines.append("확신도가 낮습니다(<0.7). 사장님 확인 요청: 위 진짜 의도가 맞습니까? (예/아니오)")
    await update.message.reply_text("\n".join(lines)[:4000])


async def dod(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intent → DoD 파이프라인 (헌법 3조 STEP 1→2). 정량 완료조건 산출."""
    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "사용법: /dod <문장>\n예) /dod 유튜브 엔진 만들어줘"
        )
        return

    try:
        intent_result = extract_intent(text)
        dod_result = design_dod(intent_result, red_team=True)  # STEP 5 Red Team 포함
    except Exception as exc:  # noqa: BLE001
        logger.exception("/dod 실패")
        await update.message.reply_text(f"DoD 설계 오류: {exc}")
        return

    criteria = "\n".join(f"  {i}. {c}" for i, c in enumerate(dod_result.criteria, 1)) or "  - (없음)"
    lines = [
        "[완료조건 DoD]",
        f"진짜 의도: {intent_result.true_intent or '-'}",
        "완료조건:",
        criteria,
        f"근거: {dod_result.reasoning or '-'}",
        f"측정가능: {'예' if dod_result.measurable else '아니오'}  확신도: {dod_result.confidence:.2f}",
        f"[모델] {dod_result.model_used or '-'}",
    ]

    rt = dod_result.red_team
    if rt is not None:
        lines.append("")
        lines.append("[Red Team Pass — 헌법 3조 STEP 5]")
        if rt.failure_reasons:
            lines.append("6개월 후 실패 이유:")
            lines.extend(f"  - {r}" for r in rt.failure_reasons[:3])
        lines.append(
            f"모델 다양성: {rt.diversity_score:.2f}"
            + (f"  ⚠ {rt.diversity_warning}" if rt.diversity_warning else "")
        )

    if intent_result.needs_confirmation or dod_result.needs_confirmation:
        lines.append("")
        if rt is not None and rt.needs_user_intuition:
            lines.append(rt.user_question)
        else:
            lines.append(
                "확신도 부족 또는 완료조건 미확정. 사장님 확인 요청: 위 완료조건이 맞습니까? (예/아니오)"
            )
    await update.message.reply_text("\n".join(lines)[:4000])


def _format_bridge_prep(result: dict) -> str:
    return (
        f"[Bridge prep]\n"
        f"주제: {result.get('topic')}\n"
        f"역할: {result.get('role')} → {result.get('channel_hint')}\n"
        f"파일: {result.get('outbox_file')}\n\n"
        f"--- 붙여넣기 프롬프트 (앞 1500자) ---\n"
        f"{(result.get('prompt_preview') or '')[:1500]}\n\n"
        f"답변 후: /bridge ingest <답변>"
    )


def _format_bridge_next(result: dict) -> str:
    if result.get("done"):
        return (
            f"[Bridge 완료]\n"
            f"{result.get('message', '')}\n"
            f"latest: {result.get('latest_path', 'handoff/bridge/latest.md')}"
        )
    return (
        f"[Bridge round {result.get('round')}]\n"
        f"역할: {result.get('role')} → {result.get('channel_hint')}\n"
        f"파일: {result.get('outbox_file')}\n\n"
        f"{(result.get('prompt_preview') or '')[:1500]}\n\n"
        f"답변 후: /bridge ingest <답변>"
    )


async def bridge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscription Bridge — 정액제 웹 핸드오프."""
    args = list(context.args or [])
    if not args:
        await update.message.reply_text(
            "사용법:\n"
            "/bridge prep <주제>\n"
            "/bridge status\n"
            "/bridge next\n"
            "/bridge ingest <웹 UI 답변 전체>\n\n"
            "docs/SUBSCRIPTION_BRIDGE.md 참고"
        )
        return

    sub = args[0].lower()
    rest = " ".join(args[1:]).strip()
    chat_id = str(update.effective_chat.id) if update.effective_chat else "telegram"
    thread_id = f"tg-bridge-{chat_id}"

    try:
        if sub == "prep":
            if not rest:
                await update.message.reply_text("사용법: /bridge prep <주제>")
                return
            result = bridge_prep(rest, thread_id=thread_id)
            await update.message.reply_text(_format_bridge_prep(result))
            return

        if sub == "status":
            st = bridge_status()
            if not st.get("active"):
                await update.message.reply_text(st.get("message", "세션 없음"))
                return
            await update.message.reply_text(
                f"주제: {st.get('topic')}\n"
                f"진행: {st.get('current_index')}/{st.get('total_rounds')}\n"
                f"다음 역할: {st.get('next_role')}\n"
                f"outbox: {st.get('current_outbox')}"
            )
            return

        if sub == "next":
            result = bridge_next()
            await update.message.reply_text(_format_bridge_next(result))
            return

        if sub == "ingest":
            if not rest:
                await update.message.reply_text("사용법: /bridge ingest <Claude/Gemini 답변>")
                return
            result = bridge_ingest(rest, thread_id=thread_id)
            lines = [
                f"저장: {result.get('ingested_role')}",
                f"inbox: {result.get('inbox_file')}",
            ]
            nxt = result.get("next")
            if isinstance(nxt, dict):
                lines.append("")
                lines.append(_format_bridge_next(nxt))
            await update.message.reply_text("\n".join(lines)[:4000])
            return

        await update.message.reply_text("알 수 없는 subcommand. /bridge 만 입력해 도움말.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("/bridge 실패")
        await update.message.reply_text(f"Bridge 오류: {exc}")


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
    app.add_handler(CommandHandler("debate", debate))
    app.add_handler(CommandHandler("intent", intent))
    app.add_handler(CommandHandler("dod", dod))
    app.add_handler(CommandHandler("bridge", bridge))
    logger.info(
        "Telegram bot polling started (/ping, /memory, /goal, /debate, /intent, /dod, /bridge)"
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
