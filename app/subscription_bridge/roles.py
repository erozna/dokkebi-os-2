"""4역할 + Cursor — 구독 채널 매핑."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Channel = Literal["claude_web", "gemini_web", "groq_api", "cursor_ide"]


@dataclass(frozen=True)
class BridgeRole:
    id: str
    label: str
    channel: Channel
    channel_hint: str
    instruction: str


ROUND_ORDER: tuple[str, ...] = ("장인", "심판자", "검사관", "재판장", "cursor")

ROLES: dict[str, BridgeRole] = {
    "장인": BridgeRole(
        id="장인",
        label="장인",
        channel="claude_web",
        channel_hint="Claude 웹/앱 (정액제)",
        instruction=(
            "실용적인 구현안을 제시하세요. 실행 순서, 파일 경로, 리스크. "
            "이모지 금지. 한국어."
        ),
    ),
    "심판자": BridgeRole(
        id="심판자",
        label="심판자",
        channel="gemini_web",
        channel_hint="Gemini 웹 (정액제)",
        instruction=(
            "가상의 심판자(사장님 흉내 금지). 비용·시간·ROI·리스크를 비판하세요. "
            "이모지 금지. 한국어."
        ),
    ),
    "검사관": BridgeRole(
        id="검사관",
        label="검사관",
        channel="gemini_web",
        channel_hint="Gemini 웹 또는 Groq(무료 API)",
        instruction=(
            "pytest 관점 테스트 시나리오·엣지 케이스를 나열하세요. "
            "이모지 금지. 한국어."
        ),
    ),
    "재판장": BridgeRole(
        id="재판장",
        label="재판장",
        channel="claude_web",
        channel_hint="Claude 웹/앱 (정액제)",
        instruction=(
            "앞선 발언을 종합해 실행 가능한 합의안 3~5문장으로 마무리하세요. "
            "이모지 금지. 한국어."
        ),
    ),
    "cursor": BridgeRole(
        id="cursor",
        label="Cursor",
        channel="cursor_ide",
        channel_hint="Cursor Pro — handoff/latest.md @참조",
        instruction=(
            "합의안을 repo에 구현. pytest 통과, 최소 diff. "
            "SHARED_BRAIN·handoff/latest.md 먼저 읽기."
        ),
    ),
}
