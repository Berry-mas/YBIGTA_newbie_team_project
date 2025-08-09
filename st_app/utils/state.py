# st_app/utils/state.py
from typing import TypedDict, Optional, Any, Dict, List

class ChatMessage(TypedDict):
    role: str       # "user" | "assistant" | "system"
    content: str

class ChatState(TypedDict, total=False):
    # 입력/출력
    user_msg: str
    last_answer: Optional[str]

    # 라우팅 힌트
    subject_name: Optional[str]

    # 대화/메모리
    messages: List[ChatMessage]

    # 추가 확장 포인트 (RAG 팀원과 공유)
    # retriever_results: List[Dict[str, Any]]
    # user_prefs: Dict[str, Any]

def new_state() -> ChatState:
    return ChatState(
        user_msg="",
        last_answer=None,
        subject_name=None,
        messages=[]
    )

def push_user(state: ChatState, text: str) -> None:
    state["user_msg"] = text
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append({"role": "user", "content": text})

def push_assistant(state: ChatState, text: str) -> None:
    state["last_answer"] = text
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append({"role": "assistant", "content": text})
