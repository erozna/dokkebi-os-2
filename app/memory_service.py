"""Mem0 검색·포맷 공통 서비스."""

from __future__ import annotations

from typing import Any

from mem0 import Memory

from app.config import ensure_env_from_credentials, mem0_config

VALID_CATEGORIES = frozenset({"episodic", "semantic", "procedural", "preference"})


def get_memory(*, use_server: bool | None = None) -> Memory:
    """Mem0 인스턴스 생성."""
    ensure_env_from_credentials()
    return Memory.from_config(mem0_config(use_server=use_server))


def search_memories(
    query: str,
    *,
    user_id: str | None = None,
    category: str | None = None,
    limit: int = 5,
    use_server: bool | None = None,
) -> list[dict[str, Any]]:
    """Mem0 시맨틱 검색. category 지정 시 메타데이터로 후필터."""
    memory = get_memory(use_server=use_server)
    fetch_limit = limit * 4 if category else limit
    kwargs: dict[str, Any] = {"limit": fetch_limit}

    if user_id:
        kwargs["filters"] = {"user_id": user_id}
        raw = memory.search(query, **kwargs)
        if isinstance(raw, dict):
            rows = list(raw.get("results") or [])
        else:
            rows = list(raw) if isinstance(raw, list) else []
        return _filter_by_category(rows, category, limit)

    merged: list[dict[str, Any]] = []
    for uid in ("shared-brain-migration", "supervisor-default"):
        kwargs["filters"] = {"user_id": uid}
        raw = memory.search(query, **kwargs)
        rows = raw.get("results") if isinstance(raw, dict) else raw
        if isinstance(rows, list):
            merged.extend(rows)
    merged.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
    return _filter_by_category(merged, category, limit)


def _filter_by_category(
    rows: list[dict[str, Any]],
    category: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """카테고리 후필터."""
    if not category:
        return rows[:limit]
    cat = str(category).lower()
    if cat not in VALID_CATEGORIES:
        return rows[:limit]
    filtered = [
        r
        for r in rows
        if str((r.get("metadata") or {}).get("category", "")).lower() == cat
    ]
    return filtered[:limit]


def format_memory_results(results: list[dict[str, Any]], *, category: str | None = None) -> str:
    """텔레그램용 한국어 포맷."""
    if not results:
        label = f" ({category})" if category else ""
        return f"검색 결과가 없습니다{label}."

    header = f"기억 검색 결과 (상위 {len(results)}건)"
    if category:
        header += f" [필터: {category}]"
    lines = [header, ""]
    for idx, item in enumerate(results, start=1):
        text = str(item.get("memory") or item.get("text") or "").strip()
        if not text:
            continue
        item_category = (item.get("metadata") or {}).get("category", "미분류")
        score = item.get("score")
        score_txt = f"{score:.2f}" if isinstance(score, (int, float)) else "-"
        if len(text) > 220:
            text = text[:220] + "…"
        lines.append(f"{idx}. [{item_category}] (유사도 {score_txt})")
        lines.append(f"   {text}")
        lines.append("")

    return "\n".join(lines).strip()
