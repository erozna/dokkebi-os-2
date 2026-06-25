"""ChromaDB 컨테이너 재기동 후 데이터 무손실 검증."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chromadb
from chromadb.config import Settings

from app.chroma_paths import MEM0_COLLECTION_NAME, chroma_server_settings


def _docker_cmd() -> list[str]:
    """docker 실행 파일 경로 탐색."""
    candidates = [
        "docker",
        r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
    ]
    for cmd in candidates:
        try:
            subprocess.run([cmd, "version"], check=True, capture_output=True, text=True)
            return [cmd]
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise FileNotFoundError("Docker CLI를 찾을 수 없습니다. Docker Desktop 설치 후 PATH를 확인하세요.")


def _compose(*args: str) -> None:
    """docker compose 명령 실행."""
    base = _docker_cmd()
    result = subprocess.run(
        [*base, "compose", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"docker compose {' '.join(args)} 실패\nstdout:{result.stdout}\nstderr:{result.stderr}"
        )


def _서버_건수() -> int:
    """서버 컬렉션 문서 수."""
    cfg = chroma_server_settings()
    client = chromadb.HttpClient(
        host=str(cfg["host"]),
        port=int(cfg["port"]),
        settings=Settings(anonymized_telemetry=False),
    )
    client.heartbeat()
    collection = client.get_collection(MEM0_COLLECTION_NAME)
    return collection.count()


def main() -> int:
    """down → up → 건수 비교."""
    print("재부팅 전 건수 측정...")
    before = _서버_건수()
    print(f"재부팅 전: {before}건")

    print("docker compose down chromadb ...")
    _compose("stop", "chromadb")
    _compose("rm", "-f", "chromadb")

    print("docker compose up -d chromadb ...")
    _compose("up", "-d", "chromadb")

    # 서버 기동 대기
    last_error: Exception | None = None
    for attempt in range(30):
        try:
            after = _서버_건수()
            print(f"재부팅 후: {after}건")
            if after == before:
                print("재부팅 테스트 성공 - 데이터 무손실")
                return 0
            print(f"[오류] 건수 불일치 (before={before}, after={after})")
            return 1
        except Exception as exc:  # noqa: BLE001 — 기동 대기
            last_error = exc
            time.sleep(2)

    raise RuntimeError(f"ChromaDB 재기동 후 연결 실패: {last_error}")


if __name__ == "__main__":
    raise SystemExit(main())
