"""
상태 관리를 위한 모듈
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field
import json


@dataclass
class ChatState:
    """채팅 상태를 관리하는 클래스"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_node: str = "chat"
    intent_history: List[Dict[str, Any]] = field(default_factory=list)
    
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
