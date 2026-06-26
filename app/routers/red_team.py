"""Red Team Pass — 헌법 3조 STEP 5 (5a~5d 보강).

합의안(consensus) 제출 전 강제 실행:
- 5a 강제 메모리 회수 (mem0 + dialogue grep + 헌법 grep)
- 5b 강제 도구 점검 (MCP_INVENTORY 기반 deferred tools)
- 5c 본 Red Team 토론 ("6개월 후 실패 이유 3가지") + 사각지대 다양성 보장
- 5d 사장님 직감 확인 [C]

강제 단계(5a·5b·5c) 누락 시 proceed=False. 5d 미확인 시에도 proceed=False(합의 보류).
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field

from app.config import ROOT
from app.crew.personas import ROLE_MODELS
from app.litellm_router import call_llm
from app.routers.intent_extractor import _parse_json

logger = logging.getLogger(__name__)

_DIALOGUE_PATH = ROOT / "handoff" / "dialogue.md"
_CONSTITUTION_PATH = ROOT / "CONSTITUTION.md"
_MCP_INVENTORY_PATH = ROOT / "docs" / "MCP_INVENTORY.md"
_RED_TEAM_MODEL = "anthropic/claude-sonnet-4-6"  # 심판자 재등장
_KNOWN_TOOLS = (
    "filesystem",
    "DOKKEBI",
    "synology",
    "code-lens",
    "gemini",
    "pal",
    "ffmpeg",
    "chrome-devtools",
)
_GREP_LIMIT = 5
_MIN_FAILURE_REASONS = 3

_DEBATE_SYSTEM = (
    "당신은 도깨비 OS의 레드팀 심판자입니다. 제시된 합의안이 6개월 후 실패할 이유를 "
    "가차 없이 3가지 도출하세요. 비용·시간·ROI·운영 리스크 관점. 이모지 금지, 한국어.\n"
    '출력은 순수 JSON 하나: {"failure_reasons": ["이유1", "이유2", "이유3"]}'
)


@dataclass
class RedTeamResult:
    """STEP 5 Red Team Pass 결과."""

    proceed: bool = False
    steps_complete: bool = False
    memory_recall_done: bool = False
    tool_audit_done: bool = False
    debate_done: bool = False
    failure_reasons: list[str] = field(default_factory=list)
    diversity_score: float = 0.0
    diversity_ok: bool = False
    diversity_warning: str = ""
    needs_user_intuition: bool = True
    user_question: str = ""
    user_confirmed: bool | None = None
    recalled: list[str] = field(default_factory=list)
    audited_tools: list[str] = field(default_factory=list)
    model_used: str = ""
    notes: str = ""


def _topic_text(consensus: dict) -> str:
    parts: list[str] = []
    for key in ("topic", "true_intent", "surface_goal", "reasoning"):
        val = consensus.get(key)
        if val:
            parts.append(str(val))
    criteria = consensus.get("criteria")
    if isinstance(criteria, list):
        parts.extend(str(c) for c in criteria)
    return " ".join(parts).strip() or str(consensus)


def _keywords(topic: str) -> set[str]:
    return {w for w in topic.replace(",", " ").split() if len(w) >= 2}


def _grep_file(path, keywords: set[str], *, limit: int = _GREP_LIMIT) -> list[str]:
    if not path.is_file() or not keywords:
        return []
    matched: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and any(kw in stripped for kw in keywords):
            matched.append(stripped[:200])
    return matched[-limit:]


def memory_recall(topic: str, *, limit: int = _GREP_LIMIT) -> tuple[list[str], bool]:
    """5a. mem0 검색 + dialogue grep + 헌법 grep. 파일 회수 성공 시 done=True."""
    recalled: list[str] = []
    keywords = _keywords(topic)

    try:
        from app.memory_service import search_memories

        rows = search_memories(topic, limit=limit)
        for r in rows:
            text = str(r.get("memory") or r.get("text") or "").strip()
            if text:
                recalled.append(f"[mem0] {text[:160]}")
    except Exception as exc:  # noqa: BLE001 — mem0/chroma 미가동 비치명적
        logger.warning("memory_recall mem0 스킵: %s", exc)

    try:
        for line in _grep_file(_DIALOGUE_PATH, keywords):
            recalled.append(f"[dialogue] {line}")
        for line in _grep_file(_CONSTITUTION_PATH, keywords):
            recalled.append(f"[헌법] {line}")
        file_ok = _DIALOGUE_PATH.is_file() and _CONSTITUTION_PATH.is_file()
    except Exception as exc:  # noqa: BLE001
        logger.warning("memory_recall 파일 grep 실패: %s", exc)
        file_ok = False

    return recalled, file_ok


def tool_audit() -> tuple[list[str], bool]:
    """5b. MCP_INVENTORY 기반 deferred tools 전수 점검."""
    if not _MCP_INVENTORY_PATH.is_file():
        logger.warning("tool_audit: MCP_INVENTORY.md 없음")
        return [], False
    text = _MCP_INVENTORY_PATH.read_text(encoding="utf-8")
    audited = [t for t in _KNOWN_TOOLS if t in text]
    return audited, True


def diversity_check(models: list[str]) -> tuple[float, bool, str]:
    """5c. 4역할 제공자 다양성. 같은 제공자 중복 시 경고. 점수 = 제공자 종류 수 / 역할 수."""
    if not models:
        return 0.0, False, "모델 미지정"
    providers = [m.split("/")[0] for m in models]
    distinct = len(set(providers))
    score = distinct / len(models)
    warning = ""
    dup = [p for p, c in Counter(providers).items() if c > 1]
    if dup:
        warning = f"제공자 중복 {dup} — 사각지대 공유 위험(레드팀 다양성 저하)"
        logger.warning("Red Team 다양성 경고: %s (score=%.2f)", warning, score)
    if distinct == 1:
        warning = f"전원 동일 제공자({providers[0]}) — 레드팀 무용 위험"
        logger.warning("Red Team 다양성 치명: %s", warning)
    diversity_ok = distinct >= 2
    return score, diversity_ok, warning


def red_team_debate(topic: str, consensus: dict, *, max_tokens: int = 800) -> tuple[list[str], str]:
    """5c. '6개월 후 실패 이유 3가지' 도출."""
    user = f"합의안 주제: {topic}\n합의안 상세: {json.dumps(consensus, ensure_ascii=False)}"
    response, model_used = call_llm(
        user,
        system_prompt=_DEBATE_SYSTEM,
        max_tokens=max_tokens,
        model=_RED_TEAM_MODEL,
    )
    data = _parse_json(response)
    reasons = data.get("failure_reasons") if isinstance(data, dict) else None
    if isinstance(reasons, list):
        cleaned = [str(r).strip() for r in reasons if str(r).strip()]
    else:
        cleaned = [ln.strip("-• \t") for ln in response.splitlines() if ln.strip()][:3]
    return cleaned, model_used


def ask_user_intuition(consensus: dict) -> str:
    """5d. 사장님 [C] 질문 문자열. 실제 전송은 호출측(봇/텔레그램)."""
    crit = consensus.get("criteria")
    head = crit[0] if isinstance(crit, list) and crit else (consensus.get("true_intent") or "이 합의안")
    return (
        f"이 합의안('{head}' 등)이 사장님 직감과 맞습니까? "
        "'어딘가 본 것 같다' / '이미 논의하지 않았나' 싶으면 5a 메모리 회수로 회귀합니다. (예/아니오)"
    )


def run_red_team_pass(
    consensus: dict,
    *,
    models: list[str] | None = None,
    run_debate: bool = True,
    user_confirmed: bool | None = None,
) -> RedTeamResult:
    """STEP 5 전 과정 실행. 강제 단계 누락 또는 사장님 미확인 시 proceed=False.

    user_confirmed: None=대기([C]), True=직감 일치, False=5a 회귀 권고.
    """
    models = models or list(ROLE_MODELS.values())
    topic = _topic_text(consensus)

    recalled, mem_ok = memory_recall(topic)          # 5a
    audited, audit_ok = tool_audit()                 # 5b
    score, div_ok, warning = diversity_check(models)  # 5c 다양성

    failure_reasons: list[str] = []
    model_used = ""
    debate_done = True
    if run_debate:
        try:
            failure_reasons, model_used = red_team_debate(topic, consensus)
        except Exception as exc:  # noqa: BLE001
            logger.warning("red_team_debate 실패: %s", exc)
        debate_done = len(failure_reasons) >= _MIN_FAILURE_REASONS

    steps_complete = mem_ok and audit_ok and debate_done
    question = ask_user_intuition(consensus)
    needs_user = user_confirmed is None
    proceed = steps_complete and div_ok and (user_confirmed is True)

    notes = ""
    if not steps_complete:
        notes = "강제 단계 누락 — 합의 보류."
    elif user_confirmed is None:
        notes = "사장님 직감 확인 [C] 대기 — 합의 보류."
    elif user_confirmed is False:
        notes = "사장님 직감 불일치 — 5a 메모리 회수로 회귀."

    return RedTeamResult(
        proceed=proceed,
        steps_complete=steps_complete,
        memory_recall_done=mem_ok,
        tool_audit_done=audit_ok,
        debate_done=debate_done,
        failure_reasons=failure_reasons,
        diversity_score=score,
        diversity_ok=div_ok,
        diversity_warning=warning,
        needs_user_intuition=needs_user,
        user_question=question,
        user_confirmed=user_confirmed,
        recalled=recalled,
        audited_tools=audited,
        model_used=model_used,
        notes=notes,
    )
