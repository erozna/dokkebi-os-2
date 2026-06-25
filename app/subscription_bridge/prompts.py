"""역할별 붙여넣기 프롬프트 생성."""

from __future__ import annotations

from app.subscription_bridge.roles import BridgeRole


def _prior_context(manifest: dict, role_id: str) -> str:
    lines: list[str] = []
    for key, meta in (manifest.get("rounds") or {}).items():
        if not isinstance(meta, dict):
            continue
        if meta.get("status") != "ingested":
            continue
        reply = (meta.get("reply_excerpt") or "")[:1500]
        lines.append(f"### {meta.get('role', key)}\n{reply}")
    if not lines:
        return "(이전 라운드 없음)"
    return "\n\n".join(lines)


def build_outbox_prompt(
    topic: str,
    role: BridgeRole,
    *,
    manifest: dict | None = None,
) -> str:
    manifest = manifest or {}
    prior = _prior_context(manifest, role.id)
    return f"""[도깨비 OS — Subscription Bridge]
역할: {role.label}
붙여넣기 대상: {role.channel_hint}

[주제]
{topic}

[이전 라운드 요약]
{prior}

[지시]
{role.instruction}

[응답 후]
답변 전체를 도깨비에 `/bridge ingest` 또는 handoff/inbox/ 에 저장하세요.
"""
