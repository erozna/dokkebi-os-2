"""Executor — 헌법 3조 STEP 7. RouteDecision 실제 실행.

[A] Auto: 화이트리스트 4종(yt-dlp/Tavily/ChromaDB/pytest) 실제 실행 (live=True 시).
[B] Bridge: handoff/bridge-{ts}.md 작성 + 클립보드 자동 복사 → 사장님 [D] 안내
[C] Ask: 텔레그램 능동 질문 반환 (polling은 봇/오케스트레이터)
[D] Hands: handoff/queue.md 작업 큐 append → 사장님 완료 신호 대기
[E] Background: handoff/cowork/{task_id}.md 작성 → Cowork 위임 (자동 트리거 v2)

안전: 외부 실행(yt-dlp/Tavily/클립보드)은 live=True 일 때만. 기본은 계획만 반환.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from app.config import ROOT
from app.routers.capability_router import RouteDecision
from app.tools.whitelist import is_whitelisted, run_whitelisted

logger = logging.getLogger(__name__)

_HANDOFF = ROOT / "handoff"
_BRIDGE_DIR = _HANDOFF
_COWORK_DIR = _HANDOFF / "cowork"
_QUEUE_PATH = _HANDOFF / "queue.md"
_DIALOGUE_PATH = _HANDOFF / "dialogue.md"

_URL_RE = re.compile(r"https?://[^\s]+")


@dataclass
class ExecutionResult:
    """실행 결과."""

    route: str
    status: str  # 'done'|'pending'|'queued'|'delegated'|'error'
    detail: str = ""
    artifact_path: str = ""
    question: str = ""
    tool: str = ""


def _slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-")
    return (s[:n] or "task").lower()


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _detect_tool(text: str) -> tuple[str, str]:
    """[A] 작업 텍스트 → (화이트리스트 도구, 인자). 기본은 Tavily 분석."""
    low = (text or "").lower()
    url_match = _URL_RE.search(text or "")
    if url_match and ("youtube.com" in low or "youtu.be" in low):
        return "yt-dlp", url_match.group(0)
    if "pytest" in low or "테스트 실행" in low or "회귀" in low:
        return "pytest", ""
    if any(k in low for k in ("과거", "관심사", "기억", "chroma", "메모리")):
        return "chromadb", text
    # 기본: 웹 검색으로 '분석/발견' (사장님 진짜 그림의 핵심)
    return "tavily", text


def _execute_auto(d: RouteDecision, *, live: bool) -> ExecutionResult:
    tool, arg = _detect_tool(d.prompt_or_action or d.task)
    if not is_whitelisted(tool):
        return ExecutionResult(
            route="A", status="pending", tool=tool,
            detail=f"화이트리스트 외 — [C] 사장님 결정 필요: {d.task[:100]}",
        )
    if not live:
        return ExecutionResult(
            route="A", status="pending", tool=tool,
            detail=f"자동 실행 후보({tool}, live=False 미실행): {d.task[:100]}",
        )
    res = run_whitelisted(tool, arg)
    return ExecutionResult(
        route="A",
        status="done" if res.ok else "error",
        tool=tool,
        detail=(res.summary if res.ok else f"{tool} 실패: {res.error}")[:200],
        artifact_path=res.artifact_path,
    )


def _copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("클립보드 복사 실패: %s", exc)
        return False


def _execute_bridge(d: RouteDecision, *, live: bool) -> ExecutionResult:
    _BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = _BRIDGE_DIR / f"bridge-{_ts()}.md"
    body = (
        f"# Bridge 작업 ([B]) — {d.target_channel}\n\n"
        f"## 작업\n{d.task}\n\n"
        f"## 추천 채널\n{d.target_channel}\n\n"
        f"## 복붙 프롬프트\n{d.prompt_or_action}\n\n"
        f"> 웹 UI 답변을 받은 뒤 `/bridge ingest <답변>` 또는 다음 단계로.\n"
    )
    path.write_text(body, encoding="utf-8")
    copied = _copy_to_clipboard(d.prompt_or_action or body) if live else False
    detail = f"복붙 프롬프트 작성 → {d.target_channel}."
    if copied:
        detail += " 📋 클립보드 복사 완료 — Claude.ai 탭에서 Ctrl+V → Enter."
    else:
        detail += " 사장님 [D] 복붙 안내 필요."
    return ExecutionResult(route="B", status="pending", detail=detail, artifact_path=str(path))


def _execute_ask(d: RouteDecision, *, live: bool) -> ExecutionResult:
    return ExecutionResult(
        route="C",
        status="pending",
        detail="사장님 능동 질문 — 텔레그램 응답 대기",
        question=d.prompt_or_action,
    )


def _execute_hands(d: RouteDecision, *, live: bool) -> ExecutionResult:
    _HANDOFF.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _QUEUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"- [ ] {stamp} [D] {d.task} — {d.reason}\n")
    return ExecutionResult(
        route="D",
        status="queued",
        detail="사장님 손 작업 큐 등록 — 완료 신호 대기",
        artifact_path=str(_QUEUE_PATH),
    )


def _execute_background(d: RouteDecision, *, live: bool) -> ExecutionResult:
    _COWORK_DIR.mkdir(parents=True, exist_ok=True)
    task_id = f"{_ts()}-{_slug(d.task)}"
    path = _COWORK_DIR / f"{task_id}.md"
    path.write_text(
        f"# Cowork 위임 작업 ([E]) — {task_id}\n\n"
        f"## 작업\n{d.task}\n\n## 사유\n{d.reason}\n\n"
        f"> Cowork 자동 트리거 미구현(v2) → 사장님 [D]로 Cowork 수동 실행 안내.\n",
        encoding="utf-8",
    )
    return ExecutionResult(
        route="E",
        status="delegated",
        detail=f"Cowork 위임 파일 작성({task_id}). 자동 트리거 v2 — 현재 [D] 안내.",
        artifact_path=str(path),
    )


_DISPATCH = {
    "A": _execute_auto,
    "B": _execute_bridge,
    "C": _execute_ask,
    "D": _execute_hands,
    "E": _execute_background,
}


def execute(decision: RouteDecision, *, live: bool = False) -> ExecutionResult:
    """분류 결정 1건 실행. live=True 일 때만 외부 실행(yt-dlp/Tavily/클립보드)."""
    handler = _DISPATCH.get(decision.route)
    if handler is None:
        return ExecutionResult(route=decision.route, status="error", detail="알 수 없는 분류")
    try:
        return handler(decision, live=live)
    except Exception as exc:  # noqa: BLE001
        logger.exception("executor 실패: %s", decision.route)
        return ExecutionResult(route=decision.route, status="error", detail=str(exc))


def append_execution_log(results: list[ExecutionResult]) -> None:
    if not results:
        return
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {stamp} [EXECUTOR] 실행 {len(results)}건"]
    for r in results:
        lines.append(f"- [{r.route}] {r.status} — {r.detail[:100]}")
    with _DIALOGUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
