"""handoff/bridge/latest.md — Cursor용 요약."""

from __future__ import annotations

from app.subscription_bridge.paths import IMPLEMENT_PATH, LATEST_PATH, ensure_handoff_dirs
from app.subscription_bridge.roles import ROLES


def rebuild_latest(manifest: dict) -> str:
    ensure_handoff_dirs()
    topic = manifest.get("topic") or ""
    lines = [
        "# 도깨비 Subscription Bridge — Cursor 핸드오프",
        "",
        f"주제: {topic}",
        f"갱신: {manifest.get('updated_at', '-')}",
        "",
        "## 라운드 기록",
        "",
    ]
    rounds = manifest.get("rounds") or {}
    for key in sorted(rounds.keys()):
        meta = rounds[key]
        if not isinstance(meta, dict):
            continue
        role = meta.get("role", key)
        status = meta.get("status", "?")
        channel = meta.get("channel_hint", "")
        inbox_file = meta.get("inbox_file", "")
        lines.append(f"### {key} — {role} ({status})")
        lines.append(f"- 채널: {channel}")
        if inbox_file:
            lines.append(f"- 파일: `{inbox_file}`")
        excerpt = (meta.get("reply_excerpt") or "")[:800]
        if excerpt:
            lines.append(f"\n{excerpt}\n")

    consensus = _consensus_from_manifest(manifest)
    lines.extend(["", "## 합의안 (재판장 또는 최종)", "", consensus or "(아직 없음)", ""])

    cursor_role = ROLES["cursor"]
    lines.extend(
        [
            "## Cursor 실행 지시",
            "",
            cursor_role.instruction,
            "",
            "구현 후 pytest 실행. 관련 경로만 수정.",
            "",
        ]
    )

    text = "\n".join(lines)
    LATEST_PATH.write_text(text, encoding="utf-8")
    IMPLEMENT_PATH.write_text(
        f"# Implement\n\n{consensus or topic}\n\nSee handoff/bridge/latest.md for full context.\n",
        encoding="utf-8",
    )
    return text


def _consensus_from_manifest(manifest: dict) -> str:
    rounds = manifest.get("rounds") or {}
    for key in sorted(rounds.keys(), reverse=True):
        meta = rounds[key]
        if isinstance(meta, dict) and meta.get("role") == "재판장" and meta.get("reply_excerpt"):
            return str(meta["reply_excerpt"])
    return ""
