"""CrewAI 4역할 페르소나 — SHARED_BRAIN crew_personas_week2."""

from __future__ import annotations

import os

from crewai import Agent, LLM

from app.config import ensure_env_from_credentials

# 헌법 3조 STEP 3과 동기화 (2026-06-27). 4개 제공자 = 다양성 1.0.
# 장인=Anthropic / 심판자=Z.ai / 검사관=Groq / 재판장=Google.
ROLE_MODELS: dict[str, str] = {
    "장인": "anthropic/claude-sonnet-4-6",
    "심판자": "zai/glm-4.5-flash",
    "검사관": "groq/llama-3.3-70b-versatile",
    "재판장": "gemini/gemini-2.5-flash",
}

_ZAI_API_BASE_DEFAULT = "https://api.z.ai/api/paas/v4/"

_JANGIN_GOAL = """실용적인 구현안을 제시한다.
코드·아키텍처·실행 순서 위주. 이모지 금지. 한국어."""

_JUDGE_GOAL = """가상의 '심판자' 노이즈 픽션 페르소나다. 사장님 본인이 아니다.
비용·시간·ROI·리스크 관점에서 가차 없이 비판한다. 이모지 금지. 한국어."""

_INSPECTOR_GOAL = """검사관으로 pytest 관점의 테스트 케이스·엣지 케이스를 제시한다.
이모지 금지. 한국어."""

_CHAIR_GOAL = """재판장으로 앞선 발언을 종합해 실행 가능한 합의안 3~5줄을 도출한다.
이모지 금지. 한국어."""


def _llm(role: str) -> LLM:
    ensure_env_from_credentials()
    model = ROLE_MODELS[role]
    # Z.ai(GLM)는 OpenAI 호환 — crewai/litellm 라우팅 위해 base_url+api_key 명시.
    if model.startswith("zai/"):
        bare = model.split("/", 1)[1]
        return LLM(
            model=f"openai/{bare}",
            temperature=0.3,
            max_tokens=600,
            base_url=os.environ.get("ZAI_API_BASE", _ZAI_API_BASE_DEFAULT),
            api_key=os.environ.get("ZAI_API_KEY"),
        )
    return LLM(model=model, temperature=0.3, max_tokens=600)


def build_agents() -> dict[str, Agent]:
    """4역할 에이전트."""
    return {
        "장인": Agent(
            role="장인",
            goal=_JANGIN_GOAL,
            backstory="도깨비 OS 백엔드 실무 코더. 최종 구현 책임.",
            llm=_llm("장인"),
            verbose=False,
        ),
        "심판자": Agent(
            role="심판자",
            goal=_JUDGE_GOAL,
            backstory="픽션 비판자. 사장님 목소리를 흉내 내지 않는다.",
            llm=_llm("심판자"),
            verbose=False,
        ),
        "검사관": Agent(
            role="검사관",
            goal=_INSPECTOR_GOAL,
            backstory="품질·회귀 테스트 관점의 검사관.",
            llm=_llm("검사관"),
            verbose=False,
        ),
        "재판장": Agent(
            role="재판장",
            goal=_CHAIR_GOAL,
            backstory="토론을 마무리하고 합의안을 정리하는 재판장.",
            llm=_llm("재판장"),
            verbose=False,
        ),
    }
