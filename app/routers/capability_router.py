"""Capability Router — 헌법 3조 STEP 6 / 4조 5-Way 분류.

작업(task_spec)을 [A]Auto / [B]Bridge / [C]Ask / [D]Hands / [E]Background로 분류.
v1은 룰 기반(명시 플래그 우선 → 키워드 휴리스틱 → 기본 [A]). LLM 분류는 v2.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import ROOT

logger = logging.getLogger(__name__)

_DIALOGUE_PATH = ROOT / "handoff" / "dialogue.md"

# [D] 자동화 불가 — 사장님 손 (외부 권한/수동)
_HANDS_KW = (
    "oauth", "회원가입", "가입", "캡차", "captcha", "결제", "구독 결제",
    "로그인", "login", "인증서", "2fa", "본인인증", "휴대폰 인증", "카드 등록",
)
# [C] 가치 판단 필요 — 사장님 결정
_ASK_KW = (
    "할까", "선택", "결정", "도입할지", "어떤 모델", "which", "decide",
    "판단", "방향", "우선순위 정", "골라",
)
# [E] 반복적/백그라운드 — 즉시 응답 불필요
_BG_KW = (
    "매주", "매일", "매월", "정기", "주기적", "스케줄", "scheduled",
    "모니터링", "monitor", "자동 백업", "백그라운드", "watch",
)
# [B] 정액제 웹으로 비용 0 가능 — 복붙 브리지
_BRIDGE_KW = (
    "요약", "글쓰기", "카피", "초안", "번역", "브레인스토밍", "아이디어",
    "기획안", "리서치 요약", "장문 작성", "에세이",
)
# [A] 자동화 가능 — 도깨비 자동
_AUTO_KW = (
    "yt-dlp", "api", "pytest", "테스트", "스크립트", "크롤", "수집",
    "쿼리", "query", "코드", "함수", "파싱", "다운로드", "변환", "계산",
)

_BRIDGE_DEFAULT_CHANNEL = "Claude.ai (정액제)"


@dataclass
class RouteDecision:
    """5-Way 분류 결정."""

    route: str  # 'A'|'B'|'C'|'D'|'E'
    reason: str
    task: str = ""
    target_channel: str = ""
    prompt_or_action: str = ""


def _norm_spec(task_spec: dict | str) -> dict:
    if isinstance(task_spec, str):
        return {"task": task_spec}
    return dict(task_spec or {})


def _hit(text: str, keywords: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(kw in low for kw in keywords)


def classify(task_spec: dict | str) -> RouteDecision:
    """작업을 5-Way로 분류. 명시 플래그 우선, 없으면 키워드 휴리스틱, 기본 [A]."""
    spec = _norm_spec(task_spec)
    task = str(spec.get("task", "")).strip()

    # 1) [D] Hands — 외부 권한/수동 (자동화 불가). 최우선 차단.
    if spec.get("needs_external_auth") or _hit(task, _HANDS_KW):
        return RouteDecision(
            route="D",
            reason="외부 권한/수동 절차 필요 — 자동화 불가, 사장님 손",
            task=task,
            target_channel="telegram-queue",
            prompt_or_action=task,
        )

    # 2) [C] Ask — 가치 판단
    if spec.get("value_judgment") or _hit(task, _ASK_KW):
        return RouteDecision(
            route="C",
            reason="가치 판단 필요 — 사장님 결정",
            task=task,
            target_channel="telegram",
            prompt_or_action=f"사장님 결정 요청: {task}",
        )

    # 3) [E] Background — 반복적/즉시 응답 불필요
    if spec.get("repetitive") or _hit(task, _BG_KW):
        return RouteDecision(
            route="E",
            reason="반복적/즉시 응답 불필요 — 백그라운드 위임",
            task=task,
            target_channel="cowork",
            prompt_or_action=task,
        )

    # 4) [B] Bridge — 정액제 웹 활용 비용 0
    if spec.get("subscription_capable") or _hit(task, _BRIDGE_KW):
        return RouteDecision(
            route="B",
            reason="정액제 웹으로 비용 0 가능 — 복붙 브리지",
            task=task,
            target_channel=str(spec.get("channel") or _BRIDGE_DEFAULT_CHANNEL),
            prompt_or_action=task,
        )

    # 5) [A] Auto — 기본 (자동화 가능)
    return RouteDecision(
        route="A",
        reason="자동화 가능 + 권한 충돌 없음 — 도깨비 자동",
        task=task,
        target_channel="local",
        prompt_or_action=task,
    )


def append_decision_log(decisions: list[RouteDecision]) -> None:
    """분류 결정을 dialogue.md에 1블록 append."""
    if not decisions:
        return
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {stamp} [ROUTER] 5-Way 분류 {len(decisions)}건"]
    for d in decisions:
        lines.append(f"- [{d.route}] {d.task[:80]} — {d.reason}")
    with _DIALOGUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
