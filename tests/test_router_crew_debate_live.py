"""CrewAI 4역할 토론 실 LLM 평가 (모킹 아님) — 헌법 3조 STEP 3.

기본 pytest 실행에서 제외. 수동: pytest -m live tests/test_router_crew_debate_live.py -s
GEMINI/ANTHROPIC/GROQ 키 중 하나라도 없으면 skip(폴백 체인 동작 위해 최소 1개 필요).
dialogue.md 오염 방지를 위해 log_dialogue=False, Red Team off로 합의안만 평가.
"""

from __future__ import annotations

import os

import pytest

from app.config import ensure_env_from_credentials
from app.routers.crew_debate import run_debate
from app.routers.dod_designer import DoDResult
from app.routers.intent_extractor import IntentResult

pytestmark = pytest.mark.live

_INTENT = IntentResult(
    surface_goal="유튜브 수익 검증 엔진 제작",
    true_intent="수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
    hidden_constraints=["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
    confidence=0.87,
    needs_confirmation=False,
)
_DOD = DoDResult(
    criteria=[
        "주 100건 영상 자동 수집, 사기 필터 정확도 80% 이상",
        "실행 가능 수익 항목 주 3건 이상 추출",
        "사장님 검토 시간 회당 10분 이하",
        "월 운영 비용 무료 tier 0원 유지",
        "수익 모델 1건 도입까지 평균 7일 이내",
    ],
    measurable=True,
    confidence=0.9,
)

# 사장님 직감 정답 주제 (의미 일치, 문자 매칭 아님 — 토론은 DoD를 개선/재구성함)
_ANSWER_THEMES = [
    ("수집/필터", ["수집", "필터", "사기", "검증", "걸러", "배제", "차단", "탐지"]),
    ("추출/실행", ["추출", "실행", "액션", "action", "ACTION"]),
    ("검토시간", ["검토", "분", "시간", "리뷰"]),
    ("비용", ["무료", "0원", "0 원", "비용", "tier"]),
    ("도입/기간", ["도입", "7일", "일 이내", "day", "Day", "주기", "기간", "스케줄"]),
]


def _has_any_key() -> bool:
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    return bool(
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("GROQ_API_KEY")
    )


@pytest.mark.skipif(not _has_any_key(), reason="LLM API 키 미설정. 사장님 [D] 필요.")
def test_run_debate_live_dataset1() -> None:
    result = run_debate(
        _INTENT,
        _DOD,
        use_cowork=False,       # 장인은 Claude Sonnet API
        with_red_team=False,    # 합의안 품질만 평가
        log_dialogue=False,     # 실제 dialogue.md 오염 방지
        max_tokens=700,
    )

    # 4역할 모두 응답
    assert result.jangin.strip()
    assert result.simpanja.strip()
    assert result.geomsakwan.strip()
    assert result.jaepanjang.strip()

    # 합의안 3~5개
    assert 3 <= len(result.consensus) <= 5, f"합의안 개수: {len(result.consensus)} / {result.consensus}"

    # 사장님 직감 정답 주제 최소 50%(3/5) 커버
    joined = " ".join(result.consensus)
    matches = sum(1 for _label, kws in _ANSWER_THEMES if any(k in joined for k in kws))
    assert matches >= 3, f"정답 주제 커버 부족({matches}/5): {result.consensus}"

    assert result.confidence >= 0.5
    print(f"\n[DEBATE LIVE] confidence={result.confidence} usd=${result.total_usd} models={result.models_used}")
