"""mem0_router CLI 스모크 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import mem0_config
from app.mem0_router import save_to_mem0


def main() -> int:
    """샘플 2건으로 infer·카테고리 분기 확인."""
    from mem0 import Memory

    samples = [
        ('{"action":"test","task_id":"T001"}', "router-test-structured"),
        ("대장님이 오늘 커피를 좋아한다고 말씀하셨다.", "router-test-episodic"),
    ]

    memory = Memory.from_config(mem0_config())
    for text, uid in samples:
        out = save_to_mem0(text, user_id=uid, memory=memory)
        print(f"infer={out['infer']} category={out['metadata']['category']} text={text[:40]}")

    print("mem0_router 스모크 OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
