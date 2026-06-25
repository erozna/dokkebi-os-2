"""FastAPI gateway shell for Day 1."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import chroma_host, chroma_port, ensure_env_from_credentials

ensure_env_from_credentials()

app = FastAPI(title="DOKKEBI Shared Brain API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "pong"}


@app.get("/info")
def info() -> dict[str, str | int]:
    return {
        "chroma_host": chroma_host(),
        "chroma_port": chroma_port(),
    }
