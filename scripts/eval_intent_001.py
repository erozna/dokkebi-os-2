"""Intent Extractor 평가 #1 — 실 LLM 호출 하니스 (헌법 3조 STEP 1 검증).

수동 실행: python scripts/eval_intent_001.py
ANTHROPIC_API_KEY(ALL_CREDENTIALS.json 또는 환경변수) 필요. 없으면 skip.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import ensure_env_from_credentials  # noqa: E402
from app.litellm_router import select_model  # noqa: E402
from app.routers.intent_extractor import _load_system_prompt, _parse_json  # noqa: E402

DATASET_1_INPUT = (
    "유튜브에서 돈 버는 방법을 검증하는 엔진을 만들어서 자동으로 검색해서 "
    "그 유튜브 컨텐츠를 분석하고, 현실적 검증을 해보고 자동으로 도입할수 있는것들은 "
    "실행하는 프로그램을 만들어줘"
)

ANSWER = {
    "surface_goal": "유튜브 수익 검증 엔진 제작",
    "true_intent": "수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출",
    "hidden_constraints": ["정액제 활용", "무료 도구 우선", "1인 운영 규모"],
}


def _metric_surface(text: str) -> bool:
    kws = ["유튜브", "엔진", "검증", "수익"]
    return sum(1 for k in kws if k in text) >= 2


def _metric_true(text: str) -> dict[str, bool]:
    # 의미 일치 기준(문자 일치 아님): 시간 0화는 제거/없앰/단축/절감/0/줄임 등으로,
    # 자동화는 "자동" 어근으로 폭넓게 인정.
    time_zero = "시간" in text and any(w in text for w in ("0", "절감", "단축", "줄", "제거", "없", "최소"))
    g1 = time_zero or ("자동" in text)
    g2 = any(w in text for w in ("필터", "검증", "거르", "사기", "걸러", "배제"))
    g3 = ("실행" in text) or ("도입" in text)
    return {"시간0화/자동화": g1, "필터/검증": g2, "실행가능": g3}


def _metric_constraints(items: list[str]) -> int:
    joined = " ".join(items)
    hits = 0
    if "정액" in joined:
        hits += 1
    if "무료" in joined or "오픈소스" in joined:
        hits += 1
    if "1인" in joined or "개인" in joined or "혼자" in joined or "1 인" in joined:
        hits += 1
    return hits


def main() -> int:
    ensure_env_from_credentials()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIP: ANTHROPIC_API_KEY 미설정 (ALL_CREDENTIALS.json/환경변수 없음). 사장님 보고 후 대기.")
        return 2

    from litellm import completion, completion_cost

    model = select_model("code")
    system = _load_system_prompt()
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": DATASET_1_INPUT},
        ],
        max_tokens=800,
        temperature=0.3,
    )
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

    surface = str(data.get("surface_goal", ""))
    true_intent = str(data.get("true_intent", ""))
    constraints = data.get("hidden_constraints") or []
    confidence = float(data.get("confidence", 0) or 0)

    m_surface = _metric_surface(surface)
    m_true = _metric_true(true_intent)
    m_true_pass = all(m_true.values())
    c_hits = _metric_constraints([str(c) for c in constraints])
    m_constraints = c_hits >= 2
    overall = m_surface and m_true_pass and m_constraints

    report = {
        "model": model,
        "input": DATASET_1_INPUT,
        "raw": raw,
        "parsed": data,
        "metrics": {
            "surface_pass": m_surface,
            "true_intent_groups": m_true,
            "true_intent_pass": m_true_pass,
            "constraints_hits": c_hits,
            "constraints_pass": m_constraints,
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
    out_path = ROOT / "docs" / ".intent_eval_001.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out_path} overall_pass={overall}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
