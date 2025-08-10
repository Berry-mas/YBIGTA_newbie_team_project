from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


Message = Dict[str, Any]


@dataclass
class ChatState:
    messages: List[Message] = field(default_factory=list)
    k: int = 4
    last_route: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "k": self.k,
            "last_route": self.last_route,
            "citations": self.citations,
            "error": self.error,
        }


