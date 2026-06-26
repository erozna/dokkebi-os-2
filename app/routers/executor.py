"""Executor — 헌법 3조 STEP 7. RouteDecision 실제 실행.

[A] Auto: 화이트리스트 검증 후 실행 (v1은 계획만 반환, 임의 subprocess 금지)
[B] Bridge: handoff/bridge-{ts}.md 작성 → 사장님 복붙 [D] 안내
[C] Ask: 텔레그램 능동 질문 반환 (polling은 봇/오케스트레이터)
[D] Hands: handoff/queue.md 작업 큐 append → 사장님 완료 신호 대기
[E] Background: handoff/cowork/{task_id}.md 작성 → Cowork 위임 (자동 트리거 v2)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from app.config import ROOT
from app.routers.capability_router import RouteDecision

logger = logging.getLogger(__name__)

_HANDOFF = ROOT / "handoff"
_BRIDGE_DIR = _HANDOFF
_COWORK_DIR = _HANDOFF / "cowork"
_QUEUE_PATH = _HANDOFF / "queue.md"
_DIALOGUE_PATH = _HANDOFF / "dialogue.md"


@dataclass
class ExecutionResult:
    """실행 결과."""

    route: str
    status: str  # 'done'|'pending'|'queued'|'delegated'|'error'
    detail: str = ""
    artifact_path: str = ""
    question: str = ""


def _slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "-", text).strip("-")
    return (s[:n] or "task").lower()


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _execute_auto(d: RouteDecision) -> ExecutionResult:
    # v1: 임의 명령 실행 금지(보안). 자동 실행 후보로 계획만 반환.
    return ExecutionResult(
        route="A",
        status="pending",
        detail=f"자동 실행 후보(화이트리스트 검증 후 실행, v1 미실행): {d.prompt_or_action[:120]}",
    )


def _execute_bridge(d: RouteDecision) -> ExecutionResult:
    _BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = _BRIDGE_DIR / f"bridge-{_ts()}.md"
    path.write_text(
        f"# Bridge 작업 ([B]) — {d.target_channel}\n\n"
        f"## 작업\n{d.task}\n\n"
        f"## 추천 채널\n{d.target_channel}\n\n"
        f"## 복붙 프롬프트\n{d.prompt_or_action}\n\n"
        f"> 웹 UI 답변을 받은 뒤 `/bridge ingest <답변>` 또는 다음 단계로.\n",
        encoding="utf-8",
    )
    return ExecutionResult(
        route="B",
        status="pending",
        detail=f"복붙 프롬프트 작성 → {d.target_channel}. 사장님 [D] 안내 필요.",
        artifact_path=str(path),
    )


def _execute_ask(d: RouteDecision) -> ExecutionResult:
    return ExecutionResult(
        route="C",
        status="pending",
        detail="사장님 능동 질문 — 텔레그램 응답 대기",
        question=d.prompt_or_action,
    )


def _execute_hands(d: RouteDecision) -> ExecutionResult:
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


def _execute_background(d: RouteDecision) -> ExecutionResult:
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


def execute(decision: RouteDecision) -> ExecutionResult:
    """분류 결정 1건 실행."""
    handler = _DISPATCH.get(decision.route)
    if handler is None:
        return ExecutionResult(route=decision.route, status="error", detail="알 수 없는 분류")
    try:
        return handler(decision)
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
