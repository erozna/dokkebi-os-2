# 도깨비 OS 2.0 — Tauri Desktop (Week 3)

Tauri 2 + React + TypeScript + CopilotKit provider + 한국어 i18n.

## 사전 요구

- Node.js 20+
- Rust / Cargo (Tauri 빌드)
- 백엔드: `uvicorn app.api:app --host 127.0.0.1 --port 8765` (repo 루트)

## 개발

Windows에서 Hyper-V가 **1383–1482** 포트를 잡아두는 PC가 있어, Vite는 **5173**을 씁니다.

```powershell
cd desktop
npm install
npm run tauri dev
```

## 환경 변수

`.env.example` → `.env` (선택)

| 변수 | 기본값 |
|------|--------|
| `VITE_DOKKEBI_API` | `http://127.0.0.1:8765` |

## 기능 (Week 3)

- 한국어 UI (`react-i18next`)
- FastAPI `/goal` 채팅 (4역할 토론 체크박스 → `router_intent=debate`)
- CopilotKit provider 스캐폴드 (full runtime → Week 4)
- 백엔드 헬스 표시 (`/healthz`)

## 샌드박스 (Docker)

```powershell
docker compose build sandbox
docker compose up -d sandbox
```

Python에서 `app.tools.sandbox.run_in_sandbox(code)` 호출.

## Week 4 예정

- CopilotKit runtime ↔ LangGraph
- Mem0 / 설정 화면
- Tauri 패키징 MVP
