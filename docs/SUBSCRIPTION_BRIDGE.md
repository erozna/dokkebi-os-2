# Subscription Bridge (정액제 핸드오프)

Claude/Gemini **웹 정액제** + **Cursor Pro** + 도깨비 **기억·라운드 지휘**.

## 흐름

1. `/bridge prep <주제>` — 1라운드(장인) 프롬프트 → `handoff/outbox/`
2. **Claude 웹**에 붙여넣기 → 답변 복사
3. `/bridge ingest <답변>` — Mem0 + `handoff/inbox/` 저장
4. 자동으로 다음 라운드 안내 (심판자→Gemini, …)
5. 완료 후 **Cursor**에서 `@handoff/latest.md` 참조

## 라운드

| 순서 | 역할 | 붙여넣기 |
|------|------|----------|
| 1 | 장인 | Claude 웹 |
| 2 | 심판자 | Gemini 웹 |
| 3 | 검사관 | Gemini 웹 |
| 4 | 재판장 | Claude 웹 |
| 5 | cursor | Cursor IDE |

## 텔레그램

```
/bridge prep Week 4 우선순위
/bridge status
/bridge next
/bridge ingest (답변 전체)
```

## API

- `POST /bridge/prep` `{"topic":"..."}`
- `POST /bridge/ingest` `{"reply":"..."}`
- `POST /bridge/next`
- `GET /bridge/status`
- `GET /bridge/latest`

## Economy

`.env`에 `ECONOMY_MODE=1` → `/goal` 일반 대화는 Gemini Flash (API 절약).

Bridge 토론은 **API 거의 없음** (prep/ingest만 로컬).
