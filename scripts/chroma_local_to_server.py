"""embedded Chroma(dokkebi_mem0) → ChromaDB 서버(포트 8000) 마이그레이션."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings

from app.chroma_paths import LOCAL_CHROMA_PATH, MEM0_COLLECTION_NAME, chroma_server_settings


def _로컬_클라이언트() -> chromadb.PersistentClient:
    """로컬 embedded Chroma 클라이언트."""
    if not LOCAL_CHROMA_PATH.is_dir():
        raise FileNotFoundError(f"로컬 Chroma 경로 없음: {LOCAL_CHROMA_PATH}")
    return chromadb.PersistentClient(
        path=str(LOCAL_CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )


def _서버_클라이언트(*, max_retry: int = 30, interval_sec: float = 2.0) -> chromadb.HttpClient:
    """ChromaDB HTTP 서버 연결 (기동 대기 포함)."""
    cfg = chroma_server_settings()
    last_error: Exception | None = None

    for _ in range(max_retry):
        try:
            client = chromadb.HttpClient(
                host=str(cfg["host"]),
                port=int(cfg["port"]),
                settings=Settings(anonymized_telemetry=False),
            )
            client.heartbeat()
            return client
        except Exception as exc:  # noqa: BLE001 — 연결 재시도
            last_error = exc
            time.sleep(interval_sec)

    raise ConnectionError(
        f"ChromaDB 서버({cfg['host']}:{cfg['port']}) 연결 실패. "
        f"docker compose up -d 후 재시도하세요. 원인: {last_error}"
    )


def _컬렉션_복사(소스, 서버_클라이언트) -> int:
    """ID·임베딩·문서·메타데이터 일괄 복사."""
    데이터 = 소스.get(include=["embeddings", "documents", "metadatas"])
    ids = 데이터.get("ids") or []
    if not ids:
        return 0

    try:
        서버_클라이언트.delete_collection(MEM0_COLLECTION_NAME)
    except Exception:
        pass

    새_컬렉션 = 서버_클라이언트.create_collection(name=MEM0_COLLECTION_NAME)
    embeddings = 데이터.get("embeddings")
    documents = 데이터.get("documents")
    metadatas = 데이터.get("metadatas")

    batch = 50
    for start in range(0, len(ids), batch):
        end = start + batch
        kwargs: dict = {
            "ids": ids[start:end],
        }
        if embeddings is not None:
            kwargs["embeddings"] = embeddings[start:end]
        if documents is not None:
            kwargs["documents"] = documents[start:end]
        if metadatas is not None:
            kwargs["metadatas"] = metadatas[start:end]
        새_컬렉션.add(**kwargs)
    return len(ids)


def main() -> int:
    """로컬 → 서버 마이그레이션 실행."""
    로컬 = _로컬_클라이언트()
    try:
        로컬_컬렉션 = 로컬.get_collection(MEM0_COLLECTION_NAME)
    except Exception as exc:
        print(f"[오류] 로컬 컬렉션 '{MEM0_COLLECTION_NAME}' 없음: {exc}")
        return 1

    로컬_건수 = 로컬_컬렉션.count()
    print(f"로컬 컬렉션 건수: {로컬_건수}")

    서버 = _서버_클라이언트()
    복사_건수 = _컬렉션_복사(로컬_컬렉션, 서버)

    서버_컬렉션 = 서버.get_collection(MEM0_COLLECTION_NAME)
    서버_건수 = 서버_컬렉션.count()

    print(f"복사 완료: {복사_건수}건")
    print(f"서버 검증 건수: {서버_건수}건")

    if 서버_건수 != 로컬_건수:
        print("[오류] 로컬·서버 건수 불일치")
        return 1

    print("마이그레이션 성공 (무손실)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
