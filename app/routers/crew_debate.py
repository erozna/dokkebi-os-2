"""CrewAI 4역할 토론 본 구현 — 헌법 3조 STEP 3.

장인(설계) → 심판자(약점) → 검사관(실현성) → 재판장(합의) 순차 호출.
각 라운드 결과를 다음 라운드 컨텍스트로 전달하고 dialogue.md에 append.
합의안 도출 직후 STEP 5 Red Team Pass 자동 호출 — 강제 단계 누락 시 최대 2회 재시작.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from app.config import ROOT
from app.litellm_router import DEBATE_ROLE_FALLBACK, DEBATE_ROLE_MODELS, call_llm
from app.routers.dod_designer import DoDResult
from app.routers.intent_extractor import IntentResult, _parse_json
from app.routers.jangin_via_cowork import run_jangin
from app.routers.red_team import RedTeamResult, run_red_team_pass

logger = logging.getLogger(__name__)

_PROMPT_DIR = ROOT / "prompts"
_DIALOGUE_PATH = ROOT / "handoff" / "dialogue.md"
_DEFAULT_THRESHOLD = 0.7
_MAX_RESTARTS = 2
_ROLE_TAG = {
    "jangin": "JANGIN",
    "simpanja": "SIMPANJA",
    "geomsakwan": "GEOMSAKWAN",
    "jaepanjang": "JAEPANJANG",
}


@dataclass
class DebateResult:
    jangin: str = ""
    simpanja: str = ""
    geomsakwan: str = ""
    jaepanjang: str = ""
    consensus: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    needs_confirmation: bool = True
    rounds: list[dict] = field(default_factory=list)
    models_used: dict[str, str] = field(default_factory=dict)
    red_team: RedTeamResult | None = None
    restarts: int = 0
    total_usd: float = 0.0


@lru_cache(maxsize=8)
def _prompt(role: str) -> str:
    path = _PROMPT_DIR / f"{role}.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"당신은 {role}입니다. 한국어로 간결히 답하세요."


def _append_dialogue(role: str, content: str) -> None:
    """라운드 결과를 dialogue.md에 append (## YYYY-MM-DD HH:MM [ROLE])."""
    tag = _ROLE_TAG.get(role, role.upper())
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = f"\n## {stamp} [{tag}]\n{content.strip()[:1500]}\n"
    with _DIALOGUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(block)


def _call_role(role: str, user_input: str, *, max_tokens: int = 800) -> tuple[str, str, dict]:
    text, model_used, usage = call_llm(
        user_input,
        system_prompt=_prompt(role),
        max_tokens=max_tokens,
        model=DEBATE_ROLE_MODELS[role],
        fallback=DEBATE_ROLE_FALLBACK.get(role),
        return_usage=True,
    )
    return text, model_used, usage


def _brief(intent: IntentResult, dod: DoDResult) -> str:
    crit = "\n".join(f"- {c}" for c in dod.criteria) or "- (없음)"
    return (
        f"[진짜 의도] {intent.true_intent}\n"
        f"[숨은 제약] {', '.join(intent.hidden_constraints) or '없음'}\n"
        f"[완료조건 DoD]\n{crit}"
    )


def _run_once(
    intent: IntentResult,
    dod: DoDResult,
    *,
    use_cowork: bool,
    log_dialogue: bool,
    max_tokens: int,
) -> DebateResult:
    result = DebateResult()
    brief = _brief(intent, dod)

    # 1) 장인 — 설계 (Cowork 우선)
    jangin = run_jangin(brief, round_no=1, use_cowork=use_cowork, max_tokens=max_tokens)
    result.jangin = jangin.design
    result.models_used["jangin"] = jangin.model_used
    if jangin.usage:
        result.total_usd += float(jangin.usage.get("usd", 0))
    result.rounds.append({
        "role": "jangin", "model": jangin.model_used, "content": jangin.design,
        "via": jangin.via, "usage": jangin.usage or {},
    })
    if log_dialogue:
        _append_dialogue("jangin", jangin.design)

    # 2) 심판자 — 약점 3가지
    s_in = f"{brief}\n\n[장인 설계]\n{result.jangin}"
    text, model, usage = _call_role("simpanja", s_in, max_tokens=max_tokens)
    result.simpanja = text
    result.models_used["simpanja"] = model
    result.total_usd += float(usage.get("usd", 0))
    result.rounds.append({"role": "simpanja", "model": model, "content": text, "usage": usage})
    if log_dialogue:
        _append_dialogue("simpanja", text)

    # 3) 검사관 — 실현성 정량 검증
    g_in = f"{s_in}\n\n[심판자 약점]\n{result.simpanja}"
    text, model, usage = _call_role("geomsakwan", g_in, max_tokens=max_tokens)
    result.geomsakwan = text
    result.models_used["geomsakwan"] = model
    result.total_usd += float(usage.get("usd", 0))
    result.rounds.append({"role": "geomsakwan", "model": model, "content": text, "usage": usage})
    if log_dialogue:
        _append_dialogue("geomsakwan", text)

    # 4) 재판장 — 합의안 (JSON). Gemini 2.5 Flash(thinking-disabled) → 1500 적정.
    j_in = (
        f"{g_in}\n\n[검사관 실현성]\n{result.geomsakwan}\n\n"
        "위 발언을 종합해 최종 합의안을 스키마대로 JSON으로만 출력하세요."
    )
    text, model, usage = _call_role("jaepanjang", j_in, max_tokens=max(max_tokens, 1500))
    data = _parse_json(text)
    # Flash가 본문 비거나 파싱 실패 시 → GLM-4.5-Flash로 1회 재시도(다른 제공자).
    if not text.strip() or not (isinstance(data, dict) and data.get("consensus")):
        logger.warning("재판장(%s) 합의안 비거나 파싱 실패 → zai/glm-4.5-flash 재시도", model)
        text2, model2, usage2 = call_llm(
            j_in,
            system_prompt=_prompt("jaepanjang"),
            max_tokens=1500,
            model="zai/glm-4.5-flash",
            return_usage=True,
        )
        if text2.strip():
            text, model, usage = text2, model2, usage2
            data = _parse_json(text)
    result.jaepanjang = text
    result.models_used["jaepanjang"] = model
    result.total_usd += float(usage.get("usd", 0))
    result.rounds.append({"role": "jaepanjang", "model": model, "content": text, "usage": usage})
    if log_dialogue:
        _append_dialogue("jaepanjang", text)

    consensus = data.get("consensus") if isinstance(data, dict) else None
    if isinstance(consensus, list):
        result.consensus = [str(c).strip() for c in consensus if str(c).strip()]
    confidence = data.get("confidence", 0) if isinstance(data, dict) else 0
    try:
        result.confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        result.confidence = 0.0
    result.reasoning = str(data.get("reasoning", "")).strip() if isinstance(data, dict) else ""
    result.total_usd = round(result.total_usd, 6)
    return result


def run_debate(
    intent: IntentResult,
    dod: DoDResult,
    *,
    use_cowork: bool = False,
    with_red_team: bool = True,
    log_dialogue: bool = True,
    confidence_threshold: float = _DEFAULT_THRESHOLD,
    max_tokens: int = 800,
    max_restarts: int = _MAX_RESTARTS,
) -> DebateResult:
    """4역할 순차 토론 → 합의안 → STEP 5 Red Team Pass.

    Red Team 강제 단계(5a·5b·5c)가 누락되면 최대 max_restarts회 토론 재시작.
    강제 단계는 완료됐으나 사장님 직감 확인 [C]만 대기인 경우는 정상 — 재시작 없이 needs_confirmation 유지.
    """
    if intent is None or not (intent.true_intent or intent.surface_goal).strip():
        return DebateResult(reasoning="빈 의도 — 토론 불가.", needs_confirmation=True)

    result = _run_once(
        intent, dod, use_cowork=use_cowork, log_dialogue=log_dialogue, max_tokens=max_tokens
    )

    if with_red_team:
        attempt = 0
        while True:
            consensus = {
                "surface_goal": intent.surface_goal,
                "true_intent": intent.true_intent,
                "criteria": result.consensus or dod.criteria,
                "reasoning": result.reasoning,
            }
            rt = run_red_team_pass(consensus)
            result.red_team = rt
            result.restarts = attempt
            # 강제 단계 누락 → 재시작. 사장님 확인 대기(steps_complete=True)는 정상 종료.
            if rt.steps_complete or attempt >= max_restarts:
                break
            attempt += 1
            logger.warning("Red Team 강제 단계 누락 → 토론 재시작 %d/%d", attempt, max_restarts)
            result = _run_once(
                intent, dod, use_cowork=use_cowork, log_dialogue=log_dialogue, max_tokens=max_tokens
            )

    count_ok = 3 <= len(result.consensus) <= 5
    rt_hold = result.red_team is not None and not result.red_team.proceed
    result.needs_confirmation = (
        result.confidence < confidence_threshold or not count_ok or rt_hold
    )
    return result
