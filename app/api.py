"""FastAPI /goal 엔드포인트 — Day 5."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import ensure_env_from_credentials, goal_api_token
from app.litellm_router import RouterIntent
from app.supervisor import run_supervisor

ensure_env_from_credentials()

app = FastAPI(title="DOKKEBI OS API", version="0.3.0")


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
    return {
        "name": "DOKKEBI OS API",
        "version": app.version,
        "copilotkit": "week3-scaffold",
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
