"""
Streamlit 메인 애플리케이션
Chat Node만 동작하는 기본 버전
"""
import streamlit as st
import json
import os
from openai import OpenAI
from st_app.utils.state import ChatState
from st_app.graph.nodes.chat_node import ChatNode


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
    if "chat_node" not in st.session_state:
        st.session_state.chat_node = ChatNode(st.session_state.api_client)


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
        
        # API 키 입력
        api_key_input = st.text_input(
            "Upstage API Key", 
            type="password",
            placeholder="API 키를 입력하세요 (선택사항)"
        )
        
        if api_key_input and api_key_input != st.session_state.get("current_api_key"):
            st.session_state.current_api_key = api_key_input
            st.session_state.api_client = OpenAI(
                api_key=api_key_input,
                base_url="https://api.upstage.ai/v1/solar"
            )
            st.session_state.chat_node = ChatNode(st.session_state.api_client)
            st.success("API 키가 설정되었습니다!")
        
        # 상태 정보 표시
        st.subheader("📊 현재 상태")
        st.write(f"**현재 노드**: {st.session_state.chat_state.current_node}")
        st.write(f"**메시지 수**: {len(st.session_state.chat_state.messages)}")
        
        # 대화 초기화 버튼
        if st.button("🔄 대화 초기화"):
            st.session_state.chat_state.reset()
            st.rerun()
        
        # 사용법 안내
        st.subheader("💡 사용법")
        st.markdown("""
        **키워드 안내:**
        - 🎨🎭 + 질문: '소년이 온다' 기본정보
        - 📖 + 질문: yes24/알라딘/교보 리뷰분석
        - 일반 질문: 기본 대화
        
        **예시 질문:**
        - "🎨 작가 정보 알려줘"
        - "📖 평점이 어때?"
        - "교보문고 리뷰는?"
        """)
    
    # 메인 화면
    st.title("📖 '소년이 온다' 리뷰 분석 챗봇")
    st.markdown("**한강 작가의 '소년이 온다'**에 대한 yes24, 알라딘, 교보문고 리뷰 데이터를 분석해드립니다!")
    
    # 책 정보 표시
    with st.expander("📚 '소년이 온다' 기본 정보", expanded=False):
        st.markdown("""
        - **작가**: 한강 (노벨문학상 수상작가)
        - **출간**: 2014년
        - **장르**: 현대소설
        - **주제**: 5.18 광주민주화운동
        - **데이터**: yes24, 알라딘, 교보문고 리뷰/평점
        """)
    
    # 현재 노드 표시
    st.info(f"🎯 현재 노드: **{st.session_state.chat_state.current_node.upper()}**")
    
    # 채팅 히스토리 표시
    for message in st.session_state.chat_state.messages:
        display_message(message["role"], message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가 및 표시
        st.session_state.chat_state.add_message("user", prompt)
        display_message("user", prompt)
        
        # Chat Node 실행 (개선된 인터페이스)
        with st.spinner("응답을 생성하고 있습니다..."):
            try:
                # 팀원 스타일에 맞춘 호출 방식
                result = st.session_state.chat_node.run(prompt, st.session_state.chat_state)
                
                # 어시스턴트 응답 표시
                display_message("assistant", result["response"])
                
                # 다음 노드 정보 표시 (개발용)
                if result["intent"] != "chat":
                    st.warning(f"🔄 다음에 {result['intent']} 노드로 라우팅될 예정입니다. (신뢰도: {result['confidence']:.2f})")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
                # 기본 응답 추가
                fallback_response = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
                st.session_state.chat_state.add_message("assistant", fallback_response)
                display_message("assistant", fallback_response)
    
    # 하단 정보
    st.markdown("---")
    st.markdown("💻 **개발 정보**: '소년이 온다' 전용 Chat Node (RAG 연결 대기중)")
    st.markdown("📊 **데이터 출처**: yes24, 알라딘, 교보문고 리뷰 데이터")


if __name__ == "__main__":
    main()
