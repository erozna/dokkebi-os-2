"""장인 라운드 어댑터 — 헌법 3조 STEP 3 (장인 = Claude Sonnet, Cowork 우선).

기본은 API 모드(Claude Sonnet 직접 호출). use_cowork=True면:
  1. 프롬프트를 handoff/round-N-jangin.md 에 작성
  2. Cowork task 트리거 (현재 자동 트리거 미지원 → 사장님 [D] 수동 안내)
  3. handoff/round-N-jangin.result.md 결과 파일 polling (최대 timeout초)
  4. 타임아웃 시 fallback: Gemini Pro 임시 대체 + 경고 로그
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

from app.config import ROOT
from app.litellm_router import DEBATE_ROLE_FALLBACK, DEBATE_ROLE_MODELS, call_llm

logger = logging.getLogger(__name__)

_PROMPT_PATH = ROOT / "prompts" / "jangin.md"
_HANDOFF_DIR = ROOT / "handoff"
_POLL_INTERVAL = 5.0
_DEFAULT_TIMEOUT = 300.0  # 5분


@dataclass
class JanginResult:
    design: str
    model_used: str
    via: str  # "api" | "cowork" | "fallback"
    raw: str = ""
    usage: dict | None = None


@lru_cache(maxsize=1)
def _system_prompt() -> str:
    if _PROMPT_PATH.is_file():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "당신은 장인입니다. 실행 가능한 구현안을 3~5개 불릿으로 설계하세요. 한국어."


def _round_paths(round_no: int):
    prompt_file = _HANDOFF_DIR / f"round-{round_no}-jangin.md"
    result_file = _HANDOFF_DIR / f"round-{round_no}-jangin.result.md"
    return prompt_file, result_file


def _api_design(user_input: str, *, model: str, max_tokens: int) -> JanginResult:
    text, model_used, usage = call_llm(
        user_input,
        system_prompt=_system_prompt(),
        max_tokens=max_tokens,
        model=model,
        return_usage=True,
    )
    via = "api" if model_used == model else "fallback"
    return JanginResult(design=text, model_used=model_used, via=via, raw=text, usage=usage)


def run_jangin(
    user_input: str,
    *,
    round_no: int = 1,
    use_cowork: bool = False,
    timeout: float = _DEFAULT_TIMEOUT,
    poll_interval: float = _POLL_INTERVAL,
    max_tokens: int = 800,
) -> JanginResult:
    """장인 설계 라운드. use_cowork=False면 Claude Sonnet API 직접 호출."""
    model = DEBATE_ROLE_MODELS["jangin"]

    if not use_cowork:
        return _api_design(user_input, model=model, max_tokens=max_tokens)

    # Cowork 모드: 프롬프트 파일 작성 + 결과 polling
    prompt_file, result_file = _round_paths(round_no)
    _HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(
        f"# 장인 라운드 {round_no} (Cowork)\n\n## 시스템\n{_system_prompt()}\n\n## 입력\n{user_input}\n\n"
        f"> 결과를 `{result_file.name}`에 작성하면 도깨비가 회수합니다.\n",
        encoding="utf-8",
    )
    logger.warning(
        "장인 Cowork 트리거 필요 [D]: 사장님이 Claude Desktop Cowork로 %s 처리 → %s 작성",
        prompt_file.name,
        result_file.name,
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result_file.is_file():
            content = result_file.read_text(encoding="utf-8").strip()
            if content:
                return JanginResult(design=content, model_used="cowork/claude-sonnet", via="cowork", raw=content)
        time.sleep(poll_interval)

    # 타임아웃 → Gemini Pro fallback
    fallback = DEBATE_ROLE_FALLBACK.get("jangin", "gemini/gemini-2.5-pro")
    logger.warning("장인 Cowork 타임아웃(%.0fs) → %s fallback", timeout, fallback)
    res = _api_design(user_input, model=fallback, max_tokens=max_tokens)
    res.via = "fallback"
    return res
