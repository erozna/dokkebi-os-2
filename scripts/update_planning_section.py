"""SHARED_BRAIN.json dokkebi_os_2_planning 섹션 동기화."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = Path(r"D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json")
PROJECT_COPY = ROOT / "SHARED_BRAIN.json"


def build_planning() -> dict:
    """도깨비 OS 2.0 기획 섹션 본문."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "updated_at": now,
        "project_path": str(ROOT),
        "repo_url": "https://github.com/erozna/dokkebi-os-2",
        "branch": "main",
        "week1_milestone": "7/7 완료 (Day 3 기준)",
        "roadmap_5weeks": {
            "week1": {
                "title": "백엔드 + 메모리",
                "status": "Day 3 완료, Day 4 진행 중",
                "scope": [
                    "LiteLLM 게이트웨이",
                    "Mem0 + ChromaDB 서버 모드",
                    "LangGraph Supervisor",
                    "Telegram bot (/ping, /memory, /goal)",
                ],
            },
            "week2": {
                "title": "CrewAI 4역할 토론",
                "roles": ["장인", "심판자", "검사관", "재판장"],
            },
            "week3": {
                "title": "Docker 샌드박스 + Tauri UI 착수",
            },
            "week4": {
                "title": "Tauri UI 완성 + Composio MCP",
            },
            "week5": {
                "title": "Self-Harness 진화 루프 + 사장님 도메인 통합",
            },
        },
        "stack_8": [
            {"name": "Tauri 2.0", "role": "데스크톱 UI"},
            {"name": "CopilotKit + React + 한국어 i18n", "role": "UI 빌딩 블록"},
            {"name": "LangGraph 0.4", "role": "오케스트레이션, SQLite 체크포인터"},
            {"name": "CrewAI", "role": "멀티 에이전트 토론 (AutoGen 대체)"},
            {"name": "Mem0 + ChromaDB", "role": "영구 메모리, Chroma 서버 모드"},
            {"name": "LiteLLM", "role": "모델 게이트웨이 (Claude/Gemini/Groq)"},
            {"name": "Composio", "role": "MCP 도구 통합"},
            {"name": "FastAPI", "role": "백엔드"},
        ],
        "infrastructure_split": {
            "pc_docker_desktop": {
                "purpose": "개발/테스트",
                "services": [
                    "개발용 ChromaDB",
                    "Mem0 dev_test",
                    "실행 샌드박스",
                ],
            },
            "nas_ds920_docker": {
                "purpose": "운영",
                "services": [
                    "운영 ChromaDB",
                    "Mem0 daepyo_real",
                    "Telegram 봇",
                    "Self-Harness 야간 cron",
                ],
            },
            "cursor_pro": {
                "purpose": "코딩 도구",
                "note": "컨트롤 타워 아님",
            },
        },
        "crew_personas_week2": {
            "장인": {
                "model": "Claude Opus",
                "role": "실용 코더, 최종 책임",
            },
            "심판자": {
                "model": "Gemini Flash (무료)",
                "role": "사장님 노이즈 픽션 페르소나, 가차없는 비판",
            },
            "검사관": {
                "model": "Groq Llama 3.3 (무료)",
                "role": "테스트 케이스 작성",
            },
            "재판장": {
                "model": "Claude Sonnet",
                "role": "합의안 도출",
            },
        },
        "day1_completed": [
            "API 키 3개 (Anthropic/Google/Groq)",
            ".env 설정",
            "requirements.txt + venv",
            "docker-compose.yml",
            "LiteLLM 3모델 hello-world",
        ],
        "day2_completed": [
            "Chroma 서버 모드 (chromadb/chroma:1.5.9)",
            "embedded 85건 → 서버 마이그레이션",
            "Mem0 라우터 (infer=False/True 하이브리드)",
            "Telegram /ping, /memory",
            "reboot_test 무손실 검증",
        ],
        "day3_completed": [
            "중복 메모리 88건 청산 → 85건 유지",
            "보안 점검 통과 (.env/API키 커밋 노출 없음)",
            "master → main 브랜치 전환",
            "LangGraph supervisor 4노드",
            "LiteLLM router (claude→gemini→groq 폴백)",
            "Telegram /goal",
            "E2E 테스트 5/5",
        ],
        "day4_in_progress": [
            "봇 실전 검증 (사장님 진행, PID 14176)",
            "gh CLI 설치 + master 원격 삭제",
            "FastAPI /goal HTTP 엔드포인트",
            "Mem0 카테고리 필터 (/memory --episodic 등)",
            "GitHub Actions CI",
            "LangSmith 연동 (선택)",
        ],
        "day5_7_remaining": [
            "Self-Harness 평가 KPI 5개 정의",
            "SHOP_ENGINE 메모리 연동",
            "Week 2 CrewAI 준비",
        ],
        "boss_core_decisions": [
            "도깨비는 독립 데스크톱 앱(Tauri), Cursor/Claude는 백엔드로만 호출",
            "taOS 미사용, 자체 조립(라이브러리 8개)",
            "한국어 UI 우선, 영어 코드",
            "백엔드 + Telegram bot 먼저, Tauri UI는 Week 3",
            "가성비/시간/ROI 3축 판단",
        ],
        "security_infrastructure": {
            "nas_lan": "192.168.1.3",
            "nas_credentials": "SHARED_BRAIN 비공개 (별도 보관)",
            "tailscale": "100.66.77.127",
            "guardian_bot_token": "도깨비 1.0 잔재, 사용 안 함",
            "sync_note": ".env / ALL_CREDENTIALS.json 동기화 폴더 위치 보안 점검 필요",
            "credentials_path_pc": r"D:\SynologyDrive\dokkebi_secrets\ALL_CREDENTIALS.json",
        },
        "deferred_decisions": {
            "guardian_bot_cleanup": "Day 5",
            "bot_nas_migration": "Week 2 중반",
            "branch_protection": "Week 2 시작 전",
            "github_default_branch_main": "사장님 Settings에서 main으로 변경 후 master 삭제",
        },
    }


def apply_to_file(path: Path) -> None:
    """기존 SHARED_BRAIN에 planning 섹션 병합."""
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "schema_version": "1.3",
            "description": "도깨비 OS 2.0 프로젝트 인계용 SHARED_BRAIN (기획 섹션)",
        }
    data["dokkebi_os_2_planning"] = build_planning()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated: {path}")


def main() -> int:
    apply_to_file(CANONICAL)
    apply_to_file(PROJECT_COPY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
