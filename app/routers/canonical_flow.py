"""Canonical Flow — 헌법 3조 9단계 오케스트레이터.

run_canonical_flow(user_input) → STEP 0~9 순차 실행 → FlowResult.
한 줄 입력으로 의도추출→DoD→토론→Tech Radar→Red Team→분류→실행→사용법→메모리까지.
모든 dialogue 기록은 log_dialogue 플래그로 게이팅(테스트 격리).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.config import ROOT
from app.crew.brain_writer import record_consensus
from app.routers.capability_router import RouteDecision, append_decision_log, classify
from app.routers.dod_designer import design_dod
from app.routers.executor import ExecutionResult, append_execution_log, execute
from app.routers.intent_extractor import ExecutionStrength, extract_intent
from app.routers.red_team import run_red_team_pass
from app.routers.usage_doc import generate_usage_doc
from app.tools.web_search import search_web

# 지연 import 회피: run_debate는 crew_debate가 dod_designer를 import하므로 안전
from app.routers.crew_debate import run_debate

logger = logging.getLogger(__name__)

_DIALOGUE_PATH = ROOT / "handoff" / "dialogue.md"

# STEP 0 — Mission Memory (헌법 2조 사장님 진짜 목표 9가지) 강제 prefix
MISSION_MEMORY = (
    "[Mission Memory — 헌법 2조] 1.진짜 의도 추출 2.자율 DoD 3.레드팀 검증 "
    "4.연속 대화 검증 5.능동 질문 6.최신 기술 자동 도입 7.컨텍스트 망각 방지 "
    "8.오픈소스 즉각 활용 9.정액제+복붙 친화 | 프레임: 시간절감→비용→ROI | "
    "제약: 정액제 활용·무료/오픈소스 우선·1인 운영 규모"
)


@dataclass
class FlowResult:
    user_input: str = ""
    steps: list[dict] = field(default_factory=list)
    intent: object | None = None
    dod: object | None = None
    consensus: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    tech_radar: dict = field(default_factory=dict)
    red_team: object | None = None
    routes: list[RouteDecision] = field(default_factory=list)
    executions: list[ExecutionResult] = field(default_factory=list)
    execution_strength: str = ""
    usage_doc: str = ""
    brain_entry_id: str = ""
    needs_confirmation: bool = False
    questions: list[str] = field(default_factory=list)
    total_usd: float = 0.0


def _append_flow_log(fr: FlowResult) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {stamp} [FLOW] Canonical Flow 9단계: {fr.user_input[:60]}"]
    for s in fr.steps:
        lines.append(f"- STEP {s['step']} {s['name']}: {s['status']} — {s['summary'][:90]}")
    with _DIALOGUE_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _step(fr: FlowResult, step: int, name: str, status: str, summary: str) -> None:
    fr.steps.append({"step": step, "name": name, "status": status, "summary": summary})


def run_canonical_flow(
    user_input: str,
    *,
    log_dialogue: bool = True,
    with_tech_radar: bool = True,
    max_tokens: int = 800,
    live_execution: bool | None = None,
) -> FlowResult:
    """헌법 3조 STEP 0~9 순차 오케스트레이션."""
    fr = FlowResult(user_input=(user_input or "").strip())
    if not fr.user_input:
        _step(fr, 0, "Mission Memory", "skip", "빈 입력")
        fr.needs_confirmation = True
        fr.usage_doc = "빈 입력입니다. 작업을 한 줄로 적어주세요."
        return fr

    # STEP 0 — Mission Memory 로드
    _step(fr, 0, "Mission Memory", "done", MISSION_MEMORY[:80])

    # STEP 1 — Intent Extractor
    fr.intent = extract_intent(fr.user_input)
    true_intent = getattr(fr.intent, "true_intent", "") or ""
    _step(fr, 1, "Intent Extractor", "done", f"진짜 의도: {true_intent[:60]}")
    if not (true_intent or getattr(fr.intent, "surface_goal", "")).strip():
        fr.needs_confirmation = True
        fr.usage_doc = generate_usage_doc(fr)
        if log_dialogue:
            _append_flow_log(fr)
        return fr

    # STEP 2 — DoD Auto-Designer
    fr.dod = design_dod(fr.intent, red_team=False)
    _step(fr, 2, "DoD Auto-Designer", "done", f"완료조건 {len(getattr(fr.dod, 'criteria', []))}개")

    # STEP 3 — CrewAI 4역할 토론
    debate = run_debate(
        fr.intent, fr.dod, with_red_team=False, log_dialogue=log_dialogue, max_tokens=max_tokens
    )
    fr.consensus = list(debate.consensus)
    fr.confidence = debate.confidence
    fr.reasoning = debate.reasoning
    fr.total_usd += float(debate.total_usd)
    _step(fr, 3, "CrewAI 토론", "done", f"합의안 {len(fr.consensus)}개 conf {fr.confidence:.2f}")

    # STEP 4 — Tech Radar (스켈레톤: Tavily 1회)
    if with_tech_radar:
        try:
            radar = search_web(f"{true_intent} 오픈소스 도구 2026", max_results=3)
            tools = [r.get("title", "") for r in radar.get("results", [])]
            fr.tech_radar = {"answer": radar.get("answer", "")[:200], "candidates": tools}
            _step(fr, 4, "Tech Radar", "done", f"후보 {len(tools)}건 (스켈레톤)")
        except Exception as exc:  # noqa: BLE001
            fr.tech_radar = {"skipped": str(exc)[:80]}
            _step(fr, 4, "Tech Radar", "skip", f"건너뜀: {str(exc)[:60]}")
    else:
        _step(fr, 4, "Tech Radar", "skip", "비활성")

    # STEP 5 — Red Team Pass
    consensus_dict = {
        "surface_goal": getattr(fr.intent, "surface_goal", ""),
        "true_intent": true_intent,
        "criteria": fr.consensus or getattr(fr.dod, "criteria", []),
        "reasoning": fr.reasoning,
    }
    fr.red_team = run_red_team_pass(consensus_dict)
    _step(fr, 5, "Red Team", "done", f"다양성 {getattr(fr.red_team, 'diversity_score', 0):.2f}")

    # STEP 6 — Capability Router
    tasks = fr.consensus or getattr(fr.dod, "criteria", [])
    fr.routes = [classify({"task": t}) for t in tasks]
    if log_dialogue:
        append_decision_log(fr.routes)
    counts = {r: sum(1 for d in fr.routes if d.route == r) for r in "ABCDE"}
    _step(fr, 6, "Capability Router", "done", f"분류 {counts}")

    # STEP 7 — Execution (7-A 후보 수집/분석 자동 → 7-B 사장님 [C] 라운드)
    strength = getattr(fr.intent, "execution_strength", ExecutionStrength.CANDIDATE_LIST)
    fr.execution_strength = getattr(strength, "value", str(strength))
    auto_exec = strength in (ExecutionStrength.OK_THEN_AUTO, ExecutionStrength.FULL_AUTO)
    live = auto_exec if live_execution is None else live_execution
    fr.executions = [execute(d, live=live) for d in fr.routes]
    if log_dialogue:
        append_execution_log(fr.executions)
    # 7-B: executor 질문 + Intent가 예측한 사장님 결정 포인트(중간 [C] 라운드)
    exec_qs = [e.question for e in fr.executions if e.question]
    decision_qs = list(getattr(fr.intent, "required_user_decisions", []) or [])
    fr.questions = exec_qs + [q for q in decision_qs if q not in exec_qs]
    _step(fr, 7, "Execution", "done", f"실행 {len(fr.executions)}건 live={live} 질문 {len(fr.questions)}")

    # needs_confirmation 판정 (OK_THEN_AUTO는 사장님 OK 후 자동화 진행 → 확인 필요)
    rt_hold = fr.red_team is not None and not getattr(fr.red_team, "proceed", False)
    has_cd = any(d.route in ("C", "D") for d in fr.routes)
    ok_then_auto = strength == ExecutionStrength.OK_THEN_AUTO
    fr.needs_confirmation = bool(
        debate.needs_confirmation or rt_hold or has_cd or ok_then_auto or fr.questions
    )

    # STEP 8 — Usage Doc Auto-Gen
    fr.usage_doc = generate_usage_doc(fr)
    _step(fr, 8, "Usage Doc", "done", f"{len(fr.usage_doc)}자")

    # STEP 9 — Mission Memory 업데이트 (SHARED_BRAIN)
    try:
        fr.brain_entry_id = record_consensus(
            topic=true_intent or fr.user_input,
            consensus="\n".join(fr.consensus),
            transcript=f"conf={fr.confidence} routes={counts}",
            source="canonical_flow",
        )
        _step(fr, 9, "Mission Memory", "done", f"SHARED_BRAIN {fr.brain_entry_id}")
    except Exception as exc:  # noqa: BLE001
        _step(fr, 9, "Mission Memory", "error", str(exc)[:60])

    if log_dialogue:
        _append_flow_log(fr)
    return fr
