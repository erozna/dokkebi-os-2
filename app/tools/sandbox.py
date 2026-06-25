"""Docker sandbox runner — Week 3."""

from __future__ import annotations

import json
import subprocess


class SandboxError(RuntimeError):
    pass


def run_in_sandbox(code: str, *, container: str = "dokkebi-sandbox") -> dict:
    """Execute code in dokkebi-sandbox container via docker exec."""
    payload = json.dumps({"code": code}, ensure_ascii=False)
    try:
        proc = subprocess.run(
            ["docker", "exec", "-i", container, "python", "/home/sandbox/run_code.py"],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise SandboxError("docker CLI not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise SandboxError("sandbox timeout") from exc

    if not proc.stdout.strip():
        raise SandboxError(proc.stderr.strip() or "empty sandbox output")

    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise SandboxError(f"invalid sandbox json: {proc.stdout[:200]}") from exc

    if not data.get("ok"):
        raise SandboxError(str(data.get("error") or "sandbox failed"))
    return data
