"""
상태 관리를 위한 모듈
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
import json
import time


Message = Dict[str, Any]


class ChatMessage(TypedDict):
    role: str       # "user" | "assistant" | "system"
    content: str


@dataclass
class MemoryItem:
    """메모리 아이템"""
    content: str
    timestamp: float
    importance: float  # 0.0 ~ 1.0
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        return cls(
            content=data["content"],
            timestamp=data["timestamp"],
            importance=data["importance"],
            context=data["context"]
        )


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
    
    # 메모리 관련 필드들
    short_term_memory: List[MemoryItem] = field(default_factory=list)  # 최근 대화
    long_term_memory: List[MemoryItem] = field(default_factory=list)   # 중요 정보
    memory_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_short_term": 40,
        "max_long_term": 100,
        "importance_threshold": 0.7,
        "memory_decay_days": 30
    })
    
    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.messages.append({
            "role": role,
            "content": content
        })
        
        # 메모리에 중요 정보 저장
        if role == "assistant":
            self._add_to_memory(content, importance=0.6, context={"type": "assistant_message"})
    
    def add_intent(self, intent: str, confidence: float, reason: str):
        """의도 정보 추가"""
        intent_data = {
            "intent": intent,
            "confidence": confidence,
            "reason": reason
        }
        self.intent_history.append(intent_data)
        
        # 높은 신뢰도의 의도는 메모리에 저장
        if confidence > 0.8:
            self._add_to_memory(f"의도: {intent} (신뢰도: {confidence:.2f})", 
                              importance=confidence, context={"type": "intent", "intent": intent})
    
    def get_last_user_message(self) -> str:
        """마지막 사용자 메시지 반환"""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return ""
    
    def get_conversation_history(self, max_messages: int = 10) -> str:
        """대화 히스토리를 문자열로 반환"""
        history = []
        for msg in self.messages[-max_messages:]:
            role = "사용자" if msg["role"] == "user" else "어시스턴트"
            history.append(f"{role}: {msg['content']}")
        return "\n".join(history)
    
    def get_memory_context(self, max_items: int = 5) -> str:
        """메모리 컨텍스트 반환"""
        # 장기 메모리에서 중요도 높은 항목들
        important_memories = sorted(
            self.long_term_memory, 
            key=lambda x: x.importance, 
            reverse=True
        )[:max_items]
        
        if not important_memories:
            return ""
        
        context_parts = ["[중요한 기억들]"]
        for memory in important_memories:
            context_parts.append(f"- {memory.content}")
        
        return "\n".join(context_parts)
    
    def _add_to_memory(self, content: str, importance: float = 0.5, 
                      context: Optional[Dict[str, Any]] = None):
        """메모리에 항목 추가"""
        memory_item = MemoryItem(
            content=content,
            timestamp=time.time(),
            importance=importance,
            context=context or {}
        )
        
        # 단기 메모리에 추가
        self.short_term_memory.append(memory_item)
        
        # 중요도가 높으면 장기 메모리에도 추가
        if importance >= self.memory_config["importance_threshold"]:
            self.long_term_memory.append(memory_item)
        
        # 메모리 크기 제한
        self._cleanup_memory()
    
    def _cleanup_memory(self):
        """메모리 정리"""
        # 단기 메모리 제한
        if len(self.short_term_memory) > self.memory_config["max_short_term"]:
            self.short_term_memory = self.short_term_memory[-self.memory_config["max_short_term"]:]
        
        # 장기 메모리 제한
        if len(self.long_term_memory) > self.memory_config["max_long_term"]:
            # 중요도 순으로 정렬하여 상위 항목들만 유지
            self.long_term_memory = sorted(
                self.long_term_memory, 
                key=lambda x: x.importance, 
                reverse=True
            )[:self.memory_config["max_long_term"]]
        
        # 오래된 메모리 제거 (30일 이상)
        current_time = time.time()
        decay_seconds = self.memory_config["memory_decay_days"] * 24 * 3600
        
        self.long_term_memory = [
            item for item in self.long_term_memory
            if current_time - item.timestamp < decay_seconds
        ]
    
    def get_recent_context(self, max_messages: int = 6) -> str:
        """최근 컨텍스트 반환 (메시지 + 메모리)"""
        # 최근 대화
        conversation = self.get_conversation_history(max_messages)
        
        # 중요 메모리
        memory_context = self.get_memory_context(3)
        
        context_parts = []
        if conversation:
            context_parts.append(f"최근 대화:\n{conversation}")
        if memory_context:
            context_parts.append(f"\n{memory_context}")
        
        return "\n".join(context_parts)
    
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
        # 메모리는 유지 (사용자 경험을 위해)
    
    def clear_memory(self):
        """메모리 완전 초기화"""
        self.short_term_memory.clear()
        self.long_term_memory.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """상태를 딕셔너리로 변환 (RAG 호환성)"""
        return {
            "messages": self.messages,
            "k": self.k,
            "last_route": self.last_route,
            "citations": self.citations,
            "error": self.error,
            "short_term_memory": [item.to_dict() for item in self.short_term_memory],
            "long_term_memory": [item.to_dict() for item in self.long_term_memory],
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """딕셔너리에서 상태 복원"""
        self.messages = data.get("messages", [])
        self.k = data.get("k", 4)
        self.last_route = data.get("last_route")
        self.citations = data.get("citations", [])
        self.error = data.get("error")
        
        # 메모리 복원
        short_term_data = data.get("short_term_memory", [])
        self.short_term_memory = [MemoryItem.from_dict(item) for item in short_term_data]
        
        long_term_data = data.get("long_term_memory", [])
        self.long_term_memory = [MemoryItem.from_dict(item) for item in long_term_data]


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
