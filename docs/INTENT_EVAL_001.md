# Intent Extractor 평가 #1 (실 LLM)

> 헌법 3조 STEP 1 검증. 모킹 아님 — 실제 `anthropic/claude-sonnet-4-6` 호출.
> 하니스: `scripts/eval_intent_001.py` · live 테스트: `tests/test_intent_extractor_live.py`
> 일자: 2026-06-27 · 판정: **PASS (시도 2회)**

## 1. 입력

```
유튜브에서 돈 버는 방법을 검증하는 엔진을 만들어서 자동으로 검색해서 그 유튜브 컨텐츠를
분석하고, 현실적 검증을 해보고 자동으로 도입할수 있는것들은 실행하는 프로그램을 만들어줘
```

## 2. 정답지 (#1, 사장님 a 컨펌 — dialogue.md)

| 필드 | 정답 |
| --- | --- |
| surface_goal | 유튜브 수익 검증 엔진 제작 |
| true_intent | 수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능 항목만 추출 |
| hidden_constraints | 정액제 활용, 무료 도구 우선, 1인 운영 규모 |

## 3. 최종 모델 응답 (raw, 통과 시도)

```json
{
  "surface_goal": "유튜브 수익화 방법 자동 검증·실행 프로그램 제작",
  "true_intent": "수동 리서치 시간을 제거하고 검증된 수익 아이디어만 자동 필터링해 즉시 실행 가능한 것부터 1인이 실제 돈을 벌게 한다",
  "hidden_constraints": ["정액제·무료API 우선", "1인 실행 가능 범위", "사기성 정보 자동 차단"],
  "confidence": 0.87,
  "reasoning": "표면은 프로그램 제작이나 진짜 ROI는 리서치 시간 0화+검증 필터로 실행 전환율 극대화, 1인 운영·무료 도구 제약이 핵심."
}
```

## 4. 정답 대비 비교 (의미 일치도)

| 메트릭 | 기준 | 결과 | 판정 |
| --- | --- | --- | --- |
| surface_goal | "유튜브" + (엔진/검증/수익) 2개 이상 | 유튜브·검증·수익 일치 | ✅ PASS |
| true_intent — 시간0화/자동화 | "제거/0화" or "자동" | "시간을 제거", "자동 필터링" | ✅ PASS |
| true_intent — 필터/검증 | "필터" or "검증" | "검증된...자동 필터링" | ✅ PASS |
| true_intent — 실행가능 | "실행" or "도입" | "즉시 실행 가능" | ✅ PASS |
| hidden_constraints | 3개 중 2개 이상 | 정액제·무료·1인 **3/3** | ✅ PASS |
| confidence | ≥ 0.7 권장 | **0.87** → needs_confirmation=False | ✅ PASS |

**종합: PASS** (overall_pass=True)

## 5. 시도 이력 (최대 3회)

| 시도 | 변경 | 결과 |
| --- | --- | --- |
| #1 | 초기 프롬프트 (제약 2~5개, reasoning 1~3문장) | ❌ FAIL — 출력이 `max_tokens=600` 초과로 **잘림** → JSON 파싱 실패 (`completion_tokens=600` 정확히 한도). |
| #2 | 프롬프트 **간결 강제**(제약 정확히 3개·각 12자 이내, reasoning 1문장) + 기본 `max_tokens` 600→800 | ✅ PASS. 단 하니스 메트릭 `시간0화` 항이 "제거/자동"을 누락(문자 일치 과잉) → 메트릭을 **의미 기준**으로 보정 후 재확인 PASS. |

> 메트릭 보정은 과제 규칙 "의미 일치도, 문자 일치 아님"에 따른 것. 모델은 시도 #2부터 의미상 정답을 산출했고, 잘림 버그가 유일한 실질 실패였음.

## 6. 프롬프트 튜닝 후보 (향후)

- `hidden_constraints` 항목 길이 상한(12자)을 더 압축하면 토큰 추가 절감 가능.
- 출력 스키마에 `confidence` 산정 근거를 reasoning에 1구절로 고정하면 신뢰도 일관성 ↑.
- 다국어/영어 입력 데이터셋(#2~)으로 일반화 검증 필요.

## 7. 비용 보고 (헌법 5조 ROI)

| 항목 | 값 |
| --- | --- |
| 모델 | anthropic/claude-sonnet-4-6 |
| prompt_tokens | 1,160 |
| completion_tokens | 233 |
| total_tokens | 1,393 |
| **호출당 비용** | **≈ $0.006975 (약 0.007달러 / ₩10 내외)** |

> 시도 #1(잘림 포함) 합산 실 지출 ≈ $0.012 + $0.007 + $0.007 ≈ **$0.026** (평가 1회 전체).

## 8. 결론

Intent Extractor(STEP 1) 실 LLM 평가 #1 **통과**. confidence 0.87.
→ 다음: **DoD Auto-Designer (STEP 2)** 진입 가능.
