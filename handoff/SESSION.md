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
1. **(완료) Cursor: MCP 전수 점검** → `docs/MCP_INVENTORY.md`. 판정: **mcp-memory 불필요.**
2. **선행 [D] 사장님: ChromaDB 재시작** — `http://192.168.1.3:8000` DOWN 확정. NAS DSM에서 컨테이너 재시작. (안 하면 메모리/토론 테스트 차단)
3. **선행 [D] 사장님: Claude Cowork 활성화 + 권한 범위** (약 20분)
   - 가용 폴더: `D:/SynologyDrive/dokkebi/projects/shared-brain-day1/` 만
   - **불가**: `D:/SynologyDrive/dokkebi_secrets/` (자격증명)
   - 전원: 잠자기 해제(`디스플레이만 끄기`)
4. **권장 본업: Intent Extractor 스켈레톤 착수** (헌법 3조 STEP 1, Week 3.5) — ChromaDB 복구 후
5. (선택) gemini API키 회수 + filesystem MCP 경로 확장

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
