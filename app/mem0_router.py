"""Mem0 저장 라우터 — infer 분기 + 카테고리 자동 분류."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from app.config import ensure_env_from_credentials, mem0_config

Category = Literal["episodic", "semantic", "procedural"]

# 구조화 로그 패턴 (SHARED_BRAIN 마이그레이션 형식 등)
_STRUCTURED_MARKERS = (
    re.compile(r"^\s*[\[{]"),
    re.compile(r"action\s*=", re.I),
    re.compile(r"task_id\s*=", re.I),
    re.compile(r"payload\s*=", re.I),
    re.compile(r'"schema_version"\s*:'),
    re.compile(r'"entry_id"\s*:'),
)

_PROCEDURAL = (
    "규칙",
    "절차",
    "sop",
    "헌법",
    "학습",
    "procedure",
    "policy",
    "must",
    "workflow",
    "운영매뉴얼",
    "법전",
)
_SEMANTIC = (
    "선호",
    "사실",
    "preference",
    "likes",
    "설정",
    "이름은",
    "주소",
    "전화",
    "api_key",
    "기억",
    "fact",
)
_EPISODIC = (
    "user:",
    "assistant:",
    "대화",
    "물어봤",
    "답변",
    "said",
    "chat",
    "conversation",
    "대장님",
)


def is_structured_data(text: str) -> bool:
    """JSON·구조화 로그 여부 판별."""
    stripped = (text or "").strip()
    if not stripped:
        return False

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, (dict, list)):
            return True
    except json.JSONDecodeError:
        pass

    return any(pattern.search(stripped) for pattern in _STRUCTURED_MARKERS)


def classify_category(text: str) -> Category:
    """episodic / semantic / procedural 자동 분류."""
    ruled = classify_category_rule(text)
    if ruled is not None:
        return ruled
    return "episodic"


def classify_category_rule(text: str) -> Category | None:
    """규칙 매칭 시 카테고리, 미매칭 시 None (LLM fallback 대상)."""
    lowered = (text or "").lower()

    if any(key in lowered for key in _PROCEDURAL):
        return "procedural"
    if any(key in lowered for key in _SEMANTIC):
        return "semantic"
    if any(key in lowered for key in _EPISODIC):
        return "episodic"

    if is_structured_data(text):
        return "procedural"

    return None


def build_metadata(
    text: str,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """저장용 메타데이터 생성."""
    meta: dict[str, Any] = {
        "category": classify_category(text),
        "structured": is_structured_data(text),
    }
    if extra:
        meta.update(extra)
    return meta


def should_infer(text: str) -> bool:
    """자유 텍스트면 True, 구조화 데이터면 False."""
    return not is_structured_data(text)


def save_to_mem0(
    text: str,
    *,
    user_id: str,
    memory=None,
    use_server: bool | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mem0에 라우팅 규칙에 따라 저장."""
    ensure_env_from_credentials()

    if memory is None:
        from mem0 import Memory

        memory = Memory.from_config(mem0_config(use_server=use_server))

    infer = should_infer(text)
    metadata = build_metadata(text, extra=extra_metadata)

    result = memory.add(
        text,
        user_id=user_id,
        metadata=metadata,
        infer=infer,
    )
    return {
        "infer": infer,
        "metadata": metadata,
        "result": result,
    }
