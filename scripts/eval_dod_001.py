"""DoD Auto-Designer 평가 #1 — 실 LLM 호출 하니스 (헌법 3조 STEP 2 검증).

수동 실행: python scripts/eval_dod_001.py
Intent Extractor 출력을 그대로 DoD 입력으로 사용(파이프라인).
ANTHROPIC_API_KEY/GEMINI_API_KEY(ALL_CREDENTIALS.json 또는 환경변수) 필요. 없으면 skip.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials  # noqa: E402
from app.routers.dod_designer import _DOD_MODEL, _build_user_input, _load_system_prompt  # noqa: E402
from app.routers.intent_extractor import _parse_json, extract_intent  # noqa: E402

DATASET_1_INPUT = (
    "유튜브에서 돈 버는 방법을 검증하는 엔진을 만들어서 자동으로 검색해서 "
    "그 유튜브 컨텐츠를 분석하고, 현실적 검증을 해보고 자동으로 도입할수 있는것들은 "
    "실행하는 프로그램을 만들어줘"
)

# 사장님 직감 정답 후보 (검증용, 일치도만 측정)
ANSWER_CRITERIA = [
    {"keys": ["100", "수집"], "alt": ["영상", "필터", "80"], "label": "주 100개 수집+필터 80%"},
    {"keys": ["3", "추출"], "alt": ["실행", "건"], "label": "실행 항목 주 3건"},
    {"keys": ["10", "검토"], "alt": ["분", "회"], "label": "검토 회당 10분 이하"},
    {"keys": ["무료", "비용"], "alt": ["0", "tier", "원"], "label": "월 비용 무료 tier"},
    {"keys": ["7", "도입"], "alt": ["일", "수익"], "label": "도입까지 7일"},
]


def _match_answer(criteria_text: str, ans: dict) -> bool:
    """의미 일치(문자 매칭 아님): 핵심 키 1개 + 보조 키 1개 이상이면 일치로 간주."""
    has_key = any(k in criteria_text for k in ans["keys"])
    has_alt = any(k in criteria_text for k in ans["alt"])
    return has_key and has_alt


def _measurable_unit(text: str) -> bool:
    units = ("%", "분", "시간", "일", "건", "개", "회", "원", "$", "tier", "무료", "정확도")
    return any(u in text for u in units)


def main() -> int:
    ensure_env_from_credentials()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print("SKIP: GEMINI/ANTHROPIC API 키 미설정. 사장님 보고 후 대기.")
        return 2

    from litellm import completion, completion_cost

    # STEP 1 — Intent (실 호출)
    intent = extract_intent(DATASET_1_INPUT)

    # STEP 2 — DoD (Gemini 실 호출, 사용 모델 자동 폴백 추적)
    model = _DOD_MODEL
    system = _load_system_prompt()
    user = _build_user_input(intent)
    fallback = ["anthropic/claude-sonnet-4-6", "gemini/gemini-2.5-flash", "groq/llama-3.3-70b-versatile"]
    chain = [model] + [m for m in fallback if m != model]

    response = None
    used_model = ""
    last_err = None
    for m in chain:
        try:
            response = completion(
                model=m,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=2048,
                temperature=0.3,
            )
            used_model = m
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    if response is None:
        print(f"FAIL: 모든 모델 호출 실패: {last_err}")
        return 1

    raw = (response.choices[0].message.content or "").strip()
    data = _parse_json(raw)

    try:
        cost = completion_cost(completion_response=response) or 0.0
    except Exception:  # noqa: BLE001
        cost = 0.0
    usage = getattr(response, "usage", None)
    prompt_tok = getattr(usage, "prompt_tokens", 0)
    comp_tok = getattr(usage, "completion_tokens", 0)
    total_tok = getattr(usage, "total_tokens", 0)

    criteria = [str(c).strip() for c in (data.get("criteria") or []) if str(c).strip()]
    confidence = float(data.get("confidence", 0) or 0)
    count_ok = 3 <= len(criteria) <= 5
    units_ok = all(_measurable_unit(c) for c in criteria) if criteria else False

    matched = []
    for ans in ANSWER_CRITERIA:
        hit = any(_match_answer(c, ans) for c in criteria)
        matched.append({"label": ans["label"], "hit": hit})
    match_count = sum(1 for m in matched if m["hit"])

    overall = count_ok and units_ok and match_count >= 3

    report = {
        "intent": {
            "surface_goal": intent.surface_goal,
            "true_intent": intent.true_intent,
            "hidden_constraints": intent.hidden_constraints,
            "confidence": intent.confidence,
        },
        "dod_model_requested": model,
        "dod_model_used": used_model,
        "raw": raw,
        "parsed": data,
        "metrics": {
            "criteria_count": len(criteria),
            "count_ok_3to5": count_ok,
            "all_measurable_units": units_ok,
            "answer_match": matched,
            "answer_match_count": match_count,
            "confidence": confidence,
            "confidence_ok": confidence >= 0.7,
            "overall_pass": overall,
        },
        "cost": {
            "prompt_tokens": prompt_tok,
            "completion_tokens": comp_tok,
            "total_tokens": total_tok,
            "usd": round(cost, 6),
        },
    }
    out_path = ROOT / "docs" / ".dod_eval_001.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out_path} overall_pass={overall} model_used={used_model}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
