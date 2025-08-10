from __future__ import annotations

from typing import Any, Dict, List, TypedDict
from typing_extensions import Annotated
import operator

from langgraph.graph import StateGraph, START, END

from st_app.rag.llm import get_llm
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node


class GraphState(TypedDict, total=False):
    messages: Annotated[List[Dict[str, Any]], operator.add]
    k: int
    last_route: str
    citations: Annotated[List[Dict[str, Any]], operator.add]
    error: Dict[str, Any]


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """마지막 사용자 메시지 추출"""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"]).strip()
    return ""


def _decide_route(question: str) -> str:
    """LLM 기반 라우팅. 반환: chat | subject_info | rag_review

    - 한국어 지시 강화, 후처리로 한국어 키워드 보정.
    - 모호 시 질문 텍스트에 대한 휴리스틱 적용.
    """
    llm = get_llm()
    prompt = (
        "너는 라우팅 판단자다. 사용자의 질문이 어떤 처리로 가야 할지 '정확히 하나'만 선택해라.\n"
        "가능한 선택지(영문 토큰만 출력): chat | subject_info | rag_review\n"
        "규칙:\n"
        "- 대상(제품/작품/인물)의 기본 정보/스펙/설명/저자/제조사 등을 물으면 subject_info\n"
        "- 리뷰/후기/요약/인용 등 사용자 반응을 근거로 한 답변이 필요하면 rag_review\n"
        "- 그 외 일반 대화는 chat\n"
        "출력 형식: 위 토큰 중 하나만 단독으로 출력 (예: rag_review)\n\n"
        f"질문: {question}\n"
        "답변:"
    )
    out = llm.invoke(prompt)
    decision_raw = (getattr(out, "content", str(out)) or "").strip()
    decision = decision_raw.lower().replace(" ", "").replace("\n", "").replace("\t", "")
    decision = decision.strip('\"\'')

    subj_markers = ["subject_info", "subjectinfo", "subject", "정보", "스펙", "특징", "저자", "작가", "제조사", "소개", "설명"]
    review_markers = ["rag_review", "ragreview", "rag", "review", "리뷰", "후기", "요약", "인용"]

    if any(tok in decision for tok in subj_markers):
        return "subject_info"
    if any(tok in decision for tok in review_markers):
        return "rag_review"
    if decision in {"chat", "subject_info", "rag_review"}:
        return decision

    q = (question or "").lower()
    if any(kw in q for kw in ["리뷰", "후기", "요약", "인용"]):
        return "rag_review"
    if any(kw in q for kw in ["정보", "스펙", "특징", "저자", "작가", "제조사", "설명", "가격"]):
        return "subject_info"
    return "chat"


def _wrap_partial(node_fn):
    """Wrap our existing node that returns full state into a partial updater.

    Returns only delta for messages/citations/last_route so LangGraph can merge.
    """

    def _inner(state: GraphState) -> GraphState:
        out = node_fn(dict(state))
        # compute delta: last assistant message, citations, last_route
        new_msgs = out.get("messages", [])
        last_msg = new_msgs[-1] if new_msgs else None
        delta: GraphState = {}
        if last_msg:
            delta["messages"] = [last_msg]
        if out.get("citations"):
            delta["citations"] = out["citations"]
        if out.get("last_route"):
            delta["last_route"] = out["last_route"]
        if out.get("error"):
            delta["error"] = out["error"]
        return delta

    return _inner


def _router_passthrough(state: GraphState) -> GraphState:
    """라우터 노드 - no-op; decision is taken by conditional edge function"""
    return {}


def _route_selector(state: GraphState) -> str:
    """라우팅 선택자 - LLM 기반 의도 분석"""
    messages = state.get("messages", [])
    question = _get_last_user_message(messages)
    if not question:
        return "chat"
    return _decide_route(question)


def get_graph_app():
    """LangGraph 애플리케이션 생성"""
    graph = StateGraph(GraphState)
    
    # 노드 추가
    graph.add_node("router", _router_passthrough)
    graph.add_node("chat", _wrap_partial(chat_node))
    graph.add_node("subject_info", _wrap_partial(subject_info_node))
    graph.add_node("rag_review", _wrap_partial(rag_review_node))

    # 엣지 추가
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_selector,
        {
            "chat": "chat",
            "subject_info": "subject_info",
            "rag_review": "rag_review",
        },
    )
    # 한 턴에 중복 응답이 보이지 않도록, 각 노드에서 바로 종료
    graph.add_edge("subject_info", END)
    graph.add_edge("rag_review", END)
    graph.add_edge("chat", END)

    return graph.compile()


def run_graph(state: Dict[str, Any]) -> Dict[str, Any]:
    """기존 호환성을 위한 함수 - LangGraph 앱 실행"""
    try:
        app = get_graph_app()
        return app.invoke(state)
    except Exception as e:
        # 폴백: 간단한 라우팅
        messages: List[Dict[str, Any]] = state.get("messages", [])
        question = _get_last_user_message(messages)
        if not question:
            return chat_node(state)

        route = _decide_route(question)
        if route == "subject_info":
            return subject_info_node(state)
        if route == "rag_review":
            return rag_review_node(state)
        return chat_node(state)


