from __future__ import annotations

import os
import streamlit as st

from st_app.graph.router import run_graph
from st_app.graph.graph import get_graph_app


st.set_page_config(page_title="YBIGTA RAG Agent", page_icon="🤖", layout="centered")
st.title("YBIGTA RAG Agent")

if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
    st.session_state.messages = []

with st.sidebar:
    st.markdown("**Settings**")
    st.text_input("UPSTAGE_API_KEY", type="password", key="upstage_api_key")
    st.number_input("Top-k (RAG)", min_value=1, max_value=10, value=4, step=1, key="topk")
    if st.session_state.get("upstage_api_key"):
        os.environ["UPSTAGE_API_KEY"] = st.session_state["upstage_api_key"]

for m in st.session_state.messages:
    role = m.get("role")
    content = m.get("content")
    if role not in ("user", "assistant") or not isinstance(content, str):
        continue
    with st.chat_message(role):
        st.markdown(content)

prompt = st.chat_input("메시지를 입력하세요…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    state = {"messages": st.session_state.messages, "k": int(st.session_state.get("topk", 4))}
    # Try LangGraph app first; fall back to pure-router if graph import not available
    try:
        app = get_graph_app()
        out = app.invoke(state)
    except Exception:
        out = run_graph(state)
    # 세션 메시지 업데이트 후 전체 대화 재렌더 (사용자-어시스턴트 순서 보장)
    st.session_state.messages = out.get("messages", st.session_state.messages)
    st.rerun()


