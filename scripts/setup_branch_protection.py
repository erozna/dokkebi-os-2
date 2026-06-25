"""main 브랜치 protection 설정 (gh CLI + GitHub 토큰)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import load_credentials

REPO = "erozna/dokkebi-os-2"
BRANCH = "main"


def _ensure_gh_token() -> bool:
    if os.environ.get("GH_TOKEN", "").strip():
        return True
    creds = load_credentials()
    github = creds.get("github") or {}
    token = ""
    if isinstance(github, dict):
        token = str(github.get("token") or "").strip()
    if token:
        os.environ["GH_TOKEN"] = token
        return True
    return False


def main() -> int:
    if not _ensure_gh_token():
        print("GH_TOKEN missing — set env or add github.token in ALL_CREDENTIALS.json")
        return 1

    payload = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["test", "gitleaks-scan"],
        },
        "enforce_admins": False,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    cmd = [
        "gh",
        "api",
        f"repos/{REPO}/branches/{BRANCH}/protection",
        "-X",
        "PUT",
        "--input",
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        print("gh CLI not found — install GitHub CLI first")
        return 1

    if proc.returncode != 0:
        print(proc.stderr or proc.stdout)
        print("Branch protection failed. Token needs admin access on the repo.")
        return proc.returncode

    print(f"Branch protection enabled for {REPO}:{BRANCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
