# DOKKEBI OS Handoff — SESSION (latest)

> 항상 최신 상태. 매 Sprint 종료 시 갱신.
> 부팅: `@CONSTITUTION.md @handoff/SESSION.md 읽고 진행`

## 마지막 결정 사항
- 헌법 3조 Canonical Flow 9단계 **원문 복원 완료** (STEP 0~9)
- **3중 백업 완성**: GitHub + Synology Drive + NAS (`\\192.168.1.3\home\dokkebi_backup\constitution\`, SHA256 일치 확인)
- 세션 인계 문서 = `handoff/SESSION.md` (committed) / Bridge [B] 산출물 = `handoff/bridge-<timestamp>.md` (gitignored) — 역할 분리
- 헌법 0조(최상위, 변경 불가) 발효
- **2026-06-26 (당일 후반) — Claude Desktop MCP Filesystem 양방향 브리지 발효.** 사장님 복붙 노동 95%+ 감소 단계 진입.
- **헌법 4조 [E] Background 분류 신설** (Claude Cowork 활용 기반, 사장님 [C-2] 승인).
- **handoff/dialogue.md 발효** — Claude와 Cursor가 공유하는 단일 진실원 칠판.
- 사장님 [C] 3건 컴펙: [C-1] a) Cowork GO / [C-2] a) [E] 신설 / [C-3] a) MCP 점검만 우선.

## 다음 1턴 액션
1. **(완료) Intent Extractor 스켈레톤** — `app/routers/intent_extractor.py` + `prompts/intent_extractor.md` + `/intent` 봇 명령 + 테스트 5건. 데이터셋 #1 통과.
2. **(완료) Intent Extractor 실 LLM 평가 #1** — 실 Sonnet 호출 **PASS** (confidence 0.87, $0.007/호출). 결과 `docs/INTENT_EVAL_001.md`.
3. **(완료) DoD Auto-Designer (STEP 2) + 평가 #1** — Gemini 2.5-flash **PASS** (confidence 0.90, criteria 5개·측정단위 100%, 정답 4/5, $0.0044/호출). 결과 `docs/DOD_EVAL_001.md`. `/dod` 봇 파이프라인(Intent→DoD) 추가.
4. **다음: STEP 3 CrewAI 4역할 토론 진입 또는 운영 모델 결정 [C]** — DoD 완료조건을 받아 4역할(설계/검증/레드팀/심판) 토론으로 실행안 확정.
5. (보류) 보안 키 회수 — 사장님 방침: 1인 로컬 환경 위험 낮음으로 **스킵**. 자격증명 파일 직접 출력 금지 원칙만 유지.
6. (선택 [D]) PAL/Zen 복구 — 설정을 Python(uvx) 방식으로 교체 + API키. 현재 npx 참조라 실패 중.

## 미해결 질문 (사장님 답변 대기)
- Canonical Flow 9단계(헌법 3조) 중 직감에 어긋나는 STEP?
- Tauri 작업 vs 인지 레이어 — 순차 vs 병렬?

## 사장님 즉시 실행 [D]
- [D-3] userPreferences에 "DOKKEBI OS 작업 시작 시 CONSTITUTION.md + handoff/SESSION.md 먼저 읽기" 1줄 추가 (Claude 설정 → 개인화)
- 부팅 명령 즐겨찾기 저장

## 다음 세션 부팅 명령
```
@CONSTITUTION.md @handoff/SESSION.md @handoff/dialogue.md 읽고 진행. 마지막 상태 + 다음 1턴 액션 1줄 보고.
```
