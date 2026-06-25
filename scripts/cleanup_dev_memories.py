"""Day 1 스모크/테스트 Mem0 메모리 청산."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings

from app.chroma_paths import LOCAL_CHROMA_PATH, MEM0_COLLECTION_NAME, chroma_server_settings

SHARED_BRAIN_TARGET = Path(
    r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json"
)

# Day 1 마이그레이션 시작 시각 (UTC) — 첫 1시간 윈도우
DAY1_START_UTC = datetime(2026, 6, 25, 2, 45, 0, tzinfo=timezone.utc)
DAY1_WINDOW = timedelta(hours=1)

_TEST_USER_IDS = frozenset(
    {"dokkebi-day1", "router-test-structured", "router-test-episodic"}
)
_DUMMY_PATTERNS = re.compile(
    r"\b(test|hello|ping|smoke|litellm|router-test)\b",
    re.IGNORECASE,
)
_DEV_TAGS = frozenset({"test", "dev", "smoke"})


@dataclass
class MemoryRow:
    """Chroma 한 건 요약."""

    id: str
    user_id: str
    created_at: str
    data: str
    metadata: dict[str, Any]
    reasons: list[str]


def _parse_created_at(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _has_dev_tag(metadata: dict[str, Any]) -> bool:
    """메타데이터 test/dev/smoke 태그 검사."""
    for key in ("tag", "tags", "env", "source", "category"):
        raw = metadata.get(key)
        if raw is None:
            continue
        if isinstance(raw, str) and raw.lower() in _DEV_TAGS:
            return True
        if isinstance(raw, (list, tuple)) and any(str(x).lower() in _DEV_TAGS for x in raw):
            return True
    if str(metadata.get("structured", "")).lower() in {"true", "false"}:
        uid = str(metadata.get("user_id", ""))
        if uid.startswith("router-test"):
            return True
    return False


def _is_day1_first_hour(created_at: str) -> bool:
    dt = _parse_created_at(created_at)
    if dt is None:
        return False
    return DAY1_START_UTC <= dt < DAY1_START_UTC + DAY1_WINDOW


def _is_dummy_content(data: str) -> bool:
    return bool(_DUMMY_PATTERNS.search(data or ""))


def _is_infer_duplicate(metadata: dict[str, Any], data: str) -> bool:
    """infer=True로 쪼개진 중복(원문 action= 형식이 아닌 migration 파생)."""
    if metadata.get("user_id") != "shared-brain-migration":
        return False
    if metadata.get("source") != "SHARED_BRAIN.json":
        return False
    # infer=False 마이그레이션 원문은 action= 접두를 유지
    return "action=" not in (data or "")


def classify_memory(row_id: str, metadata: dict[str, Any] | None) -> MemoryRow | None:
    """삭제 후보 분류. None이면 유지."""
    meta = metadata or {}
    data = str(meta.get("data") or meta.get("text_lemmatized") or "")
    user_id = str(meta.get("user_id") or "")
    created_at = str(meta.get("created_at") or "")
    reasons: list[str] = []

    if user_id in _TEST_USER_IDS:
        reasons.append(f"test_user_id:{user_id}")

    if _has_dev_tag(meta):
        reasons.append("dev_tag_metadata")

    if _is_dummy_content(data):
        reasons.append("dummy_content")

    if user_id == "dokkebi-day1":
        reasons.append("day1_smoke_user")

    if _is_infer_duplicate(meta, data):
        reasons.append("infer_duplicate_migration")

    # Day1 첫 1시간 + 테스트 계정 (보조 규칙)
    if reasons and _is_day1_first_hour(created_at) and user_id in _TEST_USER_IDS:
        reasons.append("day1_first_hour_test")

    if not reasons:
        return None

    return MemoryRow(
        id=row_id,
        user_id=user_id,
        created_at=created_at,
        data=data[:200],
        metadata=meta,
        reasons=reasons,
    )


def _chroma_clients() -> list[tuple[str, chromadb.ClientAPI]]:
    """서버 + embedded 클라이언트."""
    clients: list[tuple[str, chromadb.ClientAPI]] = []
    cfg = chroma_server_settings()
    try:
        http = chromadb.HttpClient(
            host=str(cfg["host"]),
            port=int(cfg["port"]),
            settings=Settings(anonymized_telemetry=False),
        )
        http.heartbeat()
        clients.append(("server", http))
    except Exception as exc:  # noqa: BLE001
        print(f"[경고] Chroma 서버 미연결: {exc}")

    if LOCAL_CHROMA_PATH.is_dir():
        clients.append(
            (
                "embedded",
                chromadb.PersistentClient(
                    path=str(LOCAL_CHROMA_PATH),
                    settings=Settings(anonymized_telemetry=False),
                ),
            )
        )
    return clients


def collect_delete_targets(client: chromadb.ClientAPI) -> list[MemoryRow]:
    """삭제 대상 수집."""
    collection = client.get_collection(MEM0_COLLECTION_NAME)
    payload = collection.get(include=["metadatas"])
    targets: list[MemoryRow] = []
    for row_id, meta in zip(payload["ids"], payload.get("metadatas") or []):
        row = classify_memory(row_id, meta)
        if row:
            targets.append(row)
    return targets


def apply_delete(client: chromadb.ClientAPI, ids: list[str]) -> None:
    """Chroma에서 ID 삭제."""
    if not ids:
        return
    collection = client.get_collection(MEM0_COLLECTION_NAME)
    collection.delete(ids=ids)


def record_shared_brain(targets: list[MemoryRow], *, dry_run: bool) -> None:
    """SHARED_BRAIN에 dry-run/삭제 목록 기록."""
    if not SHARED_BRAIN_TARGET.is_file():
        print(f"[경고] SHARED_BRAIN 없음: {SHARED_BRAIN_TARGET}")
        return

    data = json.loads(SHARED_BRAIN_TARGET.read_text(encoding="utf-8"))
    entry = {
        "entry_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_cleanup"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Day3_cleanup_dev_memories_dry_run" if dry_run else "Day3_cleanup_dev_memories_applied",
        "actor": "cleanup_dev_memories.py",
        "task_id": "DAY3_CLEANUP_A",
        "payload": {
            "dry_run": dry_run,
            "delete_count": len(targets),
            "targets": [asdict(t) for t in targets],
        },
    }
    data.setdefault("entries", []).append(entry)
    data["총_항목수"] = len(data["entries"])
    SHARED_BRAIN_TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fallback_remigrate() -> int:
    """차선책: 컬렉션 drop 후 SHARED_BRAIN 재마이그레이션."""
    from app.config import ensure_env_from_credentials
    from app.mem0_router import save_to_mem0
    from mem0 import Memory
    from scripts.migrate_shared_brain import _entry_text, load_all_entries

    ensure_env_from_credentials()

    for label, client in _chroma_clients():
        try:
            client.delete_collection(MEM0_COLLECTION_NAME)
            print(f"[fallback] {label} 컬렉션 drop")
        except Exception:
            pass

    entries = load_all_entries()
    memory = Memory.from_config(__import__("app.config", fromlist=["mem0_config"]).mem0_config())
    user_id = "shared-brain-migration"
    for entry in entries:
        text = _entry_text(entry)
        if text.strip():
            save_to_mem0(text, user_id=user_id, memory=memory, extra_metadata={"source": "SHARED_BRAIN.json"})

    count = _chroma_clients()[0][1].get_collection(MEM0_COLLECTION_NAME).count()
    print(f"[fallback] 재마이그레이션 후 건수: {count}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Dev/test Mem0 메모리 청산")
    parser.add_argument("--dry-run", action="store_true", help="삭제 없이 대상만 출력")
    parser.add_argument("--apply", action="store_true", help="실제 삭제 수행")
    parser.add_argument("--fallback", action="store_true", help="drop 후 재마이그레이션")
    args = parser.parse_args()

    if args.fallback:
        count = fallback_remigrate()
        return 0 if count == 85 else 1

    clients = _chroma_clients()
    if not clients:
        print("[오류] Chroma 클라이언트 없음")
        return 1

    primary_name, primary = clients[0]
    targets = collect_delete_targets(primary)
    print(f"[{primary_name}] 삭제 대상: {len(targets)}건")

    for row in targets[:10]:
        print(f"  - {row.id[:12]}... | {row.user_id} | {row.reasons}")
    if len(targets) > 10:
        print(f"  ... 외 {len(targets) - 10}건")

    record_shared_brain(targets, dry_run=not args.apply)

    if args.dry_run or not args.apply:
        print("dry-run 완료 (--apply 로 실제 삭제)")
        return 0 if len(targets) == 88 else 1

    delete_ids = [t.id for t in targets]
    for label, client in clients:
        apply_delete(client, delete_ids)
        remaining = client.get_collection(MEM0_COLLECTION_NAME).count()
        print(f"[{label}] 삭제 후 건수: {remaining}")

    final = primary.get_collection(MEM0_COLLECTION_NAME).count()
    if final != 85:
        print(f"[오류] 최종 건수 {final}건 — 85건 불일치. --fallback 검토")
        return 1

    print("청산 완료: 85건 확인")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
