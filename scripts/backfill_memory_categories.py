"""Mem0 85건 category 백필 — 규칙 1차, 미매칭 Groq 배치 fallback."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings

from app.chroma_paths import LOCAL_CHROMA_PATH, MEM0_COLLECTION_NAME, chroma_server_settings
from app.config import ensure_env_from_credentials
from app.litellm_router import call_llm
from app.mem0_router import Category, classify_category_rule

REPORT_DIR = ROOT / "data" / "backfill_reports"
_BATCH_SIZE = 10
_CATEGORIES = ("episodic", "semantic", "procedural")


@dataclass
class BackfillRow:
    """백필 대상 한 건."""

    id: str
    user_id: str
    text: str
    old_category: str
    new_category: str
    method: str  # rule | groq | skip


def _chroma_clients() -> list[tuple[str, chromadb.ClientAPI]]:
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


def _extract_text(metadata: dict[str, Any] | None) -> str:
    meta = metadata or {}
    return str(meta.get("data") or meta.get("text") or meta.get("memory") or "").strip()


def load_rows(client: chromadb.ClientAPI) -> list[tuple[str, dict[str, Any]]]:
    """Chroma 전수 로드."""
    collection = client.get_collection(MEM0_COLLECTION_NAME)
    payload = collection.get(include=["metadatas"])
    rows: list[tuple[str, dict[str, Any]]] = []
    for row_id, meta in zip(payload["ids"], payload.get("metadatas") or []):
        rows.append((row_id, meta or {}))
    return rows


def print_sample(rows: list[tuple[str, dict[str, Any]]], n: int = 5) -> None:
    """구조 확인용 샘플 dump."""
    print(f"[sample] 상위 {min(n, len(rows))}건 메타데이터 구조:")
    for row_id, meta in rows[:n]:
        text = _extract_text(meta)
        keys = sorted(meta.keys())
        print(f"  id={row_id[:16]}... user_id={meta.get('user_id')} keys={keys}")
        print(f"    text[:120]={text[:120]!r}")
        print(f"    category={meta.get('category', '미분류')}")


def _groq_classify_batch(items: list[tuple[str, str]]) -> dict[str, Category]:
    """미매칭 건 Groq 배치 분류. {id: category}."""
    if not items:
        return {}

    lines = []
    for row_id, text in items:
        snippet = text.replace("\n", " ")[:300]
        lines.append(f"ID:{row_id}\n{snippet}")

    prompt = (
        "다음 메모리 텍스트를 episodic/semantic/procedural 중 하나로 분류하세요.\n"
        "- episodic: 대화·사건·경험 기록\n"
        "- semantic: 사실·선호·설정\n"
        "- procedural: 규칙·절차·SOP·구조화 로그\n\n"
        + "\n---\n".join(lines)
        + "\n\nJSON만 출력: {\"id\": \"category\", ...}"
    )

    try:
        raw, _ = call_llm(prompt, router_intent="verification", max_tokens=400)
        match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if not match:
            return {}
        parsed = json.loads(match.group())
        out: dict[str, Category] = {}
        for row_id, _ in items:
            cat = str(parsed.get(row_id, "episodic")).lower()
            if cat in _CATEGORIES:
                out[row_id] = cat  # type: ignore[assignment]
            else:
                out[row_id] = "episodic"
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"[경고] Groq 배치 분류 실패: {exc}")
        return {row_id: "episodic" for row_id, _ in items}


def plan_backfill(rows: list[tuple[str, dict[str, Any]]], *, use_groq: bool) -> list[BackfillRow]:
    """백필 계획 수립."""
    planned: list[BackfillRow] = []
    needs_groq: list[tuple[str, str]] = []

    for row_id, meta in rows:
        text = _extract_text(meta)
        old = str(meta.get("category") or "미분류")
        if old in _CATEGORIES and old != "미분류":
            planned.append(
                BackfillRow(row_id, str(meta.get("user_id", "")), text, old, old, "skip")
            )
            continue

        ruled = classify_category_rule(text)
        if ruled is not None:
            planned.append(
                BackfillRow(
                    row_id,
                    str(meta.get("user_id", "")),
                    text,
                    old,
                    ruled,
                    "rule",
                )
            )
        else:
            needs_groq.append((row_id, text))

    groq_map: dict[str, Category] = {}
    if use_groq and needs_groq:
        for i in range(0, len(needs_groq), _BATCH_SIZE):
            batch = needs_groq[i : i + _BATCH_SIZE]
            groq_map.update(_groq_classify_batch(batch))

    for row_id, text in needs_groq:
        meta = next(m for rid, m in rows if rid == row_id)
        old = str(meta.get("category") or "미분류")
        new_cat = groq_map.get(row_id, "episodic")
        method = "groq" if row_id in groq_map else "rule"
        planned.append(
            BackfillRow(row_id, str(meta.get("user_id", "")), text, old, new_cat, method)
        )

    return planned


def apply_updates(
    client: chromadb.ClientAPI,
    rows: list[tuple[str, dict[str, Any]]],
    planned: list[BackfillRow],
) -> int:
    """Chroma metadata.category 갱신."""
    meta_by_id = {rid: dict(meta) for rid, meta in rows}
    to_apply = [p for p in planned if p.method != "skip" and p.old_category != p.new_category]
    if not to_apply:
        # category 필드 자체가 없는 경우도 갱신
        to_apply = [p for p in planned if p.method != "skip"]

    collection = client.get_collection(MEM0_COLLECTION_NAME)
    updated = 0
    for item in to_apply:
        meta = meta_by_id.get(item.id, {})
        if str(meta.get("category", "")) == item.new_category:
            continue
        meta["category"] = item.new_category
        collection.update(ids=[item.id], metadatas=[meta])
        updated += 1
    return updated


def export_report(planned: list[BackfillRow], *, dry_run: bool) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"backfill_{stamp}.json"
    unclassified = sum(
        1 for p in planned if p.new_category not in _CATEGORIES or p.old_category == "미분류"
    )
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "total": len(planned),
        "by_method": {
            m: sum(1 for p in planned if p.method == m) for m in ("rule", "groq", "skip")
        },
        "unclassified_remaining": unclassified,
        "rows": [asdict(p) for p in planned],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Mem0 category 백필")
    parser.add_argument("--sample", action="store_true", help="상위 5건 구조 dump 후 종료")
    parser.add_argument("--dry-run", action="store_true", help="리포트만 생성")
    parser.add_argument("--apply", action="store_true", help="Chroma metadata 갱신")
    parser.add_argument("--no-groq", action="store_true", help="Groq fallback 비활성 (episodic 기본)")
    args = parser.parse_args()

    ensure_env_from_credentials()
    clients = _chroma_clients()
    if not clients:
        print("[오류] Chroma 클라이언트 없음")
        return 1

    primary_name, primary = clients[0]
    rows = load_rows(primary)
    print(f"[{primary_name}] 총 {len(rows)}건")

    if args.sample:
        print_sample(rows)
        return 0

    planned = plan_backfill(rows, use_groq=not args.no_groq)
    report_path = export_report(planned, dry_run=not args.apply)
    print(f"리포트: {report_path}")

    by_method = {m: sum(1 for p in planned if p.method == m) for m in ("rule", "groq", "skip")}
    print(f"계획: rule={by_method['rule']} groq={by_method['groq']} skip={by_method['skip']}")

    # 미분류 잔여 (new_category 없거나 미분류)
    remaining = sum(1 for p in planned if p.method != "skip" and p.new_category not in _CATEGORIES)
    print(f"미분류 잔여 예상: {remaining}건")

    if args.dry_run or not args.apply:
        print("dry-run 완료 (--apply 로 실제 갱신)")
        return 0

    for label, client in clients:
        n = apply_updates(client, load_rows(client), planned)
        print(f"[{label}] 갱신 {n}건")

    final_rows = load_rows(primary)
    uncat = sum(
        1
        for _, meta in final_rows
        if str(meta.get("category", "미분류")) in ("", "미분류")
        or meta.get("category") not in _CATEGORIES
    )
    print(f"최종 미분류: {uncat}건")
    return 0 if uncat <= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
