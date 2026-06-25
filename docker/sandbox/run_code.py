"""Run untrusted code in RestrictedPython (stdin JSON: {\"code\": \"...\"})."""

from __future__ import annotations

import json
import sys

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        print(json.dumps({"ok": False, "error": "invalid json"}))
        return 1

    code = str(payload.get("code") or "")
    if not code.strip():
        print(json.dumps({"ok": False, "error": "code is empty"}))
        return 1

    byte_code = compile_restricted(code, "<sandbox>", "exec")
    if byte_code.errors:
        print(json.dumps({"ok": False, "error": "; ".join(byte_code.errors)}))
        return 1

    globs = {"__builtins__": safe_builtins}
    locs: dict = {}
    try:
        exec(byte_code.code, globs, locs)  # noqa: S102
        print(json.dumps({"ok": True, "locals": {k: repr(v) for k, v in locs.items()}}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
