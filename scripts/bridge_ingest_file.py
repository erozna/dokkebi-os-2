"""ingest Bridge reply from file (long answers)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.subscription_bridge import bridge_ingest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge ingest from file")
    parser.add_argument("file", type=Path, help="reply markdown/text file")
    parser.add_argument("--role", default=None)
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    result = bridge_ingest(text, role=args.role)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
