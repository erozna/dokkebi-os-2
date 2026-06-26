"""STEP 3 CrewAI 4역할 토론 평가 #1 — 실 LLM 호출 하니스 (헌법 3조 STEP 3).

수동 실행: python scripts/eval_debate_001.py
Intent + DoD("유튜브 엔진") 고정 입력 → 4역할 토론 → 합의안.
LLM 키(ALL_CREDENTIALS.json 또는 환경변수) 필요. 없으면 skip.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials  # noqa: E402
from app.routers.crew_debate import run_debate  # noqa: E402
from app.routers.dod_designer import DoDResult  # noqa: E402
from app.routers.intent_extractor import IntentResult  # noqa: E402

INTENT = IntentResult(
    surface_goal="유튜브 수익 검증 엔진 제작",
    true_intent="수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
    hidden_constraints=["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
    confidence=0.87,
    needs_confirmation=False,
)
DOD = DoDResult(
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
# 의미(주제) 일치 — 토론은 DoD를 개선/재구성하므로 문자 매칭이 아닌 테마 커버리지로 평가.
ANSWER_THEMES = [
    ("수집/필터", ["수집", "필터", "사기", "검증", "걸러", "배제", "차단", "탐지"]),
    ("추출/실행", ["추출", "실행", "액션", "action", "ACTION"]),
    ("검토시간", ["검토", "분", "시간", "리뷰"]),
    ("비용", ["무료", "0원", "0 원", "비용", "tier"]),
    ("도입/기간", ["도입", "7일", "일 이내", "day", "Day", "주기", "기간", "스케줄"]),
]


def main() -> int:
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    if not (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("GROQ_API_KEY")
    ):
        print("SKIP: LLM API 키 미설정. 사장님 보고 후 대기.")
        return 2

    result = run_debate(
        INTENT, DOD, use_cowork=False, with_red_team=False, log_dialogue=False, max_tokens=1200
    )

    joined = " ".join(result.consensus)
    matches = sum(1 for _label, kws in ANSWER_THEMES if any(k in joined for k in kws))
    count_ok = 3 <= len(result.consensus) <= 5
    overall = count_ok and matches >= 3 and result.confidence >= 0.5

    report = {
        "rounds": result.rounds,
        "consensus": result.consensus,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "models_used": result.models_used,
        "metrics": {
            "consensus_count": len(result.consensus),
            "count_ok_3to5": count_ok,
            "answer_match": matches,
            "answer_match_ok": matches >= 3,
            "confidence_ok": result.confidence >= 0.5,
            "overall_pass": overall,
        },
        "cost": {"total_usd": result.total_usd},
    }
    out_path = ROOT / "docs" / ".debate_eval_001.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out_path} overall_pass={overall} match={matches}/5 usd=${result.total_usd}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
