from __future__ import annotations

import os
from typing import Any, Optional


# 1) 우선 LangChain-Upstage 사용 시도
try:  # pragma: no cover
    from langchain_upstage import ChatUpstage  # type: ignore
    from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
    _HAS_LANGCHAIN_UPSTAGE = True
except Exception:  # pragma: no cover
    _HAS_LANGCHAIN_UPSTAGE = False


# 2) 백업: HTTP 직접 호출 클라이언트
try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class _LangChainUpstageWrapper:
    """LangChain ChatUpstage를 감싼 래퍼. 문자열 prompt를 받아 invoke.

    모든 노드에서는 `.invoke(str)` 형태를 유지하고, 내부에서 LC 메시지로 변환합니다.
    """

    def __init__(self, api_key: str, model: str, temperature: float) -> None:
        if not _HAS_LANGCHAIN_UPSTAGE:
            raise RuntimeError("langchain_upstage가 설치되어 있지 않습니다.")
        self._chat = ChatUpstage(api_key=api_key, model=model, temperature=temperature)

    def invoke(self, prompt: str) -> Any:
        msgs = [
            SystemMessage(content="You are a helpful and concise assistant."),
            HumanMessage(content=prompt),
        ]
        res = self._chat.invoke(msgs)
        # LangChain AIMessage는 content 속성을 가짐
        return type("LLMResult", (), {"content": getattr(res, "content", str(res))})()


class _HttpUpstageClient:
    """HTTP 기반 백업 클라이언트 (LangChain 미사용 시)."""

    def __init__(self, api_key: str, model: str, base_url: str, temperature: float) -> None:
        if requests is None:
            raise RuntimeError("requests가 설치되어 있지 않습니다.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def invoke(self, prompt: str) -> Any:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
        }
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return type("LLMResult", (), {"content": content})()


_CACHED: Optional[Any] = None


def get_llm() -> Any:
    """LangChain 기반 ChatUpstage를 우선 사용. 불가 시 HTTP 백업 사용.

    - 환경변수: UPSTAGE_API_KEY (필수), UPSTAGE_MODEL, UPSTAGE_TEMPERATURE, UPSTAGE_BASE_URL
    """
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY is not set in environment")
    # HTTP 헤더 제한(ISO-8859-1)에 따라 비ASCII 키는 허용하지 않음
    try:
        api_key.encode("ascii")
    except Exception as e:
        raise RuntimeError("UPSTAGE_API_KEY에 비ASCII 문자가 포함되어 있습니다. 실제 API 키를 설정하세요.") from e

    model = os.getenv("UPSTAGE_MODEL", "solar-1-mini-chat")
    temp_env = os.getenv("UPSTAGE_TEMPERATURE")
    try:
        temperature = float(temp_env) if temp_env else 0.2
    except ValueError:
        temperature = 0.2

    if _HAS_LANGCHAIN_UPSTAGE:
        _CACHED = _LangChainUpstageWrapper(api_key=api_key, model=model, temperature=temperature)
        return _CACHED

    base_url = os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai")
    _CACHED = _HttpUpstageClient(api_key=api_key, model=model, base_url=base_url, temperature=temperature)
    return _CACHED


