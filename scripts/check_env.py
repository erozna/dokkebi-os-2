"""환경변수 4종 존재 여부만 보고 (키 값 절대 미출력 — 보안)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import ensure_env_from_credentials  # noqa: E402

ensure_env_from_credentials()
if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]


def mark(key: str) -> str:
    return "O" if os.environ.get(key) else "X"


print(
    f"ZAI={mark('ZAI_API_KEY')}, "
    f"GROQ={mark('GROQ_API_KEY')}, "
    f"GEMINI={mark('GEMINI_API_KEY')}, "
    f"ANTHROPIC={mark('ANTHROPIC_API_KEY')}"
)
