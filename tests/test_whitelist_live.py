"""화이트리스트 실제 실행 smoke (live) — 헌법 8조 [A] Auto.

기본 pytest에서 제외(`-m 'not live'`).
수동: pytest -m live tests/test_whitelist_live.py -s
yt-dlp 메타데이터 수집만 — 영상 다운로드 없음, API 키 불필요(무료).
"""

from __future__ import annotations

import importlib.util

import pytest

from app.tools.whitelist import run_ytdlp

pytestmark = pytest.mark.live

_STABLE_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" (최초 유튜브 영상)


@pytest.mark.skipif(
    importlib.util.find_spec("yt_dlp") is None,
    reason="yt-dlp 미설치",
)
def test_ytdlp_metadata_only():
    res = run_ytdlp(_STABLE_VIDEO, limit=1)
    assert res.ok, f"yt-dlp 실패: {res.error}"
    assert res.data.get("count", 0) >= 1
    assert res.artifact_path  # data/youtube/{ts}.json 작성
