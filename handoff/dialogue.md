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
