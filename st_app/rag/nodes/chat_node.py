from __future__ import annotations

from typing import Any, Dict, List

from st_app.rag.llm import get_llm


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"]).strip()
    return ""


def chat_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = state.get("messages", [])
    question = _get_last_user_message(messages)
    if not question:
        return state

    llm = get_llm()
    prompt = (
        "너는 친절한 한국어 대화 어시스턴트야. 사용자 메시지에 간단하고 공손하게 답변해.\n\n"
        f"사용자: {question}\n"
        "어시스턴트:"
    )
    out = llm.invoke(prompt)
    answer = getattr(out, "content", str(out))

    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "meta": {"node": "chat"},
    }
    new_state = dict(state)
    new_state["messages"] = list(messages) + [assistant_msg]
    new_state["last_route"] = "chat"
    return new_state


