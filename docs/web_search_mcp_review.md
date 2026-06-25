# web_search MCP 도입 검토 (Day 5 — 조사만)

작성일: 2026-06-25  
범위: 설치·pip·API 키 발급 없음

## 비교 대상

| 옵션 | 비용 | 한도 | 통합 난이도 | supervisor 호환 | 한국어 품질 |
|------|------|------|-------------|-----------------|-------------|
| **Brave Search MCP** | 유료 ($5/1000 req) | API 키별 | 중 (MCP 서버 별도) | LangGraph tool 노드 추가 필요 | 양호 |
| **Tavily** | 무료 티어 1000/월 | 제한적 | 중 (REST 또는 MCP) | `reasoner` 전 tool 호출 패턴 적합 | 양호 |
| **DuckDuckGo + requests** | $0 | 비공식, 차단 위험 | 낮 (자체 함수) | `litellm_router` 옆 유틸로 삽입 용이 | 보통 |
| **Composio 통합** | 플랜별 | Composio 쿼터 | 높 (Week 4 계획과 정합) | CrewAI/Composio Week 4 로드맵과 동일 경로 | 양호 |

## supervisor 호환성

현재 파이프라인: `input_parser` → `reasoner` (LLM 1회) → `memory_writer` → `output_formatter`.

web_search 도입 시 최소 변경:

1. `input_parser`에서 `search` 의도 감지 시 `web_search` 노드 분기 (LangGraph conditional edge)
2. 또는 `reasoner` 내 tool-calling (LiteLLM function call) — 모델별 지원 차이 주의

Telegram `/goal`·FastAPI `/goal`은 동일 `run_supervisor()` 경로이므로 **그래프 1곳만 수정**하면 됨.

## 비용·ROI (사장님 3축)

| 옵션 | 시간절감 | 비용 | ROI |
|------|----------|------|-----|
| DuckDuckGo 자체 | 빠른 PoC | $0 | 높음(단기), 운영 불안정 |
| Tavily 무료 | 중 | $0~ | **Day 6 PoC 최적** |
| Brave | 중 | 유료 | 검색 품질 필요 시 |
| Composio | 느림(Week 4) | 플랜 | 장기 통합 1곳 |

## 권장안

**1차 PoC: Tavily 무료 API (또는 DuckDuckGo로 1일 스파이크)**  
**본격 도입: Week 4 Composio MCP와 통합** (확정 스택 8개 중 Composio 이미 포함)

- **도입 시점:** Day 6 — Tavily/DuckDuckGo로 `search` 의도 1노드 PoC (2시간 이내)
- **Week 2:** CrewAI 토론 시 web_search 결과를 심판자 컨텍스트로 주입 검토
- **Week 4:** Composio로 Slack/Gmail 등과 함께 MCP 단일 게이트웨이화

## Day 6 착수 조건 (GO/NO-GO)

- [ ] `search` 의도 호출 비율 측정 (Telegram 로그 1주)
- [ ] Tavily API 키 사장님 승인
- [ ] Mem0에 검색 결과 캐시 정책 (중복 API 방지)

## 보류 사유 (Day 5에서 미구현)

- 외부 API 키·pip 추가는 사장님 승인 후
- FastAPI·CI 안전망 선행이 우선 (Day 5 옵션 C)
