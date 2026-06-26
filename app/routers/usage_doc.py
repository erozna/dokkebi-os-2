"""Usage Doc Auto-Gen — 헌법 3조 STEP 8.

FlowResult를 사장님 친화 마크다운으로 정리. **실행 결과 중심**:
1. 사장님께 발견된 것 (STEP 7-A 실행 결과)
2. 사장님 결정 필요 ([C] 라운드)
3. 자동화 가능한 것 (execution_strength 기반)
4. 다음 액션 (사장님 [C] 답변 시 진행)
5. 비용 + 시간 + ROI (헌법 5조)
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

_STRENGTH_LABEL = {
    "INFO_ONLY": "정보 제공",
    "CANDIDATE_LIST": "후보 추천",
    "OK_THEN_AUTO": "사장님 OK 후 자동 실행",
    "FULL_AUTO": "완전 자동",
}


def generate_usage_doc(flow) -> str:  # noqa: ANN001 — duck-typed FlowResult
    """FlowResult → 사장님 친화 마크다운 (실행 결과 중심)."""
    lines: list[str] = ["# 도깨비 작업 결과", ""]

    intent = getattr(flow, "intent", None)
    if intent is not None:
        lines.append(f"**진짜 의도:** {getattr(intent, 'true_intent', '') or '-'}")
        strength = getattr(flow, "execution_strength", "") or ""
        if strength:
            lines.append(f"**실행 강도:** {_STRENGTH_LABEL.get(strength, strength)}")
        lines.append("")

    routes = list(getattr(flow, "routes", None) or [])
    execs = list(getattr(flow, "executions", None) or [])
    pairs = list(zip(routes, execs))

    # 1. 사장님께 발견된 것 — 실제 실행([A]) 결과
    done = [(d, r) for d, r in pairs if r.status == "done"]
    lines.append("## 1. 발견된 것 (자동 실행 결과)")
    if done:
        for d, r in done:
            tool = f" `{getattr(r, 'tool', '')}`" if getattr(r, "tool", "") else ""
            lines.append(f"- ✅{tool} {r.detail[:110]}")
            if r.artifact_path:
                lines.append(f"  - 저장: `{r.artifact_path}`")
    else:
        lines.append("- 실증 데이터 없음. 화이트리스트 점검 필요 (yt-dlp/Tavily/ChromaDB/pytest).")
    lines.append("")

    # 2. 사장님 결정 필요 — [C] 라운드
    questions = list(getattr(flow, "questions", None) or [])
    ask_routes = [(d, r) for d, r in pairs if d.route in ("C", "D")]
    lines.append("## 2. 사장님 결정 필요 [C]")
    if questions or ask_routes:
        for q in questions:
            lines.append(f"- ❓ {q}")
        for d, r in ask_routes:
            if not r.question:
                lines.append(f"- ✋ [{d.route}] {d.task[:80]}")
    else:
        lines.append("- 없음 (자동 진행 가능)")
    lines.append("")

    # 3. 자동화 가능한 것
    auto = [(d, r) for d, r in pairs if d.route in ("A", "B")]
    lines.append("## 3. 자동화 가능한 것")
    if auto:
        for d, r in auto:
            label = _ROUTE_LABEL.get(d.route, d.route)
            lines.append(f"- [{d.route}] {label} — {d.task[:70]}")
    else:
        lines.append("- 후보 없음")
    lines.append("")

    # 4. 다음 액션
    lines.append("## 4. 다음 액션")
    if getattr(flow, "needs_confirmation", False):
        if questions:
            lines.append("- 위 질문에 답해 주시면 (예/아니오 또는 선택) 선택된 항목 자동화를 진행합니다.")
        else:
            lines.append("- 합의안/결과를 확인해 주세요.")
    else:
        lines.append("- 자동 처리 항목은 완료되었습니다. 사장님 손/결정 항목만 확인 부탁드립니다.")
    lines.append("")

    # 5. Red Team + 비용/시간/ROI (헌법 5조)
    rt = getattr(flow, "red_team", None)
    if rt is not None:
        div = getattr(rt, "diversity_score", 0.0)
        line = f"## 5. 검증 + 비용 (헌법 5조)\n- 모델 다양성: {div:.2f}"
        warn = getattr(rt, "diversity_warning", "")
        if warn:
            line += f" (⚠ {warn})"
        lines.append(line)
    else:
        lines.append("## 5. 검증 + 비용 (헌법 5조)")
    cost = getattr(flow, "total_usd", 0.0)
    lines.append(f"- 비용: ${cost:.4f}")
    lines.append(f"- ROI: 수동 리서치 시간 절감 → 발견 {len(done)}건 자동 수집")

    return "\n".join(lines)
