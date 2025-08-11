"""
Streamlit 메인 애플리케이션
Chat Node와 RAG 기능을 모두 지원하는 통합 버전
"""
from __future__ import annotations

import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from st_app.utils.state import ChatState
from st_app.graph.nodes.chat_node import chat_node

# .env 파일 로드
load_dotenv()

# RAG 관련 import (선택적)
try:
    from st_app.graph.router import run_graph
    from st_app.graph.router import get_graph_app
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# feature/subject-node 브랜치 호환성
try:
    from st_app.graph.nodes.subject_info_node import subject_info_node
    SUBJECT_NODE_AVAILABLE = True
except ImportError:
    SUBJECT_NODE_AVAILABLE = False


def init_api_client():
    """API 클라이언트 초기화"""
    try:
        # secrets.toml 파일이 있으면 사용
        api_key = st.secrets.get("UPSTAGE_API_KEY", None)
    except:
        # secrets.toml 파일이 없으면 환경변수 또는 None
        api_key = os.getenv("UPSTAGE_API_KEY")
    
    if api_key:
        return OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1/solar"
        )
    return None


def init_session_state():
    """Streamlit 세션 상태 초기화"""
    if "chat_state" not in st.session_state:
        st.session_state.chat_state = ChatState()
    if "api_client" not in st.session_state:
        st.session_state.api_client = init_api_client()
    # chat_node는 함수이므로 session_state에 저장할 필요 없음
    if "use_rag" not in st.session_state:
        st.session_state.use_rag = False
    if "use_simple_mode" not in st.session_state:
        st.session_state.use_simple_mode = False


def display_message(role: str, content: str):
    """메시지 표시"""
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            # 의도 JSON이 포함된 경우 분리해서 표시
            if content.strip().endswith('}'):
                try:
                    # 마지막 줄이 JSON인지 확인
                    lines = content.strip().split('\n')
                    potential_json = lines[-1]
                    if potential_json.startswith('{') and potential_json.endswith('}'):
                        # JSON 부분과 응답 부분 분리
                        response_text = '\n'.join(lines[:-1]).strip()
                        intent_json = json.loads(potential_json)
                        
                        # 응답 텍스트 표시
                        if response_text:
                            st.write(response_text)
                        
                        # 의도 정보를 접을 수 있는 형태로 표시
                        with st.expander("🎯 의도 분석 결과", expanded=False):
                            st.json(intent_json)
                    else:
                        st.write(content)
                except (json.JSONDecodeError, IndexError):
                    st.write(content)
            else:
                st.write(content)


def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="도서 리뷰 분석 챗봇",
        page_icon="📚",
        layout="wide"
    )
    
    # 초기화
    init_session_state()
    
    # 사이드바 설정
    with st.sidebar:
        st.title("🤖 챗봇 설정")
        
        # API 키 입력 (로컬 개발용 - 주석처리)
        # api_key_input = st.text_input(
        #     "Upstage API Key", 
        #     type="password",
        #     placeholder="API 키를 입력하세요 (선택사항)"
        # )
        
        # if api_key_input and api_key_input != st.session_state.get("current_api_key"):
        #     st.session_state.current_api_key = api_key_input
        #     st.session_state.api_client = OpenAI(
        #         api_key=api_key_input,
        #         base_url="https://api.upstage.ai/v1/solar"
        #     )
        #     st.success("API 키가 설정되었습니다!")
        
        # API 키 상태 표시 (배포 시 사용)
        if st.session_state.api_client:
            st.success("✅ API 키가 설정되어 있습니다!")
        else:
            st.error("❌ API 키가 설정되지 않았습니다. 환경변수를 확인해주세요.")
        
        # 모드 선택
        st.subheader("🔧 모드 선택")
        
        # 간단 모드 선택
        use_simple_mode = st.checkbox("간단 모드 사용", value=st.session_state.use_simple_mode)
        if use_simple_mode != st.session_state.use_simple_mode:
            st.session_state.use_simple_mode = use_simple_mode
            st.rerun()
        
        if not use_simple_mode:
            # 고급 모드 (자동 라우팅)
            st.info("🚀 고급 모드 - 질문에 따라 자동으로 노드가 변경됩니다!")
            st.write("**사용 가능한 노드:**")
            st.write("- 💬 Chat Node: 일반 대화")
            st.write("- 📚 Subject Info: 책/작가 정보")
            st.write("- 🔍 RAG Review: 리뷰 분석")
        
        # 상태 정보 표시
        st.subheader("📊 현재 상태")
        if use_simple_mode:
            st.write("**모드**: 간단 모드")
        else:
            st.write("**모드**: 고급 모드 (자동 라우팅)")
        
        if not use_simple_mode:
            # 현재 노드 표시 (last_route 정보 활용)
            current_node = st.session_state.chat_state.last_route or "chat"
            node_display_names = {
                "chat": "💬 Chat Node",
                "subject_info": "📚 Subject Info", 
                "rag_review": "🔍 RAG Review"
            }
            st.write(f"**현재 노드**: {node_display_names.get(current_node, current_node)}")
            st.write(f"**메시지 수**: {len(st.session_state.chat_state.messages)}")
        
        # 대화 초기화 버튼
        if st.button("🔄 대화 초기화"):
            if use_simple_mode:
                st.session_state.messages = []
            else:
                st.session_state.chat_state.reset()
            st.rerun()
        
        # 메모리 관리 (고급 모드에서만)
        if not use_simple_mode:
            st.subheader("🧠 메모리 관리")
            
            # 메모리 정보 표시
            if hasattr(st.session_state.chat_state, 'short_term_memory'):
                st.write(f"**단기 메모리**: {len(st.session_state.chat_state.short_term_memory)}개")
                st.write(f"**장기 메모리**: {len(st.session_state.chat_state.long_term_memory)}개")
            
            # 메모리 초기화 버튼
            if st.button("🧹 메모리 초기화"):
                if hasattr(st.session_state.chat_state, 'clear_memory'):
                    st.session_state.chat_state.clear_memory()
                st.success("메모리가 초기화되었습니다!")
                st.rerun()
            
            # 메모리 내용 보기
            if hasattr(st.session_state.chat_state, 'long_term_memory') and st.session_state.chat_state.long_term_memory:
                with st.expander("📚 장기 메모리 내용", expanded=False):
                    for i, memory in enumerate(st.session_state.chat_state.long_term_memory[:5], 1):
                        st.write(f"{i}. {memory.content} (중요도: {memory.importance:.2f})")
        
        # 사용법 안내
        st.subheader("💡 사용법")
        if use_simple_mode:
            st.markdown("""
            **간단 모드:**
            - 기본적인 책 정보 질의 응답
            - 빠르고 간단한 인터페이스
            
            **예시 질문:**
            - "소년이 온다 정보 알려줘"
            - "작가 정보는?"
            """)
        else:
            st.markdown("""
            **고급 모드 (자동 라우팅):**
            - 질문 의도에 따라 자동으로 적절한 노드 선택
            - 일반 대화, 책 정보, 리뷰 분석 모두 지원
            
            **예시 질문:**
            - "안녕하세요" → Chat Node
            - "한강 작가 정보 알려줘" → Subject Info
            - "소년이 온다 평점은?" → RAG Review
            - "리뷰에서 자주 언급되는 내용은?" → RAG Review
            """)
    
    # 메인 화면
    st.title("📖 '소년이 온다' 리뷰 분석 챗봇")
    st.markdown("**한강 작가의 '소년이 온다'**에 대한 yes24, 알라딘, 교보문고 리뷰 데이터를 분석해드립니다!")
    
    # 모드 표시
    if st.session_state.use_simple_mode:
        st.success("🚀 간단 모드로 실행 중")
    else:
        st.info("🚀 고급 모드로 실행 중 - 질문에 따라 자동으로 노드가 변경됩니다!")
    
    # 책 정보 표시
    with st.expander("📚 '소년이 온다' 기본 정보", expanded=False):
        st.markdown("""
        - **작가**: 한강 (노벨문학상 수상작가)
        - **출간**: 2014년
        - **장르**: 현대소설
        - **주제**: 5.18 광주민주화운동
        - **데이터**: yes24, 알라딘, 교보문고 리뷰/평점
        """)
    
    # 간단 모드 처리
    if st.session_state.use_simple_mode:
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
            if SUBJECT_NODE_AVAILABLE:
                state = {"user_msg": user_msg, "subject_name": None, "last_answer": None}
                subject_info_node(state)
                reply = state["last_answer"]
            else:
                reply = "죄송합니다. 간단 모드에서 노드를 찾을 수 없습니다."

            # 3) 어시스턴트 표시 + 히스토리 추가
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
    
    else:
        # 기존 복잡한 모드 처리
        # 현재 노드 표시
        current_node = st.session_state.chat_state.last_route or "chat"
        node_display_names = {
            "chat": "💬 Chat Node",
            "subject_info": "📚 Subject Info", 
            "rag_review": "🔍 RAG Review"
        }
        st.info(f"🎯 현재 노드: **{node_display_names.get(current_node, current_node)}**")
        
        # 채팅 히스토리 표시
        for message in st.session_state.chat_state.messages:
            display_message(message["role"], message["content"])
        
        # 사용자 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            # 사용자 메시지 추가 및 표시
            st.session_state.chat_state.add_message("user", prompt)
            display_message("user", prompt)
            
            # 고급 모드 실행 (자동 라우팅)
            with st.spinner("응답을 생성하고 있습니다..."):
                try:
                    # 자동 라우팅 실행
                    state = {
                        "messages": st.session_state.chat_state.messages, 
                        "k": 4  # 기본 Top-k 값
                    }
                    
                    try:
                        app = get_graph_app()
                        out = app.invoke(state)
                    except Exception:
                        out = run_graph(state)
                    
                    # 결과 처리
                    messages = out.get("messages", [])
                    if messages and len(messages) > len(st.session_state.chat_state.messages):
                        # 새로운 어시스턴트 메시지가 있으면 추가
                        new_message = messages[-1]
                        if new_message["role"] == "assistant":
                            st.session_state.chat_state.add_message("assistant", new_message["content"])
                            display_message("assistant", new_message["content"])
                            
                            # citations 표시 (RAG 결과인 경우)
                            citations = out.get("citations", [])
                            if citations:
                                with st.expander("📚 참고 자료", expanded=False):
                                    for i, citation in enumerate(citations, 1):
                                        st.write(f"{i}. {citation.get('content', '')[:100]}...")
                    
                    # 세션 메시지 업데이트
                    st.session_state.chat_state.messages = messages
                    
                    # last_route 업데이트 (UI 동기화를 위해)
                    if out.get("last_route"):
                        st.session_state.chat_state.last_route = out["last_route"]
                        print(f"🔍 UI 업데이트 - last_route: {out['last_route']}")
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
                    # 기본 응답 추가
                    fallback_response = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
                    st.session_state.chat_state.add_message("assistant", fallback_response)
                    display_message("assistant", fallback_response)
    
    # 하단 정보
    st.markdown("---")
    if st.session_state.use_simple_mode:
        st.markdown("💻 **개발 정보**: 간단 모드 - 기본 책 정보 질의")
    else:
        st.markdown("💻 **개발 정보**: 고급 모드 - 자동 라우팅 (Chat/Subject/RAG)")
        # 현재 노드 정보 표시
        current_node = st.session_state.chat_state.last_route or "chat"
        node_display_names = {
            "chat": "💬 Chat Node",
            "subject_info": "📚 Subject Info", 
            "rag_review": "🔍 RAG Review"
        }
        st.markdown(f"🎯 **현재 노드**: {node_display_names.get(current_node, current_node)}")
    st.markdown("📊 **데이터 출처**: yes24, 알라딘, 교보문고 리뷰 데이터")


if __name__ == "__main__":
    main()
