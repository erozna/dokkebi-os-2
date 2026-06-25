"""페르소나·이모지 금지 시스템 프롬프트 테스트."""

from __future__ import annotations

import re
from unittest.mock import patch

from app.prompts import build_system_prompt
from app.supervisor import output_formatter, reasoner

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "]",
    flags=re.UNICODE,
)


def test_system_prompt_no_emoji_and_korean_persona():
    """이모지 없음 + 한국어 페르소나 핵심 문구 포함."""
    prompt = build_system_prompt("default")
    assert not _EMOJI_RE.search(prompt)
    assert "사장님" in prompt or "효남금속" in prompt
    assert "이모지" in prompt and "금지" in prompt
    assert "한국어" in prompt


def test_intent_branch_in_system_prompt():
    """의도별 분기 문자열 존재."""
    code_prompt = build_system_prompt("code")
    summary_prompt = build_system_prompt("summary")
    assert "코드" in code_prompt
    assert "요약" in summary_prompt
    assert code_prompt != summary_prompt


def test_reasoner_passes_system_prompt():
    """reasoner가 build_system_prompt를 call_llm에 전달."""
    state = {"input": "파이썬 함수 작성", "intent": "code", "thread_id": "persona-test"}

    with patch("app.supervisor.call_llm") as mocked:
        mocked.return_value = ("ok", "anthropic/claude-sonnet-4-6")
        reasoner(state)
        assert mocked.called
        _, kwargs = mocked.call_args
        sp = kwargs.get("system_prompt") or ""
        assert sp
        assert not _EMOJI_RE.search(sp)
        assert "이모지" in sp


def test_output_formatter_no_emoji():
    """output_formatter 응답에 이모지 없음."""
    out = output_formatter(
        {
            "response": "테스트 본문",
            "memory_id": "mid-1",
            "model_used": "anthropic/claude-sonnet-4-6",
            "elapsed_sec": 1.2,
        }
    )
    text = out["response"]
    assert not _EMOJI_RE.search(text)
    assert "[응답]" in text
    assert "[메모리]" in text
    assert "[모델]" in text
    assert "[시간]" in text
