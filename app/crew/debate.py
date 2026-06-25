"""CrewAI 순차 토론 루프."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from crewai import Crew, Process, Task

from app.crew.personas import ROLE_MODELS, build_agents


@dataclass
class CrewDebateResult:
    """토론 결과."""

    topic: str
    consensus: str
    transcript: str
    models_used: list[str]
    elapsed_sec: float


def _mock_result(topic: str) -> CrewDebateResult:
    transcript = (
        "[장인] CI mock: 최소 구현안 제시\n"
        "[심판자] CI mock: 비용·리스크 지적\n"
        "[검사관] CI mock: pytest 시나리오 2건\n"
        "[재판장] CI mock: 합의안 정리"
    )
    consensus = f"[ci-mock 합의] {topic[:80]} — 단계적 구현, 테스트 우선."
    return CrewDebateResult(
        topic=topic,
        consensus=consensus,
        transcript=transcript,
        models_used=list(ROLE_MODELS.values()),
        elapsed_sec=0.01,
    )


def run_crew_debate(topic: str, *, context: str = "") -> CrewDebateResult:
    """4역할 순차 토론 후 합의안 반환."""
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("topic is required")

    if os.environ.get("CI") == "1" or os.environ.get("CREW_MOCK") == "1":
        return _mock_result(topic)

    t0 = time.perf_counter()
    agents = build_agents()
    brief = f"주제: {topic}"
    if context.strip():
        brief = f"{brief}\n\n참고:\n{context.strip()}"

    task_propose = Task(
        description=f"{brief}\n\n실행 가능한 구현안을 제시하세요.",
        expected_output="구현안 요약 (불릿 3~5개)",
        agent=agents["장인"],
    )
    task_critique = Task(
        description="장인의 구현안을 비판하세요. 사장님 흉내 금지.",
        expected_output="비판 포인트 (불릿 3~5개)",
        agent=agents["심판자"],
        context=[task_propose],
    )
    task_tests = Task(
        description="구현안에 대한 테스트·검증 시나리오를 작성하세요.",
        expected_output="테스트 케이스 목록",
        agent=agents["검사관"],
        context=[task_propose, task_critique],
    )
    task_consensus = Task(
        description="앞선 발언을 종합해 최종 합의안을 작성하세요.",
        expected_output="합의안 3~5문장",
        agent=agents["재판장"],
        context=[task_propose, task_critique, task_tests],
    )

    crew = Crew(
        agents=list(agents.values()),
        tasks=[task_propose, task_critique, task_tests, task_consensus],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    raw = str(result.raw if hasattr(result, "raw") else result).strip()
    elapsed = time.perf_counter() - t0

    transcript = (
        f"[장인]\n{task_propose.output or '-'}\n\n"
        f"[심판자]\n{task_critique.output or '-'}\n\n"
        f"[검사관]\n{task_tests.output or '-'}\n\n"
        f"[재판장]\n{raw}"
    )
    return CrewDebateResult(
        topic=topic,
        consensus=raw,
        transcript=transcript,
        models_used=list(ROLE_MODELS.values()),
        elapsed_sec=elapsed,
    )
