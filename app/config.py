"""Shared config for Day 1 scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CREDENTIALS_CANDIDATES = (
    Path(r"D:\SynologyDrive\dokkebi_secrets\ALL_CREDENTIALS.json"),
    Path(r"D:\SynologyDrive\dokkebi\dokkebi_secrets\ALL_CREDENTIALS.json"),
)

SHARED_BRAIN_SOURCES = (
    Path(r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json"),
    Path(r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\05_DEV_OUTPUT\py\SHARED_BRAIN.json"),
)


def load_credentials() -> dict:
    for path in CREDENTIALS_CANDIDATES:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def ensure_env_from_credentials() -> None:
    creds = load_credentials()
    mapping = {
        "ANTHROPIC_API_KEY": creds.get("ANTHROPIC_API_KEY")
        or (creds.get("anthropic") or {}).get("api_key"),
        "GROQ_API_KEY": creds.get("GROQ_API_KEY")
        or (creds.get("groq") or {}).get("api_key"),
        "GOOGLE_API_KEY": creds.get("GEMINI_API_KEY")
        or creds.get("GOOGLE_API_KEY")
        or (creds.get("google") or {}).get("gemini_api_key"),
        "TELEGRAM_BOT_TOKEN": creds.get("TELEGRAM_BOT_TOKEN")
        or (creds.get("telegram") or {}).get("bot_token"),
        "TAVILY_API_KEY": creds.get("TAVILY_API_KEY")
        or (creds.get("tavily") or {}).get("api_key"),
    }
    for key, value in mapping.items():
        if value and not os.environ.get(key):
            os.environ[key] = str(value).strip()
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]


def chroma_host() -> str:
    return os.environ.get("CHROMA_HOST", "localhost")


def chroma_port() -> int:
    return int(os.environ.get("CHROMA_PORT", "8000"))


def use_chroma_server() -> bool:
    """Docker Chroma 서버(포트 8000) 사용 여부."""
    return os.environ.get("USE_CHROMA_SERVER", "").lower() in ("1", "true", "yes")


def mem0_config(*, use_server: bool | None = None) -> dict:
    if use_server is None:
        use_server = use_chroma_server()

    if use_server:
        vector_store = {
            "provider": "chroma",
            "config": {
                "host": chroma_host(),
                "port": chroma_port(),
                "collection_name": "dokkebi_mem0",
            },
        }
    else:
        path = ROOT / "chroma_data"
        path.mkdir(parents=True, exist_ok=True)
        vector_store = {
            "provider": "chroma",
            "config": {
                "collection_name": "dokkebi_mem0",
                "path": str(path),
            },
        }

    return {
        "llm": {
            "provider": "litellm",
            "config": {
                "model": "gemini/gemini-2.5-flash",
                "temperature": 0.1,
            },
        },
        "embedder": {
            "provider": "fastembed",
            "config": {
                "model": "BAAI/bge-small-en-v1.5",
            },
        },
        "vector_store": vector_store,
    }
