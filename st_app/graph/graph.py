from __future__ import annotations

from typing import Any, Dict, List, TypedDict
from typing_extensions import Annotated
import operator

from langgraph.graph import StateGraph, START, END

from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node
from st_app.graph.router import _decide_route  # reuse the LLM routing logic


class GraphState(TypedDict, total=False):
    messages: Annotated[List[Dict[str, Any]], operator.add]
    k: int
    last_route: str
    citations: Annotated[List[Dict[str, Any]], operator.add]
    error: Dict[str, Any]


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
    # no-op; decision is taken by conditional edge function
    return {}


def _route_selector(state: GraphState) -> str:
    messages = state.get("messages", [])
    question = ""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            question = str(m["content"]).strip()
            break
    if not question:
        return "chat"
    return _decide_route(question)


def get_graph_app():
    graph = StateGraph(GraphState)
    graph.add_node("router", _router_passthrough)
    graph.add_node("chat", _wrap_partial(chat_node))
    graph.add_node("subject_info", _wrap_partial(subject_info_node))
    graph.add_node("rag_review", _wrap_partial(rag_review_node))

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


