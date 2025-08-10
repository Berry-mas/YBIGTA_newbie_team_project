from __future__ import annotations

from typing import Any, Dict, List
import traceback

from st_app.rag.retriever import get_retriever, get_faiss_retriever
from st_app.rag.llm import get_llm
from st_app.rag.prompt import build_review_prompt


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"]).strip()
    return ""


def _format_docs(docs: List[Any], max_chars: int = 1400) -> str:
    chunks = []
    for i, d in enumerate(docs, 1):
        page = getattr(d, "page_content", str(d))
        meta = getattr(d, "metadata", {}) or {}
        src = meta.get("source") or meta.get("file") or meta.get("path") or "unknown"
        chunks.append(f"[DOC {i}]\nSOURCE: {src}\nCONTENT: {page}\n")
    context = "\n\n".join(chunks)
    if len(context) > max_chars:
        context = context[: max_chars - 3] + "..."
    return context


def _extract_citations(docs: List[Any]) -> List[Dict[str, Any]]:
    cites: List[Dict[str, Any]] = []
    for d in docs:
        meta = getattr(d, "metadata", {}) or {}
        score = getattr(d, "score", None) or meta.get("score")
        cites.append({"source_id": meta.get("source") or meta.get("path") or "unknown", "score": score, "metadata": meta})
    return cites


def rag_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        messages: List[Dict[str, Any]] = state.get("messages", [])
        question: str = _get_last_user_message(messages)
        if not question:
            return state

        k: int = int(state.get("k", 4))

        # 우선 API 임베딩 사용, 실패 시 TF-IDF 폴백
        try:
            retriever = get_faiss_retriever(use_api=True)
            print("API 임베딩 사용")
        except Exception as e:
            print(f"API 임베딩 실패, TF-IDF 폴백: {e}")
            retriever = get_retriever()
        llm = get_llm()

        docs: List[Any] = retriever.get_relevant_documents(question)[:k]
        context = _format_docs(docs)
        citations = _extract_citations(docs)

        prompt_text = build_review_prompt(question, context)
        if hasattr(llm, "invoke"):
            llm_out = llm.invoke(prompt_text)
            answer_text = getattr(llm_out, "content", None) or str(llm_out)
        else:
            answer_text = str(llm(prompt_text))

        assistant_msg = {
            "role": "assistant",
            "content": answer_text,
            "meta": {"node": "rag_review", "citations": citations},
        }
        new_state = dict(state)
        new_state["messages"] = list(messages) + [assistant_msg]
        new_state["citations"] = citations
        new_state["last_route"] = "rag_review"
        return new_state
    except Exception as e:
        debug_tb = traceback.format_exc()
        fallback_msg = {
            "role": "assistant",
            "content": f"리뷰 RAG 처리 중 오류가 발생했어요. 사유: {e}",
            "meta": {"node": "rag_review", "error": str(e)},
        }
        new_state = dict(state)
        new_state.setdefault("messages", state.get("messages", [])).append(fallback_msg)
        new_state["error"] = {"node": "rag_review", "detail": str(e), "traceback": debug_tb}
        new_state["last_route"] = "rag_review:error"
        return new_state


