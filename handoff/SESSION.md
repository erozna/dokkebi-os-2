# DOKKEBI OS Handoff — 2026-06-26

> 세션 간 인계 표준. 부팅: `@CONSTITUTION.md @handoff/SESSION.md 읽고 진행`

## 마지막 결정 사항
- 헌법 v1.0 발효 (`CONSTITUTION.md`)
- 4-Way Router 도입 ([A] Auto / [B] Bridge / [C] Ask / [D] Hands)
- Week 3.5~3.9 인지 레이어 구축 결정
- Week 3 Tauri 작업 일시 보류
- Subscription Bridge로 정액제(Claude/Gemini 웹) + Cursor 활용, API 비용 최소화

## 현재 상태 (Live)
- 마지막 커밋: `2f6f84c`
- pytest: 36/36 green, ruff clean
- repo: main, PUBLIC, branch protection ON
- 봇/API: 필요 시 재기동 (uvicorn 127.0.0.1:8765, telegram polling)

## 다음 1턴 액션
- Mission Memory 9가지 → SHARED_BRAIN 영구 저장 (선택)
- Intent Extractor 스켈레톤 작성 (Week 3.5)
- Capability Router([A]~[D]) 코드화 검토

## 미해결 질문 (사장님 답변 대기)
- Canonical Flow 9단계(3조) 중 직감에 어긋나는 부분?
- Tauri 작업 vs 인지 레이어 — 순차 vs 병렬?
- userPreferences에 "매 세션 헌법+handoff 자동 로드" 1줄 추가할지 ([D-3])

## 사장님 즉시 실행 [D]
- (완료) CONSTITUTION.md, handoff/SESSION.md 생성 — Cursor가 처리함
- (사장님) userPreferences 1줄 추가 여부 결정 ([D-3])
- (사장님) 부팅 명령 즐겨찾기 저장

## 다음 세션 부팅 명령
@CONSTITUTION.md @handoff/SESSION.md 읽고 진행. 마지막 상태 + 다음 1턴 액션 1줄 보고.
