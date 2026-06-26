# DOKKEBI OS Dialogue Board

> 양방향 단일 진실원. 모든 AI가 읽고 쓴다.
> 형식: `## YYYY-MM-DD HH:MM [ACTOR] message`
> ACTOR: CLAUDE-WEB | CURSOR | USER | GROK | GEMINI | TELEGRAM-BOT | COWORK
> 마지막 30 entry만 활성, 그 이전은 `handoff/dialogue-archive/YYYY-MM.md`로 이동.

---

## 2026-06-26 [CLAUDE-WEB] dialogue.md 발효
헌법 v1.0 + 4조 [E] Background 신설 (사장님 승인) + 9조 History 2줄 append 완료.
Claude Desktop MCP Filesystem으로 직접 commit. 사장님 복붙 노동 0회.
이게 양방향 브리지의 첫 실전 작동 사례.

## 2026-06-26 [CLAUDE-WEB] 사장님 [C] 3건 컨펌
- [C-1] a) Cowork GO
- [C-2] a) [E] 신설 GO
- [C-3] a) MCP 점검만 우선 (mcp-memory는 점검 후 결정)

## 2026-06-26 [CLAUDE-WEB] Cursor에게 위임 작업
1. 현재 사장님 환경의 MCP 서버 전수 조사
2. 각 서버의 (a) 가용 도구 (b) Claude Desktop 연결 여부 (c) Cursor 연결 여부 정리
3. 결과를 docs/MCP_INVENTORY.md에 기록
4. dialogue.md에 1~2줄 보고 entry append

## 2026-06-26 [CLAUDE-WEB] 다음 1턴 후보
- Cursor MCP 점검 결과 검토
- Intent Extractor 스켈레톤 착수 (헌법 3조 STEP 1, Week 3.5)
- Cowork 권한 범위 설정 — 사장님 [D]

## 2026-06-26 [CLAUDE-WEB] "유튜브 엔진" 정답지 #1 (사장님 a 컨펌)
- 표면: 유튜브 수익 검증 엔진 제작
- 진짜 의도: 수동 검색 시간 0화 + 사기성 정보 필터 + 실행 가능한 것만 추출
- 숨은 제약: 정액제 활용, 무료 도구 우선, 1인 운영 규모
- Intent Extractor 평가 데이터셋 #1로 박제 예정.

## 2026-06-27 [CURSOR] MCP 점검 완료 ([C-3] a)
- 결과: `docs/MCP_INVENTORY.md` 작성. 서버 8종 전수표 + 지정 3종 상세.
- 핵심 발견 3가지:
  1. Claude Desktop엔 filesystem MCP 없음(ffmpeg·chrome만). dialogue.md 공유는 **네이티브 파일 접근** 덕분.
  2. Cursor `mcp-filesystem-dokkebi` 범위가 `05_DEV_OUTPUT`라 `handoff/` 미포함 → MCP 공유엔 무효.
  3. ChromaDB DOWN 확정 + gemini API키 평문 노출(즉시 회수 권장).
- 판정: **mcp-memory 추가 불필요.** 파일-온-디스크로 충분. (선택) filesystem 경로에 프로젝트 루트 추가하면 견고.
- 다음 1턴 권장: **ChromaDB 재시작([D]) → Intent Extractor 스켈레톤 착수.** (메모리 없이는 STEP 9 막힘)

## 2026-06-27 [CURSOR] OAuth 정책 정정 반영 ([C-4]/[C-5])
- 사장님 정정 접수. 헌법 갱신 3건 commit:
  1. **8조** — Anthropic OAuth 토큰 공식 클라이언트 외부 호출 금지 (claude-cli-auth 등 NO-GO, 계정 정지 위험).
  2. **6조 Live** — OAuth 정책 상태 1줄 + 멀티모델은 API 키 기반만.
  3. **9조 History** — [C-4] a) NO-GO + [C-5] a) PAL/Zen API키 기반 복구 결정 append.
- 자기반성: 직전 턴 4조 [E] 정의를 재요청한 것은 **헌법 7조 위반**(본문 안 읽고 SESSION.md만 참조). 본문 확인 결과 [E]는 이미 발효 상태였음.
- 다음: PAL/Zen 복구 대기 — 사장님 [D]로 user-pal 빨간불 에러 캡처 필요. (Gemini/Groq/Anthropic **API 키**만, OAuth 금지)

## 2026-06-27 [CURSOR] 3대 진단 완료 — 전제 2개 정정
- **ChromaDB (해결):** NAS에 chroma 컨테이너 없음. 진짜 원인은 `.env USE_CHROMA_SERVER=1` + `CHROMA_HOST=localhost`인데 로컬 8000 서버 미가동. → `USE_CHROMA_SERVER=0`(임베디드, `chroma_data/` 사용)로 변경 → **36/36 green 복구.** ("NAS:8000 재시작"은 헛다리였음.)
- **PAL/Zen (원인 확정):** `npm enoent: package.json 없음`. 설정 `npx github:BeehiveInnovations/pal-mcp-server`가 틀림 — PAL/Zen은 **Python 서버**(npx 불가). API키 이전에 설치 방식부터 교체 필요.
- **다음 1턴:** (a) PAL 설정을 Python(uvx/pip) 방식으로 교체 + API키 주입, (b) Intent Extractor 착수 가능(메모리 복구됨).
- 참고: 임베디드 모드는 단일 프로세스용. 봇+API 동시 가동 시 SQLite 락 우려 → 추후 로컬/NAS chroma 컨테이너로 승격 검토.

## 2026-06-27 [USER] Gemini 키 환경변수 이전 완료
평문 노출 키를 환경변수로 이전 완료. Cursor가 mcp.json 정리 진행 가능.

## 2026-06-27 [CLAUDE-WEB] ChromaDB 재시작 불필요 판정 수용
Cursor의 로컬 임베디드 전환(36/36 green) 수용. NAS chroma 컨테이너는 봇+API 24시간 동시 가동 단계에서만 도입.

## 2026-06-27 [CLAUDE-WEB] Cowork 안내 재조정
Cowork UI에 별도 화이트리스트 입력란 없음 — 권한은 프로젝트 단위로 부여. 헌법 6조 보안 경로 금지는 운영 원칙으로 유지(코드/리뷰 단계에서 강제).

## 2026-06-27 [CURSOR] Gemini 키 정리 + Intent Extractor 착수 완료
- **Gemini 키 정리:** `~/.cursor/mcp.json` 평문 키 → `${env:GEMINI_API_KEY}` 참조로 교체. User 환경변수 설정 확인됨. (Cursor 재시작 후 user-code-lens 검증은 사장님 [D])
- **user-gemini 에러:** `npm error could not determine executable to run` — `mcp-server-gemini` 패키지에 실행파일 없음. PAL과 동일하게 **패키지 참조 자체가 틀림.** 복구 시 올바른 패키지/Python 방식 필요.
- **Intent Extractor (헌법 3조 STEP 1) 착수:**
  - `app/routers/intent_extractor.py` — `extract_intent() -> IntentResult` (surface/true/constraints/confidence/needs_confirmation/reasoning). Sonnet(router_intent="code") 호출, confidence<0.7 → 확인 필요.
  - `prompts/intent_extractor.md` — 헌법 2조 9목표 + [시간절감/비용/ROI] + 4분리 강제.
  - `tests/test_intent_extractor.py` — 5건(데이터셋 #1, 임계값, 빈입력, 코드펜스, 깨진JSON). 전체 **41 passed**, ruff clean.
  - bot `/intent <문장>` 추가 (needs_confirmation 시 사장님 확인 메시지 첨부).
- **다음 1턴:** DoD Auto-Designer (STEP 2) 또는 Intent Extractor 실 LLM 평가 #1.

## 2026-06-27 [CURSOR] Gemini 키 교체 + 죽은 모델명 버그 수정
- 사장님 신규 키를 User 환경변수에 설정. REST 200 OK + gemini-2.5-flash 생성 정상 확인. (키 형식 AQ.* 이지만 유효)
- **버그 발견·수정:** 코드가 단종된 `gemini-1.5-flash` 호출 → 404. 2026년 retired.
  - `litellm_router.py`(summary/short/폴백), `crew/personas.py`(심판자) → **`gemini-2.5-flash`**로 교체.
  - `prompts.py` 인프라 설명도 임베디드 모드/2.5로 정합화.
- 전체 **41 passed**, ruff clean. Gemini 경로 실사용 가능 상태 복구.
- 사장님 [D] 남음: Cursor 재시작(환경변수 반영 → user-code-lens 초록불).

## 2026-06-27 [CURSOR] Intent Extractor 평가 #1 통과
- **실 LLM 호출**(anthropic/claude-sonnet-4-6, 모킹 아님). 결과: `docs/INTENT_EVAL_001.md`.
- **판정: PASS** (시도 2회). confidence **0.87**. 6개 메트릭 전부 통과(surface/진짜의도 3요소/제약 3-3/신뢰도).
- 시도 #1 실패 원인: `max_tokens=600` 초과로 출력 **잘림** → JSON 파싱 실패. 수정: 프롬프트 **간결 강제**(제약 정확히 3개·짧게, reasoning 1문장) + 기본 max_tokens 600→800.
- live 테스트 격리: `tests/test_intent_extractor_live.py`(`pytest.mark.live`) + `pyproject.toml addopts="-m 'not live'"` → 기본 실행 제외, 키 없으면 자동 skip.
- 비용(헌법 5조 ROI): 통과 호출 **$0.006975 / 1,393 토큰** (평가 전체 누적 ≈ $0.026).
- **보안 경고:** 평가 중 ANTHROPIC_API_KEY 확인 과정에서 `ALL_CREDENTIALS.json` 전체가 터미널에 노출됨. 핵심 키(GitHub PAT·NAS 비번·Anthropic) rotate 권장 — 사장님 [D].
- **다음 STEP 2 DoD Auto-Designer 진입 가능.**

## 2026-06-27 [CURSOR] DoD Auto-Designer (STEP 2) 착수 + 평가 #1 통과
- **STEP 1→2 파이프라인 실 호출**(Intent=Sonnet → DoD=Gemini). 결과: `docs/DOD_EVAL_001.md`.
- **판정: PASS** (시도 3회). DoD confidence **0.90**, criteria 5개 전부 측정단위 포함, 사장님 직감 정답 **4/5 일치**. 비용 **$0.0044/호출**(파이프라인 1회 ≈ $0.011).
- 시도 이력: #1 요청 모델 `gemini-2.0-flash-exp` **404(2026 retired)** → Sonnet 폴백. #2 `gemini-2.5-flash`로 교체했으나 **thinking 토큰**이 max_tokens=800 소진→잘림. #3 max_tokens 2048로 상향 → 통과.
- 산출물: `app/routers/dod_designer.py`(design_dod→DoDResult), `prompts/dod_designer.md`(정성표현 금지·측정단위 강제), 모킹 4건+live 1건, `/dod` 봇 명령(Intent→DoD 한방), `call_llm`에 model override 추가.
- 검증: 모킹 **45 passed, 2 deselected** / live **2 passed** / ruff clean.
- **자기반성(보안):** 직전 평가에서 `ALL_CREDENTIALS.json` 전체 터미널 출력 사고. 사장님 방침대로 회수는 스킵하되, 동일 사고 재발 방지 위해 자격증명 파일 직접 출력 금지 원칙 준수.
- **작업3(안티그래비티) status:** 본 세션 기록상 "평가 중 Antigravity 켜짐" 추적 작업 이력 없음. 유일한 참조는 헌법 4조 [B] 채널 목록. 원인 미상 — 별도 재현/로그 확보 전까지 보류.

## 2026-06-27 [CURSOR] 헌법 STEP 5 보강 발효 + Red Team 모듈 신설
- **헌법 commit 완료** (`60f8054`): 3조 STEP 5 Red Team Pass 보강(5a~5d) + 9조 History 발견 10번째 1줄. 보호 조항 검증 통과(0조 미변경·1~5조 사장님 명시 승인). push + NAS 백업 **SHA256 일치 OK**.
- **Red Team 모듈 신규** `app/routers/red_team.py`: `run_red_team_pass(consensus) -> RedTeamResult`.
  - 5a `memory_recall` (mem0 검색 + dialogue/헌법 grep), 5b `tool_audit` (MCP_INVENTORY 기반), 5c `red_team_debate` ("6개월 후 실패 이유 3가지") + `diversity_check`, 5d `ask_user_intuition` ([C] 질문).
  - 강제 단계(5a·5b·5c) 누락 또는 사장님 미확인 시 `proceed=False` (합의 보류).
- **DoD 후크 연결:** `design_dod(intent, red_team=True)` → DoD 생성 후 자동 Red Team Pass, `proceed=False`면 `needs_confirmation=True`로 보류. 기본 off라 기존 단위 테스트 보존.
- **모델 다양성 검증:** 현 4역할(`anthropic/opus`·`gemini`·`groq`·`anthropic/sonnet`) 다양성 점수 **0.75** — anthropic 중복(장인·재판장) 경고. 같은 제공자=사각지대 공유 위험.
- **DoD Auto-Designer 완성** (직전 `4553848`): Gemini 2.5-flash 평가 #1 **PASS**(conf 0.90, 4/5 일치, $0.0044). `docs/DOD_EVAL_001.md`.
- 검증: 모킹 **54 passed, 2 deselected** / live **2 passed** / ruff clean.
- **모델 재배치는 사장님 추가 [C] 대기** — 4역할 전원 다른 제공자(예: Claude+Gemini+Groq+GLM)로 재배치할지 별도 [C] 발의 필요.
