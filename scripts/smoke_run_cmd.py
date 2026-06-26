"""봇 /run 명령 smoke test (mock, live 호출 없음). 텔레그램 발송 양식 점검용."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import bot.telegram_bot as tb
from app.routers.canonical_flow import FlowResult

_STEPS = [
    ("Mission Memory", "헌법 2조 로드"),
    ("Intent Extractor", "진짜 의도: 수동 검색 시간 0화"),
    ("DoD Auto-Designer", "완료조건 4개"),
    ("CrewAI 토론", "합의안 4개 conf 0.85"),
    ("Tech Radar", "후보 3건 (스켈레톤)"),
    ("Red Team", "다양성 1.00"),
    ("Capability Router", "분류 {'A':3,'C':1}"),
    ("Execution", "실행 4건"),
    ("Usage Doc", "640자"),
    ("Mission Memory", "SHARED_BRAIN 저장"),
]


def _fake_flow() -> FlowResult:
    fr = FlowResult(user_input="테스트 작업")
    fr.steps = [
        {"step": i, "name": n, "status": "done", "summary": s}
        for i, (n, s) in enumerate(_STEPS)
    ]
    fr.questions = ["재판장 모델 교체할까요? (예/아니오)"]
    fr.usage_doc = (
        "# 도깨비 작업 결과\n\n**진짜 의도:** 수동 검색 시간 0화\n\n"
        "## 합의된 완료조건\n1. 주 50건 수집\n2. 사기필터 80%\n\n_비용: $0.0110_"
    )
    return fr


class _Msg:
    def __init__(self):
        self.sent: list[str] = []

    async def reply_text(self, text):  # noqa: ANN001
        self.sent.append(text)


class _Upd:
    def __init__(self):
        self.message = _Msg()


def main() -> None:
    upd = _Upd()
    ctx = MagicMock()
    ctx.args = ["테스트", "작업"]
    with patch("bot.telegram_bot.run_canonical_flow", return_value=_fake_flow()):
        asyncio.run(tb.run(upd, ctx))
    print(f"=== 텔레그램 발송 메시지 {len(upd.message.sent)}건 ===")
    for i, m in enumerate(upd.message.sent, 1):
        print(f"\n--- 메시지 {i} ---\n{m}")


if __name__ == "__main__":
    main()
