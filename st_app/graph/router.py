from __future__ import annotations

from typing import Any, Dict, List

from st_app.rag.llm import get_llm
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
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


def run_graph(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = state.get("messages", [])
    question = _get_last_user_message(messages)
    if not question:
        return chat_node(state)

    route = _decide_route(question)
    if route == "subject_info":
        # 노드 응답만 반환하고, 같은 턴에서 추가 Chat 응답은 생성하지 않음
        return subject_info_node(state)
    if route == "rag_review":
        # 노드 응답만 반환하고, 같은 턴에서 추가 Chat 응답은 생성하지 않음
        return rag_review_node(state)
    # default chat
    return chat_node(state)


