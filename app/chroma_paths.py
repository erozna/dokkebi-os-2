"""ChromaDB 로컬·서버 경로 상수."""

from __future__ import annotations

from pathlib import Path

from app.config import ROOT, chroma_host, chroma_port

# Mem0 embedded Chroma 저장 위치
LOCAL_CHROMA_PATH = ROOT / "chroma_data"

# Mem0가 사용하는 기본 컬렉션명
MEM0_COLLECTION_NAME = "dokkebi_mem0"


def chroma_server_settings() -> dict[str, str | int]:
    """HttpClient 접속 정보."""
    return {
        "host": chroma_host(),
        "port": chroma_port(),
    }
