"""Tavily 웹 검색 PoC — Day 6."""

from __future__ import annotations

import os
from typing import Any

from app.config import ensure_env_from_credentials


class WebSearchError(Exception):
    """웹 검색 실패."""


def _ci_mock() -> dict[str, Any]:
    return {
        "answer": "CI mock: 검색 요약입니다.",
        "results": [
            {
                "title": "Mock Result",
                "url": "https://example.com/mock",
                "content": "CI 환경 mock 검색 본문",
            }
        ],
    }


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Tavily 응답 → 표준 구조."""
    rows = raw.get("results") or []
    results = [
        {
            "title": str(item.get("title") or ""),
            "url": str(item.get("url") or ""),
            "content": str(item.get("content") or "")[:500],
        }
        for item in rows
        if isinstance(item, dict)
    ]
    return {
        "answer": str(raw.get("answer") or ""),
        "results": results,
    }


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """웹 검색. CI=1이면 mock, 아니면 Tavily API."""
    if os.environ.get("CI") == "1":
        return _ci_mock()

    ensure_env_from_credentials()
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise WebSearchError("TAVILY_API_KEY is not set")

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        raw = client.search(
            query,
            max_results=max_results,
            include_answer=True,
        )
        if not isinstance(raw, dict):
            raise WebSearchError("Unexpected Tavily response type")
        return _normalize(raw)
    except WebSearchError:
        raise
    except Exception as exc:  # noqa: BLE001 — WebSearchError로 래핑
        raise WebSearchError(str(exc)) from exc
