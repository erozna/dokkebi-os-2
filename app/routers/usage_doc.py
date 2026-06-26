"""Usage Doc Auto-Gen — 헌법 3조 STEP 8.

FlowResult를 사장님 친화 마크다운(결과 + 사용법 + 다음 액션)으로 정리.
순환 import 방지를 위해 FlowResult를 duck-typing으로 받는다.
"""

from __future__ import annotations

_ROUTE_LABEL = {
    "A": "도깨비 자동",
    "B": "복붙(정액제)",
    "C": "사장님 결정",
    "D": "사장님 손",
    "E": "백그라운드",
}


def generate_usage_doc(flow) -> str:  # noqa: ANN001 — duck-typed FlowResult
    """FlowResult → 사장님 친화 마크다운."""
    lines: list[str] = ["# 도깨비 작업 결과", ""]

    intent = getattr(flow, "intent", None)
    if intent is not None:
        lines += [f"**진짜 의도:** {getattr(intent, 'true_intent', '') or '-'}", ""]

    consensus = getattr(flow, "consensus", None) or []
    if consensus:
        lines.append("## 합의된 완료조건")
        lines += [f"{i}. {c}" for i, c in enumerate(consensus, 1)]
        conf = getattr(flow, "confidence", 0.0)
        lines += ["", f"확신도: {conf:.2f}", ""]

    routes = getattr(flow, "routes", None) or []
    execs = getattr(flow, "executions", None) or []
    if routes:
        lines.append("## 작업 분류 + 처리")
        for d, r in zip(routes, execs):
            label = _ROUTE_LABEL.get(d.route, d.route)
            lines.append(f"- **[{d.route}] {label}** — {d.task[:70]}")
            lines.append(f"  - 처리: {r.status} · {r.detail[:90]}")
            if r.artifact_path:
                lines.append(f"  - 산출: `{r.artifact_path}`")
        lines.append("")

    # 사장님 액션 필요 항목 (C/D)
    actions = [
        (d, r) for d, r in zip(routes, execs) if d.route in ("C", "D") or r.question
    ]
    if actions:
        lines.append("## 사장님 액션 필요")
        for d, r in actions:
            if r.question:
                lines.append(f"- ❓ {r.question}")
            else:
                lines.append(f"- ✋ {d.task[:80]}")
        lines.append("")

    rt = getattr(flow, "red_team", None)
    if rt is not None:
        div = getattr(rt, "diversity_score", 0.0)
        lines += ["## Red Team", f"- 모델 다양성: {div:.2f}"]
        warn = getattr(rt, "diversity_warning", "")
        if warn:
            lines.append(f"- ⚠ {warn}")
        lines.append("")

    if getattr(flow, "needs_confirmation", False):
        lines += ["## 다음 액션", "위 합의안/질문을 확인해 주세요. (예/아니오 또는 결정)", ""]
    else:
        lines += ["## 다음 액션", "자동 처리 가능 항목은 진행되었습니다. 사장님 손/결정 항목만 확인 부탁드립니다.", ""]

    cost = getattr(flow, "total_usd", 0.0)
    lines.append(f"_비용: ${cost:.4f}_")
    return "\n".join(lines)
