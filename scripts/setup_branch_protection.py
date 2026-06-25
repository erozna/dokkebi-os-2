"""main 브랜치 protection 설정 (gh CLI 필요)."""

from __future__ import annotations

import json
import subprocess

REPO = "erozna/dokkebi-os-2"
BRANCH = "main"


def main() -> int:
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
        print("gh CLI not found — install and run: gh auth login")
        return 1

    if proc.returncode != 0:
        print(proc.stderr or proc.stdout)
        print("Branch protection failed. Ensure gh auth login with admin access.")
        return proc.returncode

    print(f"Branch protection enabled for {REPO}:{BRANCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
