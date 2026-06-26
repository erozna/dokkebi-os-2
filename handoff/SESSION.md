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
3. **(완료) DoD Auto-Designer (STEP 2) + 평가 #1** — Gemini 2.5-flash **PASS** (confidence 0.90, criteria 5개·측정단위 100%, 정답 4/5, $0.0044/호출). 결과 `docs/DOD_EVAL_001.md`. `/dod` 봇 파이프라인(Intent→DoD→STEP5) 추가.
4. **(완료) 헌법 STEP 5 보강 발효 + Red Team 모듈** — `60f8054` push + NAS SHA256 OK. `app/routers/red_team.py`(5a~5d) + DoD `red_team=True` 후크 + 다양성 검증(현 점수 0.75).
5. **(완료) STEP 3 CrewAI 4역할 토론 본 구현 + 평가 #1** — 장인→심판자→검사관→재판장 순차 토론 → 합의안 → Red Team. 실 LLM 평가 **PASS** (테마 5/5, confidence 0.80, $0.0576/회). `app/routers/crew_debate.py` + `jangin_via_cowork.py` + `prompts/{jangin,simpanja,geomsakwan,jaepanjang}.md` + `/debate` 봇 한방 파이프라인. 결과 `docs/DEBATE_EVAL_001.md`. 모킹 4건 + live 1건 통과. (전체 58 passed, ruff clean)
6. **다음 1턴 액션 (택1):**
   - (a) **STEP 4 Tech Radar 강화** — Tavily로 "만들 것 vs 가져올 것" 자동 분리.
   - (b) **STEP 7 Execution 분기** — 합의안 → Capability Router([A]~[E]) → 실행.
7. (보류) 보안 키 회수 — 사장님 방침: 1인 로컬 환경 위험 낮음으로 **스킵**. 자격증명 파일 직접 출력 금지 원칙만 유지.
8. (선택 [D]) PAL/Zen 복구 — 설정을 Python(uvx) 방식으로 교체 + API키. 현재 npx 참조라 실패 중.

## 미해결 질문 (사장님 답변 대기)
- Canonical Flow 9단계(헌법 3조) 중 직감에 어긋나는 STEP?
- Tauri 작업 vs 인지 레이어 — 순차 vs 병렬?

## 사장님 즉시 실행 [D]
- [D-3] userPreferences에 "DOKKEBI OS 작업 시작 시 CONSTITUTION.md + handoff/SESSION.md 먼저 읽기" 1줄 추가 (Claude 설정 → 개인화)
- 부팅 명령 즐겨찾기 저장
- [D-4] **`ZAI_API_KEY` 설정** — 현재 미설정으로 심판자(GLM)가 anthropic 폴백 → 런타임 다양성 저하. 키 설정 시 진짜 4제공자(헌법 명시 1.0) 동작.
- [D-5] (선택) **장인 Cowork 수동 트리거** — `/debate`는 기본 장인=Claude Sonnet API. Cowork 사용 시 `run_debate(use_cowork=True)` → `handoff/round-N-jangin.md` 생성됨 → Claude Desktop Cowork로 처리 후 `round-N-jangin.result.md` 작성(미작성 시 5분 후 Gemini Pro 폴백).

## 다음 세션 부팅 명령
```
@CONSTITUTION.md @handoff/SESSION.md @handoff/dialogue.md 읽고 진행. 마지막 상태 + 다음 1턴 액션 1줄 보고.
```
