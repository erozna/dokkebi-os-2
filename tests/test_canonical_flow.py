"""Canonical Flow 9단계 오케스트레이터 테스트 — 헌법 3조. 모킹."""

from __future__ import annotations

from unittest.mock import patch

from app.routers.canonical_flow import FlowResult, run_canonical_flow
from app.routers.capability_router import RouteDecision
from app.routers.crew_debate import DebateResult
from app.routers.dod_designer import DoDResult
from app.routers.executor import ExecutionResult
from app.routers.intent_extractor import IntentResult
from app.routers.red_team import RedTeamResult

_INTENT = IntentResult(
    surface_goal="유튜브 부업채널 분석",
    true_intent="수동 검색 시간 0화 + 사기 필터 + 실행 항목 추출",
    hidden_constraints=["정액제", "무료 도구", "1인 운영"],
    confidence=0.88,
    needs_confirmation=False,
)
_DOD = DoDResult(criteria=["주 50건 수집", "추출 주 2건", "검토 10분"], measurable=True, confidence=0.9)
_DEBATE = DebateResult(
    consensus=["yt-dlp로 영상 수집 자동화", "pytest 검증 시나리오 작성", "API 쿼리 캐싱"],
    confidence=0.85,
    needs_confirmation=False,
    total_usd=0.03,
)
_RT = RedTeamResult(proceed=True, steps_complete=True, diversity_score=1.0, needs_user_intuition=False)
_RADAR = {"answer": "요약", "results": [{"title": "yt-dlp"}, {"title": "whisper"}]}


def _patches(debate=_DEBATE, rt=_RT, exec_side=None):
    def _exec(d, *, live=False):
        return exec_side(d) if exec_side else ExecutionResult(route=d.route, status="done", detail="ok")

    return [
        patch("app.routers.canonical_flow.extract_intent", return_value=_INTENT),
        patch("app.routers.canonical_flow.design_dod", return_value=_DOD),
        patch("app.routers.canonical_flow.run_debate", return_value=debate),
        patch("app.routers.canonical_flow.run_red_team_pass", return_value=rt),
        patch("app.routers.canonical_flow.search_web", return_value=_RADAR),
        patch("app.routers.canonical_flow.execute", side_effect=_exec),
        patch("app.routers.canonical_flow.record_consensus", return_value="entry_123"),
    ]


def _run(**kw):
    ps = _patches(**kw)
    for p in ps:
        p.start()
    try:
        return run_canonical_flow("유튜브 부업채널 분석해줘", log_dialogue=False)
    finally:
        for p in reversed(ps):
            p.stop()


def test_canonical_flow_runs_all_9_steps():
    fr = _run()
    assert isinstance(fr, FlowResult)
    step_nums = [s["step"] for s in fr.steps]
    assert step_nums == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert all(s["status"] in ("done", "skip") for s in fr.steps)


def test_canonical_flow_propagates_consensus_and_routes():
    fr = _run()
    assert fr.consensus == _DEBATE.consensus
    assert fr.confidence == 0.85
    assert len(fr.routes) == len(_DEBATE.consensus)
    assert all(isinstance(r, RouteDecision) for r in fr.routes)
    # 합의안 전부 [A] 자동화 키워드 → needs_confirmation False
    assert all(r.route == "A" for r in fr.routes)
    assert fr.needs_confirmation is False
    assert fr.brain_entry_id == "entry_123"
    assert fr.usage_doc
    assert fr.total_usd == 0.03


def test_canonical_flow_needs_confirmation_on_red_team_hold():
    rt_hold = RedTeamResult(proceed=False, steps_complete=True, diversity_score=0.75)
    fr = _run(rt=rt_hold)
    assert fr.needs_confirmation is True


def test_canonical_flow_collects_questions_from_executor():
    def _exec(d):
        q = "사장님 결정 필요?" if d.route == "A" else ""
        return ExecutionResult(route=d.route, status="pending", question=q)

    fr = _run(exec_side=_exec)
    assert fr.questions  # executor가 반환한 question 수집
    assert len(fr.questions) == len(fr.routes)


def test_canonical_flow_empty_input():
    fr = run_canonical_flow("   ", log_dialogue=False)
    assert fr.needs_confirmation is True
    assert fr.steps[0]["status"] == "skip"
