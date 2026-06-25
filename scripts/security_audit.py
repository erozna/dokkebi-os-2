"""Git 보안 점검 + SHARED_BRAIN 기록."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED_BRAIN_TARGET = Path(
    r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json"
)

KEY_PATTERNS = ("sk-ant-", "AIza", "gsk_")


def _run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def check_env_history() -> list[str]:
    """.env 파일 커밋 이력 검사."""
    issues: list[str] = []
    code, out = _run(["git", "log", "--all", "--full-history", "--name-only", "--pretty=format:%H"])
    if code != 0:
        issues.append(f"git log 실패: {out}")
        return issues

    for line in out.splitlines():
        name = line.strip()
        if name.endswith(".env") and not name.endswith(".env.example"):
            issues.append(f".env 노출 커밋 파일: {name}")
    return issues


def check_api_keys_in_history() -> list[str]:
    """API 키 패턴 grep."""
    issues: list[str] = []
    rev_code, rev_out = _run(["git", "rev-list", "--all"])
    if rev_code != 0:
        return [f"rev-list 실패: {rev_out}"]

    for pattern in KEY_PATTERNS:
        code, out = _run(["git", "grep", "-E", pattern, *rev_out.split()])
        if code == 0 and out.strip():
            issues.append(f"패턴 '{pattern}' 발견:\n{out[:500]}")
    return issues


def record_shared_brain(*, passed: bool, issues: list[str]) -> None:
    if not SHARED_BRAIN_TARGET.is_file():
        return
    data = json.loads(SHARED_BRAIN_TARGET.read_text(encoding="utf-8"))
    entry = {
        "entry_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_security"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Day3_security_audit",
        "actor": "security_audit.py",
        "task_id": "DAY3_CLEANUP_B",
        "payload": {
            "result": "보안 점검 통과" if passed else "보안 점검 실패",
            "issues": issues,
        },
    }
    data.setdefault("entries", []).append(entry)
    data["총_항목수"] = len(data["entries"])
    SHARED_BRAIN_TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    issues = check_env_history() + check_api_keys_in_history()
    if issues:
        print("[보안 실패] 즉시 중단 — API 키 재발급 검토 필요")
        for item in issues:
            print(f"  - {item}")
        record_shared_brain(passed=False, issues=issues)
        return 2

    print("보안 점검 통과")
    record_shared_brain(passed=True, issues=[])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
