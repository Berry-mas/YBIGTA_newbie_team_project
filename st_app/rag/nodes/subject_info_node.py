from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from st_app.rag.llm import get_llm


def _get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"]).strip()
    return ""


def _load_subjects() -> Dict[str, Any]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db", "subject_information"))
    path = os.path.join(base_dir, "subjects.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def subject_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = state.get("messages", [])
    question = _get_last_user_message(messages)
    if not question:
        return state

    subjects = _load_subjects()
    # Naive subject matching: pick best key contained in the question
    match_key = None
    for key in subjects.keys():
        if key in question:
            match_key = key
            break

    info = subjects.get(match_key) if match_key else None
    context = json.dumps(info, ensure_ascii=False, indent=2) if info else "{}"

    llm = get_llm()
    prompt = (
        "너는 대상의 기본 정보를 설명하는 어시스턴트야. 다음 SUBJECT_INFO만 근거로 간결하게 설명해.\n"
        "- 근거가 없으면 모른다고 말해.\n\n"
        f"질문: {question}\n\nSUBJECT_INFO:\n{context}\n\n"
        "응답:"
    )
    out = llm.invoke(prompt)
    answer = getattr(out, "content", str(out))

    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "meta": {"node": "subject_info", "subject": match_key},
    }
    new_state = dict(state)
    new_state["messages"] = list(messages) + [assistant_msg]
    new_state["last_route"] = "subject_info"
    return new_state


