# DoD Auto-Designer 평가 #1 (실 LLM)

> 헌법 3조 STEP 2 검증. 모킹 아님 — Intent Extractor 출력을 그대로 입력으로 받는 **STEP 1→2 파이프라인** 실 호출.
> 하니스: `scripts/eval_dod_001.py` · live 테스트: `tests/test_dod_designer_live.py`
> 일자: 2026-06-27 · 판정: **PASS (시도 3회)**

## 1. 입력 (STEP 1 Intent 출력 → STEP 2 DoD 입력)

| Intent 필드 | 값 (실 추출) |
| --- | --- |
| surface_goal | 유튜브 수익화 방법 자동 검색·분석·실행 프로그램 제작 |
| true_intent | 수동 정보 탐색·검증 시간을 0으로 줄이고, 사기성 콘텐츠를 필터링해 1인 사업에 즉시 도입 가능한 수익 액션만 자동 추출·실행 |
| hidden_constraints | 정액제 API 우선 / 무료 오픈소스 활용 / 1인 자동화 범위 |
| confidence | 0.78 |

## 2. 사장님 직감 정답 후보 (검증용, 일치도만 측정)

1. 주 100개 영상 자동 수집 + 사기 필터 정확도 80%+
2. 실행 가능 항목 주 3건 추출
3. 사장님 검토 시간 회당 10분 이하
4. 월 운영 비용 무료 tier 내 유지
5. 발견된 수익 모델 1건 도입까지 평균 7일

## 3. 최종 모델 응답 (raw, 통과 시도 — gemini/gemini-2.5-flash)

```json
{
  "criteria": [
    "사장님의 주간 정보 탐색 및 검증 시간 0분 유지",
    "수집된 정보 중 사기성 콘텐츠 필터링 정확도 85% 이상 달성",
    "1인 사업에 즉시 도입 가능한 수익 액션 주 3건 이상 자동 추출",
    "추출된 수익 액션 1건의 실제 도입까지 평균 7일 이내 소요",
    "월 운영 비용 무료 tier 내 0원 유지"
  ],
  "measurable": true,
  "confidence": 0.9,
  "reasoning": "시간절감(탐색 0분, 도입 7일)과 비용 0원을 정량화하여 ROI 추적 기반 마련."
}
```

## 4. 정답 대비 비교 (의미 일치도, 문자 매칭 아님)

| # | 정답 후보 | 모델 산출 | 일치 |
| --- | --- | --- | --- |
| 1 | 주 100개 수집 + 필터 80% | 사기 필터 정확도 85% | ✅ |
| 2 | 실행 항목 주 3건 | 수익 액션 주 3건 이상 추출 | ✅ |
| 3 | 검토 회당 10분 이하 | (탐색 시간 0분 유지로 대체) | ❌ |
| 4 | 월 비용 무료 tier | 월 운영 비용 무료 tier 0원 | ✅ |
| 5 | 도입까지 7일 | 도입까지 평균 7일 이내 | ✅ |

**일치 4/5** (≥3 통과 기준) · criteria 개수 5 (3~5 OK) · 전 항목 측정단위 포함(measurable=True) · confidence 0.9

**종합: PASS** (overall_pass=True)

> 미일치 #3은 모델이 "검토 10분"보다 강한 "탐색 시간 0분 유지"로 시간절감을 표현한 것 — 의도상 더 공격적인 정량 목표. 누락이라기보다 상향 대체.

## 5. 시도 이력 (최대 3회)

| 시도 | 모델 | 변경 | 결과 |
| --- | --- | --- | --- |
| #1 | 요청 `gemini-2.0-flash-exp` → **Sonnet 폴백** | 초기 구현 | ✅(품질) 단 **요청 모델 실패**. 2.0-flash-exp 404(2026 retired) → 폴백 체인이 Sonnet으로 처리. |
| #2 | `gemini-2.5-flash` (모델 교체) | `_DOD_MODEL` 2.0-exp→2.5-flash | ❌ FAIL — 2.5-flash **thinking 토큰**이 `max_tokens=800` 예산 소진 → JSON **잘림**(completion 796) → 파싱 실패. |
| #3 | `gemini-2.5-flash` | 기본 `max_tokens` 800→**2048** (thinking+출력 수용) | ✅ PASS. criteria 5·measurable·일치 4/5·conf 0.9. |

## 6. 프롬프트 튜닝 후보 (향후)

- "검토 시간(분/회)" 축을 예시에 더 강조하면 사장님 직감 #3 항목 커버율 ↑.
- thinking 모델 비용 절감: LiteLLM `reasoning_effort` 하향 또는 thinking 비활성으로 completion 토큰 축소 검토.
- 영어/혼합 입력 데이터셋(#2~)으로 정량 단위 강제 일반화 검증.

## 7. 비용 보고 (헌법 5조 ROI)

| 항목 | 값 |
| --- | --- |
| 모델 | gemini/gemini-2.5-flash |
| prompt_tokens | 862 |
| completion_tokens | 1,674 (thinking 포함) |
| total_tokens | 2,536 |
| **호출당 비용** | **≈ $0.004444 (약 0.0044달러 / ₩6 내외)** |

> STEP 1(Intent, Sonnet) + STEP 2(DoD, Gemini) 파이프라인 1회 ≈ $0.007 + $0.0044 ≈ **$0.011**.
> 시도 누적(폴백·잘림 포함) 실 지출 ≈ **$0.015** 내외.

## 8. 결론

DoD Auto-Designer(STEP 2) 실 LLM 평가 #1 **통과**. Gemini 2.5-flash, confidence 0.9, 측정 가능 완료조건 5개.
→ 다음: **STEP 3 CrewAI 4역할 토론 진입** 또는 **운영 모델 결정 [C]**.
