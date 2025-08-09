# streamlit_app.py (핵심 부분만)
import os
from dotenv import load_dotenv
import streamlit as st
from st_app.utils.state import ChatState, new_state, push_user, push_assistant


st.set_page_config(page_title="Subject Info Bot", page_icon="📘")

load_dotenv()

# secrets → env 반영 (Cloud)
try:
    if "UPSTAGE_API_KEY" in st.secrets:
        os.environ["UPSTAGE_API_KEY"] = st.secrets["UPSTAGE_API_KEY"]
except Exception:
    pass

from st_app.graph.nodes.subject_info_node import subject_info_node
# (필요 시) 키 체크
# if not os.getenv("UPSTAGE_API_KEY"):
#     st.warning("UPSTAGE_API_KEY가 없어 LLM 호출이 비활성화됐어요.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 과거 대화 렌더링
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_msg = st.chat_input("책 정보 물어봐!")
if user_msg:
    # 1) 즉시 화면에 사용자 메시지 표시 + 히스토리에 추가
    with st.chat_message("user"):
        st.markdown(user_msg)
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # 2) 노드 실행
    state = {"user_msg": user_msg, "subject_name": None, "last_answer": None}
    subject_info_node(state)
    reply = state["last_answer"]

    # 3) 어시스턴트 표시 + 히스토리 추가
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
