"""LangGraph Supervisor — 4노드 StateGraph."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app.config import ROOT, ensure_env_from_credentials
from app.litellm_router import call_llm, map_parser_intent
from app.mem0_router import save_to_mem0
from app.memory_service import search_memories

CHECKPOINT_DB = ROOT / "data" / "supervisor_state.db"
_CHECKPOINT_CONN: sqlite3.Connection | None = None
_GRAPH = None


class SupervisorState(TypedDict, total=False):
    """Supervisor 상태 스키마."""

    input: str
    intent: str
    model_used: str
    response: str
    memory_id: str
    timestamp: str
    elapsed_sec: float
    thread_id: str


def _classify_intent(text: str) -> str:
    """한국어 입력 의도 분류: code / search / dialogue / command."""
    lowered = (text or "").lower()
    code_keys = ("함수", "파이썬", "코드", "작성", "class ", "def ", "implement", "스크립트")
    search_keys = ("검색", "찾아", "알려줘", "날씨", "뭐야", "무엇")
    dialogue_keys = ("요약", "대화", "이전", "기억", "정리")

    if any(k in text or k in lowered for k in code_keys):
        return "code"
    if any(k in text for k in dialogue_keys):
        return "dialogue"
    if any(k in text for k in search_keys):
        return "search"
    return "command"


def input_parser(state: SupervisorState) -> SupervisorState:
    """노드1: 입력 파싱 + 의도 분류."""
    user_input = (state.get("input") or "").strip()
    intent = _classify_intent(user_input)
    return {
        **state,
        "input": user_input,
        "intent": intent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def reasoner(state: SupervisorState) -> SupervisorState:
    """노드2: 의도별 모델 호출."""
    t0 = time.perf_counter()
    user_input = state.get("input") or ""
    parser_intent = state.get("intent") or "command"
    router_intent = map_parser_intent(parser_intent, user_input)

    prompt = user_input
    # 요약·이전 대화: Mem0 검색 컨텍스트 주입
    thread_id = state.get("thread_id") or "supervisor-default"
    if router_intent == "summary" or "이전" in user_input:
        hits = search_memories(user_input, limit=3, user_id=thread_id)
        if hits:
            ctx = "\n".join(
                f"- {(h.get('memory') or h.get('data') or '')[:200]}" for h in hits
            )
            prompt = f"다음 기억을 참고해 요약하세요.\n{ctx}\n\n질문: {user_input}"

    response, model_used = call_llm(prompt, router_intent=router_intent)
    elapsed = time.perf_counter() - t0
    return {
        **state,
        "response": response,
        "model_used": model_used,
        "elapsed_sec": elapsed,
    }


def memory_writer(state: SupervisorState) -> SupervisorState:
    """노드3: 응답을 Mem0에 저장."""
    ensure_env_from_credentials()
    text = f"Q: {state.get('input', '')}\nA: {state.get('response', '')}"
    user_id = state.get("thread_id") or "supervisor-default"
    saved = save_to_mem0(
        text,
        user_id=user_id,
        extra_metadata={"source": "supervisor", "intent": state.get("intent", "")},
    )

    memory_id = ""
    result = saved.get("result")
    if isinstance(result, dict):
        rows = result.get("results") or []
        if rows and isinstance(rows[0], dict):
            memory_id = str(rows[0].get("id") or rows[0].get("memory_id") or "")
    return {**state, "memory_id": memory_id}


def output_formatter(state: SupervisorState) -> SupervisorState:
    """노드4: 한국어 최종 응답 포맷."""
    body = state.get("response") or ""
    formatted = (
        f"🐺 도깨비 응답\n\n"
        f"{body}\n\n"
        f"💾 memory_id: {state.get('memory_id', '-')}\n"
        f"🤖 사용 모델: {state.get('model_used', '-')}\n"
        f"⏱ 처리 시간: {state.get('elapsed_sec', 0.0):.1f}s"
    )
    return {**state, "response": formatted}


def _get_checkpointer() -> SqliteSaver:
    """SQLite 체크포인터 (동기 conn 유지)."""
    global _CHECKPOINT_CONN
    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    if _CHECKPOINT_CONN is None:
        _CHECKPOINT_CONN = sqlite3.connect(
            str(CHECKPOINT_DB),
            check_same_thread=False,
        )
    return SqliteSaver(_CHECKPOINT_CONN)


def build_graph():
    """컴파일된 Supervisor 그래프."""
    graph = StateGraph(SupervisorState)
    graph.add_node("input_parser", input_parser)
    graph.add_node("reasoner", reasoner)
    graph.add_node("memory_writer", memory_writer)
    graph.add_node("output_formatter", output_formatter)

    graph.add_edge(START, "input_parser")
    graph.add_edge("input_parser", "reasoner")
    graph.add_edge("reasoner", "memory_writer")
    graph.add_edge("memory_writer", "output_formatter")
    graph.add_edge("output_formatter", END)

    return graph.compile(checkpointer=_get_checkpointer())


def get_supervisor():
    """싱글톤 그래프."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def run_supervisor(user_input: str, *, thread_id: str = "default") -> SupervisorState:
    """Supervisor 실행 헬퍼."""
    app = get_supervisor()
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"input": user_input, "thread_id": thread_id},
        config=config,
    )
    return result
