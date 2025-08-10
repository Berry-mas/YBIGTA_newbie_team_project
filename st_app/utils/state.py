"""
상태 관리를 위한 모듈
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
import json

Message = Dict[str, Any]


class ChatMessage(TypedDict):
    role: str       # "user" | "assistant" | "system"
    content: str


@dataclass
class ChatState:
    """채팅 상태를 관리하는 클래스"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_node: str = "chat"
    intent_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # RAG 관련 필드들
    k: int = 4
    last_route: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[Dict[str, Any]] = None
    
    # feature/subject-node 브랜치 호환성 필드들
    user_msg: str = ""
    last_answer: Optional[str] = None
    subject_name: Optional[str] = None
    
    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def add_intent(self, intent: str, confidence: float, reason: str):
        """의도 정보 추가"""
        intent_data = {
            "intent": intent,
            "confidence": confidence,
            "reason": reason
        }
        self.intent_history.append(intent_data)
    
    def get_last_user_message(self) -> str:
        """마지막 사용자 메시지 반환"""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return ""
    
    def get_conversation_history(self) -> str:
        """대화 히스토리를 문자열로 반환"""
        history = []
        for msg in self.messages[-10:]:  # 최근 10개 메시지만
            role = "사용자" if msg["role"] == "user" else "어시스턴트"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)
    
    def reset(self):
        """상태 초기화"""
        self.messages.clear()
        self.intent_history.clear()
        self.current_node = "chat"
        self.citations.clear()
        self.error = None
        self.last_route = None
        self.user_msg = ""
        self.last_answer = None
        self.subject_name = None
    
    def to_dict(self) -> Dict[str, Any]:
        """상태를 딕셔너리로 변환 (RAG 호환성)"""
        return {
            "messages": self.messages,
            "k": self.k,
            "last_route": self.last_route,
            "citations": self.citations,
            "error": self.error,
        }


# feature/subject-node 브랜치 호환성 함수들
def new_state() -> ChatState:
    return ChatState(
        user_msg="",
        last_answer=None,
        subject_name=None,
        messages=[]
    )


def push_user(state: ChatState, text: str) -> None:
    state.user_msg = text
    if not state.messages:
        state.messages = []
    state.messages.append({"role": "user", "content": text})


def push_assistant(state: ChatState, text: str) -> None:
    state.last_answer = text
    if not state.messages:
        state.messages = []
    state.messages.append({"role": "assistant", "content": text})
