# 새 Claude 채팅 인계 프롬프트

아래 블록 전체를 새 채팅 첫 메시지로 복사하세요.

---

```
도깨비 OS 2.0 — Day 4 잔여 작업 진행.

[배경]
효남금속(주) 1인 기업가, 한국어, Magok 거주, 5인 가구.
도깨비 OS 2.0 = Tauri + LangGraph + CrewAI + Mem0+Chroma + LiteLLM (5주 로드맵).
프로젝트: D:/SynologyDrive/dokkebi/projects/shared-brain-day1
GitHub: https://github.com/erozna/dokkebi-os-2 (branch: main)

[Day 3 완료 — Week 1 마일스톤 7/7]
- 중복 메모리 88건 청산 → 85건
- LangGraph supervisor 4노드 + LiteLLM router
- E2E 테스트 5/5, 보안 점검 통과

[Day 3 발견점 3건]
1. 카테고리 미분류 85건 백필 필요 (episodic/semantic/procedural)
2. 도깨비 도구 부재 → web_search MCP 추가 필요
3. 시스템 프롬프트에 사장님 페르소나 + 이모지 금지 주입 필요

[Day 4 완료]
- 봇 실전 검증: /ping OK, /memory OK(카테고리 백필 필요), /goal OK (Claude Sonnet 4.6, 5.3초)
- gh CLI 설치, origin/master 정리 (main only)

[Day 4 잔여]
- FastAPI /goal HTTP 엔드포인트
- Mem0 카테고리 필터 + 85건 백필
- GitHub Actions CI
- LangSmith 연동 (선택)
- web_search MCP
- 첫 도깨비 자기소개

[상세 컨텍스트]
SHARED_BRAIN.json → dokkebi_os_2_planning 섹션 전체 읽기.

[응답 형식 강제]
- 한국어, 결과 먼저, 이모지 금지
- 5단계: 전략적 의도 / 실행 로드맵 / 기대 효과 / 더 높은 단계 / 마법 프롬프트
- 끝에 "가장 불확실한 부분 1가지" 명시
- [시간절감/비용/ROI] 판단
- 4단계 이상 프로세스는 요약 후 승인
- 컨텍스트 70% 시 새 창 권장
```

---

## 파일 위치

| 항목 | 경로 |
|------|------|
| 기획 JSON | `SHARED_BRAIN.json` → `dokkebi_os_2_planning` |
| 정본 | `D:\SynologyDrive\dokkebi\DOKKEBI_CORE\01_SHARED_BRAIN\SHARED_BRAIN.json` |
| 동기화 | `python scripts/update_planning_section.py` |
