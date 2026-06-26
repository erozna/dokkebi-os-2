# DOKKEBI OS Handoff — SESSION (latest)

> 항상 최신 상태. 매 Sprint 종료 시 갱신.
> 부팅: `@CONSTITUTION.md @handoff/SESSION.md 읽고 진행`

## 마지막 결정 사항
- 헌법 3조 Canonical Flow 9단계 **원문 복원 완료** (STEP 0~9)
- **3중 백업 완성**: GitHub + Synology Drive + NAS (`\\192.168.1.3\home\dokkebi_backup\constitution\`, SHA256 일치 확인)
- 세션 인계 문서 = `handoff/SESSION.md` (committed) / Bridge [B] 산출물 = `handoff/bridge-<timestamp>.md` (gitignored) — 역할 분리
- 헌법 0조(최상위, 변경 불가) 발효

## 다음 1턴 액션
- **Intent Extractor 스켈레톤 작성** (헌법 3조 STEP 1, Week 3.5)
- Capability Router([A]~[D]) 코드화 검토

## 미해결 질문 (사장님 답변 대기)
- Canonical Flow 9단계(헌법 3조) 중 직감에 어긋나는 STEP?
- Tauri 작업 vs 인지 레이어 — 순차 vs 병렬?

## 사장님 즉시 실행 [D]
- [D-3] userPreferences에 "DOKKEBI OS 작업 시작 시 CONSTITUTION.md + handoff/SESSION.md 먼저 읽기" 1줄 추가 (Claude 설정 → 개인화)
- 부팅 명령 즐겨찾기 저장

## 다음 세션 부팅 명령
@CONSTITUTION.md @handoff/SESSION.md 읽고 진행. 마지막 상태 + 다음 1턴 액션 1줄 보고.
