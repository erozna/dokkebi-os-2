# MCP Inventory — 2026-06-27 (Cursor 점검, 헌법 [C-3] a)

> 출처: `%APPDATA%\Claude\claude_desktop_config.json`, `~/.cursor/mcp.json`, MCP STATUS 캐시.
> 점검자: CURSOR. 목적: handoff/dialogue.md 양방향 공유 충분성 판정 + mcp-memory 필요성.

## 전수 목록

| 서버 | Claude Desktop | Cursor | 상태 | 가용 도구(요약) | 경로/리소스 |
|------|:---:|:---:|------|------|------|
| **mcp-filesystem-dokkebi** | ✗ | ✓ | 작동 | read/write/edit/move/search 등 14종 | `D:\...\DOKKEBI_CORE\05_DEV_OUTPUT` (⚠ 프로젝트 루트 아님) |
| **DOKKEBI** | ✗ | ✓ | 작동 | check_inbox, inbox_drop, kanban_read/done, notifications, system_status | 로컬 python (`05_DEV_OUTPUT/py`) |
| **synology-mcp** (=dokkebi-nas) | ✗ | ✓ | 에러 | (미로드) | SSH → NAS `/volume1/ai-data/mcp-server-synology` docker |
| code-lens | ✗ | ✓ | 작동 | ask_about_code, verify_logic, web_search, refactor 등 13종 (**Gemini 기반**) | npx `@j0hanz/code-lens-mcp` |
| gemini | ✗ | ✓ | 에러 | (미로드) | npx `mcp-server-gemini` (⚠ API키 평문) |
| pal (PAL/Zen) | ✗ | ✓ | 에러 | (미로드) — 크로스모델 오케스트레이션 | npx `github:BeehiveInnovations/pal-mcp-server` |
| ffmpeg-mcp | ✓ | ✓ | 에러 | (미로드) | uvx `ffmpeg-mcp` |
| chrome-devtools-mcp | ✓ | ✓ | 작동 추정 | 브라우저 제어 | npx `chrome-devtools-mcp` |

범례: ✓ 연결됨 / ✗ 미연결

## 상세 분석 (지정 3종)

### 1) mcp-filesystem-dokkebi
- **연결:** Cursor만. Claude Desktop ✗.
- **범위 문제(핵심):** 허용 경로가 `D:\SynologyDrive\dokkebi\DOKKEBI_CORE\05_DEV_OUTPUT` 로 고정.
  현재 프로젝트 루트 `D:\SynologyDrive\dokkebi\projects\shared-brain-day1` 와 **다른 트리.**
  → 이 서버로는 `handoff/dialogue.md` 에 **접근 불가.**
- **결론:** dialogue.md 공유 용도로는 **현 설정상 무효.** 경로 확장 또는 별도 서버 필요.

### 2) DOKKEBI
- **연결:** Cursor만. Claude Desktop ✗.
- **도구:** 칸반(kanban_read/done), 인박스(check_inbox/inbox_drop), 알림(notifications), 시스템 상태(system_status).
- **용도:** 도깨비 작업 큐/알림 허브. [D]·[E] 작업 큐와 연결 가능.
- **상태:** 작동.

### 3) synology-mcp (dokkebi-nas)
- **연결:** Cursor만. SSH로 NAS docker 컨테이너 기동.
- **상태:** **에러.** SSH 키/컨테이너/네트워크 중 하나 실패 추정. (ChromaDB와 동일 NAS — 아래 참조)
- **용도:** NAS 파일/리소스 접근.

## ChromaDB 헬스체크 (Critical Update 반영)
- `http://192.168.1.3:8000/api/v1/heartbeat` → **CHROMA_DOWN (연결 실패).**
- 영향: `test_supervisor_debate_route` 실패 원인 확정. Intent Extractor가 Mem0 호출 시 차단됨.
- 조치: **[D] 사장님** — NAS DSM에서 ChromaDB 컨테이너 재시작 필요.

## 보안 경고 (즉시 [D])
- `~/.cursor/mcp.json` 의 `gemini` 서버에 **GEMINI_API_KEY 평문 노출.**
- 권장: 키 **회수(rotate)** 후 환경변수/시크릿으로 이전. 이 문서·git에는 키 미기록.

## 판정 — mcp-memory 추가 설치 필요한가? (작업 3)

**결론: 추가 설치 불필요. 단, 경로 정합화 1건 필요.**

### 근거
1. **파일-온-디스크 방식이 이미 작동.** Claude Desktop은 **네이티브 파일 접근**(Cowork/내장 도구)으로,
   Cursor는 네이티브 파일 도구로, **둘 다 SynologyDrive 경로의 같은 파일을 직접** 읽고 쓴다.
   실제로 이 dialogue.md를 Claude가 직접 썼고 Cursor(나)가 직접 읽었다 → **공유 칠판은 MCP 없이도 성립.**
2. **MCP filesystem 서버는 공유에 기여 못 함.** Claude Desktop엔 filesystem MCP 자체가 없고,
   Cursor의 것은 `05_DEV_OUTPUT`로 범위가 어긋나 `handoff/`를 못 본다. → 현재 공유는 **MCP가 아니라 네이티브 접근** 덕분.
3. **mcp-memory의 이점(자동 동기화 DB)** 은 현 규모(1인, 단일 파일 dialogue.md)에서 **과잉.**
   헌법 0조 "비용 0 수렴" + 단순성 원칙에 어긋남.

### 권장 조치 (택1)
- **(권장) 현행 유지** — dialogue.md 네이티브 파일 공유로 충분. 추가 설치 0.
- (선택) 견고성 강화 — Cursor `mcp-filesystem-dokkebi` 허용 경로에 프로젝트 루트
  `D:\SynologyDrive\dokkebi\projects\shared-brain-day1` 추가. (mcp-memory보다 가벼움)

### mcp-memory 재검토 트리거 (미래)
- 공유 대상이 다중 파일/구조화 검색이 필요해질 때
- Claude·Cursor 외 3개 이상 에이전트가 동시 쓰기 시작할 때 (동시성 락 필요)
