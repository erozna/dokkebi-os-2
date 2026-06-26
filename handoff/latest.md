# DOKKEBI OS Handoff — latest

> 항상 최신 상태. 매 Sprint 종료 시 갱신.
> 부팅: `@CONSTITUTION.md @handoff/latest.md 읽고 진행`

## 마지막 결정 사항
- 헌법 v1.0 발효 (`CONSTITUTION.md`, 0조 최상위 + 1~9조)
- 4-Way Router 도입 ([A] Auto / [B] Bridge / [C] Ask / [D] Hands)
- Week 3.5~3.9 인지 레이어 구축 결정 / Week 3 Tauri 일시 보류
- 세션 인계 문서 = `handoff/latest.md` (committed), Bridge 런타임은 `handoff/bridge/`로 분리

## 다음 1턴 액션
- Intent Extractor 스켈레톤 작성 (Week 3.5)
- Capability Router([A]~[D]) 코드화 검토
- Mission Memory 9 → SHARED_BRAIN 동기화 (완료, 재확인만)

## 미해결 질문 (사장님 답변 대기)
- Canonical Flow 9단계(헌법 3조) 중 직감에 어긋나는 STEP?
- Tauri 작업 vs 인지 레이어 — 순차 vs 병렬?
- userPreferences에 "매 세션 헌법+handoff 자동 로드" 1줄 추가할지 ([D-3])

## 사장님 즉시 실행 [D]
- userPreferences 1줄 추가 여부 결정 (Claude 영구 메모리 — 도깨비가 못 건드림)
- NAS 백업 1회 (단일 실패점 방어: GitHub+Synology 완료, NAS 미설정)
- 부팅 명령 즐겨찾기 저장

## 다음 세션 부팅 명령
@CONSTITUTION.md @handoff/latest.md 읽고 진행. 마지막 상태 + 다음 1턴 액션 1줄 보고.
