# 도깨비 OS 2.0 아키텍처 (현재 + 로드맵)

> SHARED_BRAIN `dokkebi_os_2_planning` 기준. **Week 1~Day 6 구현 반영**, Week 2~5는 DoD 수준.

## 전체 플로 (현재 동작)

```mermaid
flowchart TB
    subgraph ingress [진입점 - 구현됨]
        TG[Telegram Bot<br/>/ping /memory /goal]
        API[FastAPI :8765<br/>POST /goal + Bearer<br/>GET /healthz]
    end

    subgraph supervisor [LangGraph Supervisor - 구현됨]
        IP[input_parser<br/>키워드 의도]
        R[reasoner<br/>LiteLLM 1회]
        MW[memory_writer<br/>Mem0 저장]
        OF[output_formatter<br/>라벨 응답]
        IP --> R --> MW --> OF
    end

    subgraph context [컨텍스트 주입 - Day 6]
        MEM[(Mem0 + Chroma<br/>89건)]
        WEB[Tavily web_search<br/>CI=mock]
        R --> MEM
        R --> WEB
    end

    subgraph llm [LiteLLM Gateway]
        SONNET[Claude Sonnet]
        GEMINI[Gemini Flash]
        GROQ[Groq Llama]
    end

    R --> llm

    TG --> supervisor
    API --> supervisor
    OF --> TG
    OF --> API

    subgraph ci [안전망 - Day 5]
        GHA[GitHub Actions<br/>pytest + ruff]
        GL[gitleaks]
    end
```

## 5주 로드맵 (미구현 = 점선)

```mermaid
flowchart LR
    W1[Week 1<br/>백엔드+메모리<br/>DONE]
    W2[Week 2<br/>CrewAI 4역할]
    W3[Week 3<br/>Tauri 착수]
    W4[Week 4<br/>Composio MCP]
    W5[Week 5<br/>Self-Harness]

    W1 --> W2 --> W3 --> W4 --> W5
```

## Week 2 이후 (설계만, 코드 없음)

| 구간 | 내용 | 상태 |
|------|------|------|
| CrewAI 토론 | 장인/심판자/검사관/재판장 | 미착수 |
| Tauri UI | CopilotKit + React | Week 3 |
| Composio | MCP 통합 | Week 4 |
| Self-Harness | KPI + NAS cron | Week 5 |

## 무엇이 **아직** 그려지지 않았나

- CrewAI 노드별 프롬프트·토론 루프 상세 시퀀스
- Tauri 화면 와이어프레임
- Self-Harness KPI 5개 정의
- ~~FastAPI 인증~~ → `GOAL_API_TOKEN` Bearer / `X-API-Key` (설정 시만)

이 문서가 **현 시점의 공식 플로차트**입니다. Claude 없이 Cursor가 Week 2부터 이어갈 수 있습니다.
