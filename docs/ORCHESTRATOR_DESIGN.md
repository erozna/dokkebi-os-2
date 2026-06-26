# 도깨비 OS 오케스트레이터 설계 (Design-Only)

> 작성: 2026-06-27 · 상태: **설계만** (코드 작성은 사장님 [C] 승인 후)
> 근거: 사장님 발견 15번째 — 도깨비 OS 정체성 확정
> = **"AI 오케스트레이터 + 교차검증 + 결정만 보고"**

---

## 0. 재정의된 정체성과 설계 원칙

사장님 진짜 페인(pain):

1. **무엇을 원하는지는 알지만 어떻게 하는지 모른다.**
2. AI에게 물으면 **설명·역질문이 너무 많다.**
3. 답을 받으면 **다른 AI에 복붙해서 교차검증**한다.
4. **AI 출력을 스스로 검증할 능력이 없다** → 또 다른 AI에 복붙.
5. 이 **수동 릴레이(메신저 노릇)를 자동화**하고 싶다.

→ 도깨비 OS의 단 하나의 임무:
**사장님 대신 여러 벤더 AI를 돌려 서로 교차검증하고, 사장님께는 "결정"만 4줄로 보고한다.**

설계 원칙 4가지:

| # | 원칙 | 의미 |
|---|------|------|
| P1 | 사장님 토큰 최소 | 사장님이 읽는 글자 수 = 비용. 결론만 보고. |
| P2 | 벤더 다양성 = 신뢰 | 같은 벤더끼리 검증은 사각지대 공유. 교차검증은 **다른 제공자**로. (STEP 5c 다양성 1.0) |
| P3 | 무료 우선 | Groq/Z.ai Flash/Gemini Flash 무료 tier 우선, 유료(Anthropic/Gemini Pro)는 꼭 필요할 때만. |
| P4 | 결정만 보고 | 긴 raw 응답은 내부에만. 사장님께는 결론+신뢰도+주의+다음액션. |

---

## 0.5 사장님 진짜 그림 — 3대 패턴 (입력/처리/출력 명세)

사장님이 손으로 하던 "메신저 노릇"은 결국 3가지 패턴으로 수렴한다.
도깨비 OS는 이 3개를 자동화하는 것으로 충분하다.

### 패턴 A — 자동 요약 + 검증
> "이거 (긴 글/답변) 핵심만 뽑고, 맞는지 검증해줘."

| 항목 | 명세 |
|------|------|
| 입력 | `source_text: str`(검증 대상 답·문서), `question: str | None`(원 질문) |
| 처리 | 1) Short Report Generator로 핵심 추출 → 2) Cross-AI Validator가 **다른 벤더 2~3개**에 "이 요약이 source와 사실 일치하는가" 송신 → 3) 합의 점수 + dissent 수집 |
| 출력 | 4줄 보고: 결론(요약) / 신뢰도(합의 점수+다양성) / 주의(dissent 최대 1개) / 다음([B]복붙·[C]결정) |
| 재활용 | `call_llm`(다벤더), `red_team.diversity_check`, `usage_doc`(압축) |

### 패턴 B — 자동 토론
> "이 결정/설계, AI들끼리 토론시켜서 결론만 줘."

| 항목 | 명세 |
|------|------|
| 입력 | `topic: str` 또는 `IntentResult`+`DoDResult` |
| 처리 | **기존 4역할 토론 그대로** (장인→심판자→검사관→재판장) → Red Team(다양성 1.0, 이번 턴 수정) → 합의안 |
| 출력 | 4줄 보고: 결론(합의안 1줄) / 신뢰도(confidence+다양성) / 주의(심판자 약점 최대 1개) / 다음 액션 |
| 재활용 | **`app/routers/crew_debate.run_debate` 100% 재활용.** 신규 코드 = Short Report 압축 어댑터뿐 |

### 패턴 C — 자동 코드 검증
> "이 코드/로직 맞아? 다른 AI한테도 물어봐줘."

| 항목 | 명세 |
|------|------|
| 입력 | `code: str` 또는 파일 경로, `claim: str | None`(검증할 주장) |
| 처리 | 1) Cross-AI Validator가 다벤더에 "이 코드가 claim을 만족하는가/버그 있는가" 송신 → 2) 의견 충돌 크면 **패턴 B(4역할 토론)로 escalate** → 3) (가능 시) `whitelist.run_pytest`로 실제 실행 교차검증 |
| 출력 | 4줄 보고: 결론(통과/결함) / 신뢰도 / 주의(가장 큰 결함) / 다음(수정안 [B] 또는 [C]) |
| 재활용 | `call_llm`, `crew_debate`(escalate), `app/tools/whitelist.run_pytest`(STEP 7-A) |

> 3패턴 공통 출구 = **Short Report Generator(4줄)**. 공통 신뢰 근거 = **Cross-AI Validator의 벤더 다양성**.

---

## 1. [필요] Cross-AI Validator

### 1.1 목적
사장님이 손으로 하던 "한 AI 답 → 다른 AI에 복붙해 검증" 루프를 자동화.
N개 서로 다른 벤더 AI에게 **동일 질문**을 자동 송신 → 응답 자동 수집 → **합의 점수** 산출.

### 1.2 입력/출력 (계약, 코드 아님)
- 입력: `question: str`, `validators: list[str]`(모델 ID, 기본 = 4제공자 로스터), `reference_answer: str | None`(검증 대상 답이 이미 있으면)
- 출력 (제안):
  - `answers: dict[model -> str]` — 각 AI raw 응답 (내부 보관)
  - `agreement_score: float` — 0.0~1.0 (응답 간 합의 정도)
  - `consensus: str` — 공통 핵심
  - `dissent: list[str]` — 소수 의견/충돌점 (사장님이 봐야 할 위험)
  - `provider_diversity: float` — STEP 5c 재사용 (다양성 1.0 보장)

### 1.3 합의 점수 산출 (3안 — [C] 선택 대기)
- (가) **임베딩 코사인 평균** — 응답 쌍별 의미 유사도 평균. 빠르고 무료(로컬 임베딩). 뉘앙스 약함.
- (나) **심판 AI 1회 호출** — 별도 모델이 "이 N개 답이 일치하는가"를 0~1로 채점. 정확하나 1회 추가 호출.
- (다) **하이브리드** — 임베딩으로 1차 거른 뒤, 임계 미달일 때만 (나) 호출. 비용/정확도 균형. **추천.**

### 1.4 기존 자산 재활용
- 모델 호출: `app.litellm_router.call_llm(..., return_usage=True, fallback=...)` 그대로.
- 다양성: `app.routers.red_team.diversity_check()` 그대로 (이번 턴 actual_models 버그 수정 완료).
- 임베딩: Mem0/Chroma 임베딩 파이프라인 재사용 가능.

### 1.5 CrewAI 4역할 토론과의 관계
- **Cross-AI Validator = 수평 검증** (같은 질문, N개 답, 일치도). 빠름.
- **CrewAI 4역할 토론 = 수직 심화** (설계→약점→실현성→합의). 깊음, 느림, 비쌈.
- 라우팅 제안: 단순 사실 검증 → Validator / 의사결정·설계 → 4역할 토론.

---

## 2. [필요] Short Report Generator

### 2.1 목적 (P1·P4 직격)
긴 내부 산출물(토론 transcript, N개 AI 응답, Red Team 결과)을
**사장님용 4줄**로 자동 압축.

### 2.2 출력 고정 양식 (4줄 + 메타)
```
결론:   (한 문장 — 사장님이 할 결정)
신뢰도: 0.0~1.0 (+ 근거 한 줄: 다양성 N제공자 합의)
주의:   (가장 큰 리스크 1개 — dissent에서 추출)
다음:   ([B] 복붙 / [C] 사장님 결정 / [A] 자동실행 중 하나)
─ 비용 $X.XXXX · 소요 Ns · 모델 N개
```

### 2.3 입력
- `FlowResult`(canonical_flow) 또는 `CrossValidatorResult` 또는 `DebateResult`.
- 즉, 어떤 내부 산출물이든 받아 4줄로 정규화하는 **단일 출구(出口)**.

### 2.4 기존 자산 재활용
- `app.routers.usage_doc` 가 이미 "결과 중심" 마크다운을 만든다 → Short Report는 그 **압축판(4줄)**.
  - usage_doc = 상세(텔레그램 펼침), Short Report = 헤드라인(알림 1개).
- 압축 방법: (가) 규칙 기반 슬라이싱(무료, 즉시) (나) Flash 1회 요약 호출. **(가) 우선, 길면 (나) 폴백.**

---

## 3. [재활용] CrewAI 4역할 토론

- **이미 구현됨** (`app/routers/crew_debate.py`, 4제공자, Red Team 연동).
- 신규 정체성에서도 **핵심 자산** — 사장님이 "내가 GPT랑 토론한 거 검증해줘" 할 때의 수직 심화 엔진.
- 흡수안: Cross-AI Validator를 **얕은 1차 게이트**로 두고, 의견 충돌(dissent)이 크거나 의사결정급이면 4역할 토론으로 **승급(escalate)**.
- 중복 제거: 토론 내부의 다양성 측정은 이번 턴 수정한 `actual_models` 경로로 통일 (stale ROLE_MODELS 제거 완료).

---

## 4. [검토] PAL/Zen MCP 복구 — 두 시나리오 비교

진단 요지(상세는 dialogue.md): `mcps/user-pal`에 tools 0개 = dead. 원인 = **API 키 env 블록 없음**(gemini는 있음) + `npx github:` cold-start 타임아웃. node/git 정상. 즉시 크래시는 없음.

### 시나리오 (가) — PAL 복구 후
- 구성: `~/.cursor/mcp.json` pal을 uvx(또는 로컬 고정버전) + API 키 env로 교체.
- 이점: "한 AI가 다른 AI에게 자동 위임"을 **MCP 레이어에서** 제공 → Cursor/Claude Desktop에서도 직접 호출 가능.
- 단점: ① 키/버전 관리 추가 ② 합의 점수·다양성 측정이 PAL 내부 로직(우리 통제 밖) ③ Short Report 4줄 양식과 별도 통합 필요.
- 영향: Cross-AI Validator와 **기능 중첩** → Validator는 PAL을 백엔드로 쓰는 얇은 래퍼로 축소 가능.

### 시나리오 (나) — PAL 미복구 (도깨비 내부 Validator)
- 구성: Cross-AI Validator를 `call_llm`(LiteLLM 4제공자) 위에 자체 구현. 합의/다양성은 우리 `diversity_check` 재사용.
- 이점: ① 키·라우팅·폴백 이미 검증됨(`_zai_kwargs` 등) ② 합의 산출·4줄 보고를 **우리가 완전 통제** ③ 외부 MCP 의존 0.
- 단점: Validator 코드 직접 작성(중간 작업량). MCP 레이어 노출은 없음(OS 내부 전용).
- 커버리지: 사장님 진짜 그림(패턴 A/B/C) **90%+ 달성**.

### 판정
**(나) 우선 — PAL 미복구로 진행, Validator 자체 구현.** PAL은 다음 턴 사장님 [D] 에러 캡처 후 *선택적* 백엔드로 검토(시나리오 가의 래퍼화). 복구 자체가 블로커는 아님.

---

## 5. [보류] Capability Router 5-Way

- 현 정체성에선 실사용 분기가 사실상 2개:
  - **[B] Bridge** — Cursor/정액제 AI에 복붙 (가장 자주).
  - **[C] Ask** — 사장님 가치 판단.
- `[A] Auto`(화이트리스트 4종)는 검증 단계에서 가끔, `[D] Hands`/`[E] Background`는 드묾.
- **결론: 5-Way 라우터 자체는 유지(이미 구현). 신규 투자 보류.** [B]+[C] 경로 품질에 집중.

---

## 6. 우선순위 제안 (사장님 [C] 대기)

| 순위 | 모듈 | 이유 | 예상 작업량 |
|------|------|------|-------------|
| 1 | Short Report Generator | P1·P4 즉효, usage_doc 압축이라 작음 | 소 (반나절) |
| 2 | Cross-AI Validator | 사장님 수동 릴레이 직격 자동화 | 중 (1~2일) |
| 3 | (유지) 4역할 토론 escalate 연결 | Validator 완성 후 연결 | 소 |
| 보류 | PAL/Zen 복구 | 내부 Validator로 대체 가능 | 진단 후 결정 |
| 보류 | 5-Way 신규 투자 | [B]+[C]만 자주 씀 | - |

> ⚠️ 위 전부 **설계만**. 코드 착수는 사장님이 순위/합의방식([C]) 결정 후.
