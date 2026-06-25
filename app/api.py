"""FastAPI /goal 엔드포인트 — Day 5."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import ensure_env_from_credentials, goal_api_token
from app.litellm_router import RouterIntent
from app.supervisor import run_supervisor

ensure_env_from_credentials()

app = FastAPI(title="DOKKEBI OS API", version="0.3.0")

# Tauri dev webview (127.0.0.1:28720) → API (127.0.0.1:8765) needs CORS.
# API bind stays 127.0.0.1 only; origins are local desktop dev only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:28720",
        "http://localhost:28720",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class GoalRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    router_intent: RouterIntent | str = "default"
    thread_id: str | None = None


class GoalResponse(BaseModel):
    response: str
    model: str
    memory_hits: int
    web_hits: int
    elapsed_seconds: float


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
def info() -> dict[str, str]:
    """Tauri / CopilotKit 클라이언트용 메타."""
    import os

    return {
        "name": "DOKKEBI OS API",
        "version": app.version,
        "copilotkit": "week3-scaffold",
        "subscription_bridge": "enabled",
        "economy_mode": os.environ.get("ECONOMY_MODE", ""),
    }


def require_goal_auth(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None),
) -> None:
    expected = goal_api_token()
    if not expected:
        return
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_api_key:
        token = x_api_key.strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


@app.post("/goal", response_model=GoalResponse)
def goal_post(
    body: GoalRequest,
    _: None = Depends(require_goal_auth),
) -> GoalResponse:
    """Telegram /goal과 동일 supervisor 경로."""
    thread_id = body.thread_id or "api-default"
    router_intent: RouterIntent | str | None = body.router_intent
    if router_intent == "default":
        router_intent = None

    result = run_supervisor(
        body.user_input,
        thread_id=thread_id,
        router_intent=router_intent,
    )
    return GoalResponse(
        response=result.get("response") or "",
        model=str(result.get("model_used") or ""),
        memory_hits=int(result.get("memory_hits") or 0),
        web_hits=int(result.get("web_hits") or 0),
        elapsed_seconds=float(result.get("elapsed_sec") or 0.0),
    )


class BridgePrepRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    thread_id: str | None = None


class BridgeIngestRequest(BaseModel):
    reply: str = Field(..., min_length=1)
    role: str | None = None
    thread_id: str | None = None


@app.post("/bridge/prep")
def bridge_prep_post(
    body: BridgePrepRequest,
    _: None = Depends(require_goal_auth),
) -> dict:
    from app.subscription_bridge import bridge_prep

    return bridge_prep(
        body.topic,
        thread_id=body.thread_id or "api-bridge",
    )


@app.post("/bridge/ingest")
def bridge_ingest_post(
    body: BridgeIngestRequest,
    _: None = Depends(require_goal_auth),
) -> dict:
    from app.subscription_bridge import bridge_ingest

    return bridge_ingest(
        body.reply,
        role=body.role,
        thread_id=body.thread_id or "api-bridge",
    )


@app.post("/bridge/next")
def bridge_next_post(_: None = Depends(require_goal_auth)) -> dict:
    from app.subscription_bridge import bridge_next

    return bridge_next()


@app.get("/bridge/status")
def bridge_status_get(_: None = Depends(require_goal_auth)) -> dict:
    from app.subscription_bridge import bridge_status

    return bridge_status()


@app.get("/bridge/latest")
def bridge_latest_get(_: None = Depends(require_goal_auth)) -> dict[str, str]:
    from app.subscription_bridge import read_latest

    return {"content": read_latest()}
