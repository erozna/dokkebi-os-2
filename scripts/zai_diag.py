"""Z.ai 직접 진단 — 폴백 없이 raw 에러 확인. 키 값 미출력."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litellm import completion  # noqa: E402

from app.config import ensure_env_from_credentials  # noqa: E402

ensure_env_from_credentials()
BASE = "https://api.z.ai/api/paas/v4/"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "glm-4.6"
key = os.environ.get("ZAI_API_KEY")
print(f"KEY_PRESENT={'O' if key else 'X'} MODEL=openai/{MODEL} BASE={BASE}")

try:
    resp = completion(
        model=f"openai/{MODEL}",
        messages=[{"role": "user", "content": "안녕하세요. 한 문장 자기소개."}],
        api_base=BASE,
        api_key=key,
        max_tokens=200,
        temperature=0.6,
    )
    print("OK")
    print(f"USAGE={resp.usage}")
    print(f"OUT={resp.choices[0].message.content[:200]}")
except Exception as exc:  # noqa: BLE001
    print(f"RAW_ERROR={type(exc).__name__}: {str(exc)[:600]}")
