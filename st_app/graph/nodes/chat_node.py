from __future__ import annotations

from typing import Any, Dict, List

from st_app.rag.llm import get_llm


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """마지막 사용자 메시지 추출"""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"]).strip()
    return ""


def chat_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """일반 대화를 처리하는 노드"""
    messages: List[Dict[str, Any]] = state.get("messages", [])
    question = _get_last_user_message(messages)
    if not question:
        return state

    # ChatState 객체인 경우 메모리 기능 활용
    if hasattr(state, 'get_recent_context'):
        # ChatState 객체 사용
        conversation_context = state.get_recent_context()
    else:
        # 기존 방식 (딕셔너리)
        conversation_context = _build_conversation_context(messages)
    
    llm = get_llm()
    prompt = (
        "너는 친절하고 도움이 되는 한국어 대화 어시스턴트야. "
        "사용자와 자연스럽게 대화하고, 이전 대화 맥락과 중요한 기억들을 고려해서 답변해.\n\n"
        f"컨텍스트:\n{conversation_context}\n\n"
        f"사용자: {question}\n"
        "어시스턴트:"
    )
    
    try:
        out = llm.invoke(prompt)
        answer = getattr(out, "content", str(out))
    except Exception as e:
        answer = f"죄송합니다. 일시적인 오류가 발생했습니다: {str(e)}"

    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "meta": {"node": "chat", "context_length": len(conversation_context)},
    }
    
    new_state = dict(state)
    new_state["messages"] = list(messages) + [assistant_msg]
    new_state["last_route"] = "chat"
    
    # ChatState 객체인 경우 메모리에 저장
    if hasattr(state, 'add_message'):
        state.add_message("assistant", answer)
    
    return new_state


def _build_conversation_context(messages: List[Dict[str, Any]], max_history: int = 6) -> str:
    """대화 히스토리 컨텍스트 구성 (기존 호환성)"""
    if not messages:
        return ""
    
    # 최근 대화만 사용 (메모리 효율성)
    recent_messages = messages[-max_history:]
    context_parts = []
    
    for msg in recent_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            context_parts.append(f"사용자: {content}")
        elif role == "assistant":
            context_parts.append(f"어시스턴트: {content}")
    
    return "\n".join(context_parts)


