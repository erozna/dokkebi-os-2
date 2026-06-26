"""Z.ai(GLM) 실 호출 smoke test 1회. 키 값 미출력."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import ensure_env_from_credentials  # noqa: E402
from app.litellm_router import call_llm  # noqa: E402

ensure_env_from_credentials()

MODEL = sys.argv[1] if len(sys.argv) > 1 else "zai/glm-4.6"

try:
    text, model_used, usage = call_llm(
        "안녕하세요. 한 문장으로 자기소개 해주세요.",
        model=MODEL,
        max_tokens=200,
        return_usage=True,
    )
    print(f"MODEL_USED={model_used}")
    print(f"FALLBACK={'YES' if model_used != MODEL else 'NO'}")
    print(f"USAGE={usage}")
    print(f"OUTPUT={text[:300]}")
except Exception as exc:  # noqa: BLE001
    print(f"ERROR={type(exc).__name__}: {exc}")
    sys.exit(1)
