# HANDOFF — 세션 간 인계 표준

> 컨텍스트가 끊겨도 다음 세션이 즉시 부팅되도록 하는 인계 폴더.
> Windows는 대소문자를 구분하지 않으므로 `HANDOFF/` == `handoff/` (동일 폴더).

## 핵심 규칙
- **`handoff/latest.md` 는 항상 최신 상태.** 세션 부팅의 단일 진입 문서.
- **매 Sprint 종료 시 자동 갱신** (헌법 8조: Section 6·History만 자동, 나머지는 명시 승인).
- 부팅 명령: `@CONSTITUTION.md @handoff/latest.md 읽고 진행`

## `latest.md` 표준 형식
1. **마지막 결정 사항** — 직전 세션에서 확정된 것
2. **다음 1턴 액션** — 즉시 착수할 작업
3. **미해결 질문** — 사장님 답변 대기 항목
4. **사장님 즉시 실행 [D]** — Human-in-the-Loop 위임 작업
5. **다음 세션 부팅 명령** — 복붙용 1줄

## 폴더 구조
- `handoff/latest.md` — 세션 인계 문서 (committed)
- `handoff/README.md` — 본 표준 문서 (committed)
- `handoff/bridge/` — Subscription Bridge 런타임 산출물 (gitignored, 자동 생성)
- `handoff/active/`, `inbox/`, `outbox/` — Bridge 세션 작업 디렉터리 (gitignored)
