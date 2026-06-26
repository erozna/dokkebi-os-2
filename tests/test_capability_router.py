"""Capability Router 5-Way 분류 테스트 — 헌법 3조 STEP 6 / 4조."""

from __future__ import annotations

from app.routers.capability_router import RouteDecision, classify


def test_route_d_keyword_oauth():
    d = classify("Google OAuth 토큰 발급 받아줘")
    assert d.route == "D"


def test_route_d_flag_external_auth():
    d = classify({"task": "SaaS 연결", "needs_external_auth": True})
    assert d.route == "D"


def test_route_c_keyword_decision():
    d = classify("재판장 모델 Gemini Flash로 바꿀지 결정")
    assert d.route == "C"


def test_route_c_flag_value_judgment():
    d = classify({"task": "방향 잡기", "value_judgment": True})
    assert d.route == "C"


def test_route_e_keyword_background():
    d = classify("매주 Tech Radar 모니터링 자동 백업")
    assert d.route == "E"


def test_route_b_keyword_bridge():
    d = classify("이 리서치 자료 요약하고 초안 글쓰기")
    assert d.route == "B"
    assert d.target_channel  # 채널 지정됨


def test_route_a_keyword_auto():
    d = classify("yt-dlp로 영상 메타데이터 수집 스크립트 작성")
    assert d.route == "A"


def test_route_a_default_no_keyword():
    d = classify("그냥 평범한 작업 항목")
    assert d.route == "A"
    assert isinstance(d, RouteDecision)


def test_priority_d_over_a():
    """[D] 권한 키워드가 [A] 자동화 키워드보다 우선(안전 차단)."""
    d = classify("API 스크립트 실행하려면 먼저 결제 카드 등록 필요")
    assert d.route == "D"
