"""[A] Auto 화이트리스트 도구 4종 — 헌법 8조 (2026-06-27 발효).

yt-dlp / Tavily / ChromaDB(read-only) / pytest 만 실제 실행한다.
화이트리스트 외 명령은 executor에서 [C] 사장님 결정으로 우회.

안전 원칙:
- yt-dlp: 메타데이터 수집 전용 (--skip-download --dump-json). 영상 다운로드 옵션 절대 금지.
- ChromaDB: 읽기 전용 검색만.
- 모든 외부 호출 timeout 5분. 실패는 예외 대신 결과 dict로 반환.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime

from app.config import ROOT

logger = logging.getLogger(__name__)

WHITELIST: tuple[str, ...] = ("yt-dlp", "tavily", "chromadb", "pytest")
_TIMEOUT = 300  # 5분

_DATA = ROOT / "data"
_YT_DIR = _DATA / "youtube"
_TAVILY_DIR = _DATA / "tavily"


@dataclass
class WhitelistResult:
    tool: str
    ok: bool
    summary: str = ""
    artifact_path: str = ""
    error: str = ""
    data: dict = field(default_factory=dict)


def is_whitelisted(tool: str) -> bool:
    return tool in WHITELIST


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _write_json(directory, payload: dict) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_ts()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def run_ytdlp(target: str, *, limit: int = 50, timeout: int = _TIMEOUT) -> WhitelistResult:
    """유튜브 채널/검색 메타데이터 수집. 다운로드 절대 안 함."""
    if not target or not str(target).strip():
        return WhitelistResult("yt-dlp", False, error="대상 URL/검색어 없음")
    # 안전 옵션만: 메타데이터 덤프 전용. 다운로드 플래그 미포함.
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--skip-download", "--dump-json", "--no-warnings",
        "--flat-playlist", "--playlist-end", str(int(limit)),
        str(target).strip(),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        return WhitelistResult("yt-dlp", False, error=f"timeout {timeout}s")
    except Exception as exc:  # noqa: BLE001
        return WhitelistResult("yt-dlp", False, error=str(exc))

    rows: list[dict] = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows and proc.returncode != 0:
        return WhitelistResult("yt-dlp", False, error=(proc.stderr or "")[:200])

    items = [
        {"title": r.get("title"), "id": r.get("id"), "url": r.get("url") or r.get("webpage_url"),
         "view_count": r.get("view_count"), "uploader": r.get("uploader")}
        for r in rows
    ]
    payload = {"target": target, "count": len(items), "items": items}
    path = _write_json(_YT_DIR, payload)
    return WhitelistResult(
        "yt-dlp", True, summary=f"메타데이터 {len(items)}건 수집", artifact_path=path,
        data=payload,
    )


def run_tavily(query: str, *, max_results: int = 5) -> WhitelistResult:
    """Tavily 웹 검색."""
    if not query or not str(query).strip():
        return WhitelistResult("tavily", False, error="검색어 없음")
    try:
        from app.tools.web_search import search_web

        res = search_web(str(query).strip(), max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        return WhitelistResult("tavily", False, error=str(exc))
    payload = {"query": query, **res}
    path = _write_json(_TAVILY_DIR, payload)
    n = len(res.get("results", []))
    return WhitelistResult(
        "tavily", True, summary=f"검색 결과 {n}건", artifact_path=path, data=payload,
    )


def run_chroma_query(query: str, *, limit: int = 5) -> WhitelistResult:
    """ChromaDB(mem0) 읽기 전용 검색 — 사장님 과거 관심사 매칭."""
    if not query or not str(query).strip():
        return WhitelistResult("chromadb", False, error="검색어 없음")
    try:
        from app.memory_service import search_memories

        rows = search_memories(str(query).strip(), limit=limit)
    except Exception as exc:  # noqa: BLE001
        return WhitelistResult("chromadb", False, error=str(exc)[:200])
    items = [
        {"memory": r.get("memory") or r.get("text") or "", "score": r.get("score")}
        for r in (rows or [])
    ]
    return WhitelistResult(
        "chromadb", True, summary=f"관련 기억 {len(items)}건", data={"results": items},
    )


def run_pytest(target: str | None = None, *, timeout: int = _TIMEOUT) -> WhitelistResult:
    """pytest 실행 (기본 -m 'not live'). pass/fail + 실패 메시지."""
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if target:
        cmd.append(str(target))
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return WhitelistResult("pytest", False, error=f"timeout {timeout}s")
    except Exception as exc:  # noqa: BLE001
        return WhitelistResult("pytest", False, error=str(exc))
    tail = "\n".join((proc.stdout or "").splitlines()[-8:])
    ok = proc.returncode == 0
    return WhitelistResult(
        "pytest", ok,
        summary=("통과" if ok else "실패") + f" — {tail.splitlines()[-1] if tail else ''}",
        data={"returncode": proc.returncode, "tail": tail},
        error="" if ok else tail[:300],
    )


def run_whitelisted(tool: str, arg: str = "", **kwargs) -> WhitelistResult:
    """화이트리스트 도구 디스패처."""
    if tool == "yt-dlp":
        return run_ytdlp(arg, **kwargs)
    if tool == "tavily":
        return run_tavily(arg, **kwargs)
    if tool == "chromadb":
        return run_chroma_query(arg, **kwargs)
    if tool == "pytest":
        return run_pytest(arg or None, **kwargs)
    return WhitelistResult(tool, False, error=f"화이트리스트 외 명령: {tool} — [C] 사장님 결정 필요")
