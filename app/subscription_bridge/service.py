"""Subscription Bridge 서비스."""

from __future__ import annotations

from typing import Any

from app.config import ROOT, ensure_env_from_credentials
from app.mem0_router import save_to_mem0
from app.memory_service import search_memories
from app.subscription_bridge.latest import rebuild_latest
from app.subscription_bridge.paths import INBOX_DIR, LATEST_PATH, OUTBOX_DIR, ensure_handoff_dirs
from app.subscription_bridge.prompts import build_outbox_prompt
from app.subscription_bridge.roles import ROLES, ROUND_ORDER
from app.subscription_bridge.session import (
    get_current_role,
    load_manifest,
    new_manifest,
    round_key,
    save_manifest,
)


def _mem0_context(topic: str, limit: int = 3) -> str:
    try:
        hits = search_memories(topic, limit=limit, user_id="bridge-default")
        if not hits:
            return ""
        return "\n".join(
            f"- {(h.get('memory') or h.get('data') or '')[:200]}" for h in hits
        )
    except Exception:  # noqa: BLE001
        return ""


def bridge_prep(topic: str, *, thread_id: str = "bridge-default") -> dict[str, Any]:
    """새 Bridge 세션 + 1라운드 outbox 프롬프트."""
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("topic is required")

    ensure_handoff_dirs()
    manifest = new_manifest(topic)
    mem_ctx = _mem0_context(topic)
    if mem_ctx:
        manifest["mem0_context"] = mem_ctx
        topic_block = f"{topic}\n\n[Mem0 참고]\n{mem_ctx}"
    else:
        topic_block = topic
    manifest["topic_enriched"] = topic_block

    role_id = ROUND_ORDER[0]
    role = ROLES[role_id]
    prompt = build_outbox_prompt(topic_block, role, manifest=manifest)
    rkey = round_key(0, role_id)
    outbox_name = f"{rkey}_{role.channel}.md"
    outbox_path = OUTBOX_DIR / outbox_name
    outbox_path.write_text(prompt, encoding="utf-8")

    manifest["rounds"][rkey] = {
        "role": role_id,
        "channel": role.channel,
        "channel_hint": role.channel_hint,
        "status": "prepared",
        "outbox_file": f"handoff/outbox/{outbox_name}",
    }
    manifest["current_outbox"] = manifest["rounds"][rkey]["outbox_file"]
    save_manifest(manifest)
    latest = rebuild_latest(manifest)

    return {
        "topic": topic,
        "role": role_id,
        "channel_hint": role.channel_hint,
        "outbox_file": str(outbox_path.relative_to(ROOT)),
        "outbox_path": str(outbox_path),
        "prompt_preview": prompt[:500],
        "latest_path": str(LATEST_PATH),
        "thread_id": thread_id,
        "latest_excerpt": latest[:400],
    }


def bridge_ingest(
    reply: str,
    *,
    role: str | None = None,
    thread_id: str = "bridge-default",
) -> dict[str, Any]:
    """웹 UI 답변 저장 + Mem0 + manifest 진행."""
    reply = (reply or "").strip()
    if not reply:
        raise ValueError("reply is required")

    manifest = load_manifest()
    if not manifest:
        raise ValueError("active bridge session 없음 — /bridge prep 먼저")

    role_id = role or get_current_role(manifest)
    if not role_id:
        raise ValueError("모든 라운드 완료됨")

    idx = int(manifest.get("current_index") or 0)
    rkey = round_key(idx, role_id)
    bridge_role = ROLES.get(role_id)
    if not bridge_role:
        raise ValueError(f"unknown role: {role_id}")

    inbox_name = f"{rkey}_reply.md"
    inbox_path = INBOX_DIR / inbox_name
    inbox_path.write_text(reply, encoding="utf-8")

    manifest.setdefault("rounds", {})
    manifest["rounds"][rkey] = {
        **(manifest["rounds"].get(rkey) or {}),
        "role": role_id,
        "channel": bridge_role.channel,
        "channel_hint": bridge_role.channel_hint,
        "status": "ingested",
        "inbox_file": f"handoff/inbox/{inbox_name}",
        "reply_excerpt": reply[:2000],
    }
    manifest["current_index"] = idx + 1
    from app.subscription_bridge.session import _now

    manifest["updated_at"] = _now()
    save_manifest(manifest)
    rebuild_latest(manifest)

    ensure_env_from_credentials()
    save_to_mem0(
        f"[Bridge {role_id}] Q: {manifest.get('topic', '')}\nA: {reply[:1500]}",
        user_id=thread_id,
        extra_metadata={
            "source": "subscription_bridge",
            "role": role_id,
            "bridge_key": rkey,
        },
    )

    result = {
        "ingested_role": role_id,
        "inbox_file": f"handoff/inbox/{inbox_name}",
        "next_role": get_current_role(manifest),
        "current_index": manifest["current_index"],
        "total_rounds": len(ROUND_ORDER),
    }
    try:
        nxt = bridge_next()
        result["next"] = nxt
    except ValueError:
        pass
    return result


def bridge_next() -> dict[str, Any]:
    """다음 라운드 outbox 프롬프트 생성."""
    manifest = load_manifest()
    if not manifest:
        raise ValueError("active bridge session 없음")

    role_id = get_current_role(manifest)
    if not role_id:
        latest = rebuild_latest(manifest)
        return {
            "done": True,
            "message": "모든 라운드 완료. handoff/bridge/latest.md 를 Cursor에서 @참조하세요.",
            "latest_path": str(LATEST_PATH),
            "latest_excerpt": latest[:500],
        }

    if role_id == "cursor":
        latest = rebuild_latest(manifest)
        return {
            "done": True,
            "role": "cursor",
            "channel_hint": ROLES["cursor"].channel_hint,
            "latest_path": str(LATEST_PATH),
            "message": "Cursor에서 handoff/bridge/latest.md 와 handoff/bridge/implement.md 를 열고 구현하세요.",
            "latest_excerpt": latest[:500],
        }

    idx = int(manifest.get("current_index") or 0)
    role = ROLES[role_id]
    topic_block = manifest.get("topic_enriched") or manifest.get("topic") or ""
    prompt = build_outbox_prompt(topic_block, role, manifest=manifest)
    rkey = round_key(idx, role_id)
    outbox_name = f"{rkey}_{role.channel}.md"
    outbox_path = OUTBOX_DIR / outbox_name
    outbox_path.write_text(prompt, encoding="utf-8")

    manifest.setdefault("rounds", {})
    manifest["rounds"][rkey] = {
        "role": role_id,
        "channel": role.channel,
        "channel_hint": role.channel_hint,
        "status": "prepared",
        "outbox_file": f"handoff/outbox/{outbox_name}",
    }
    manifest["current_outbox"] = manifest["rounds"][rkey]["outbox_file"]
    from app.subscription_bridge.session import _now

    manifest["updated_at"] = _now()
    save_manifest(manifest)

    return {
        "done": False,
        "role": role_id,
        "channel_hint": role.channel_hint,
        "outbox_file": f"handoff/outbox/{outbox_name}",
        "outbox_path": str(outbox_path),
        "prompt_preview": prompt[:600],
        "round": f"{idx + 1}/{len(ROUND_ORDER)}",
    }


def bridge_status() -> dict[str, Any]:
    manifest = load_manifest()
    if not manifest:
        return {"active": False, "message": "세션 없음 — /bridge prep <주제>"}
    return {
        "active": True,
        "topic": manifest.get("topic"),
        "current_index": manifest.get("current_index"),
        "total_rounds": len(ROUND_ORDER),
        "next_role": get_current_role(manifest),
        "current_outbox": manifest.get("current_outbox"),
        "rounds": manifest.get("rounds"),
    }


def read_latest() -> str:
    if LATEST_PATH.is_file():
        return LATEST_PATH.read_text(encoding="utf-8")
    return ""
