"""LiteLLM hello-world: Anthropic / Groq / Google."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from litellm import completion

from app.config import ensure_env_from_credentials

MODELS = (
    "anthropic/claude-haiku-4-5-20251001",
    "groq/llama-3.1-8b-instant",
    "gemini/gemini-2.5-flash",
)


def call_model(model: str) -> str:
    response = completion(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly: hello from litellm"}],
        max_tokens=30,
    )
    return response.choices[0].message.content or ""


def main() -> int:
    ensure_env_from_credentials()
    missing = [
        key
        for key in ("ANTHROPIC_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY")
        if not os.environ.get(key)
    ]
    if missing and "GEMINI_API_KEY" in missing and os.environ.get("GOOGLE_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        missing = [k for k in missing if k != "GEMINI_API_KEY"]

    ok = 0
    for model in MODELS:
        try:
            text = call_model(model)
            print(f"[OK] {model}: {text.strip()[:120]}")
            ok += 1
        except Exception as exc:
            print(f"[FAIL] {model}: {exc}")

    print(f"\nResult: {ok}/{len(MODELS)} models responded")
    return 0 if ok == len(MODELS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
