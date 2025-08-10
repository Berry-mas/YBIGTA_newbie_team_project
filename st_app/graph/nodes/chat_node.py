"""
Chat Node - 기본 대화를 수행하는 LLM
"""
import json
from typing import Dict, Any, List
from st_app.utils.state import ChatState

SYSTEM_PROMPT = """
당신은 한강 작가의 소설 '소년이 온다'에 대한 전문 리뷰 분석 비서입니다.
yes24, 알라딘, 교보문고의 실제 독자 리뷰 데이터를 바탕으로 답변합니다.
모르면 단정하지 말고, 필요한 경우 명확화 질문을 1개 이내로 하세요.
마지막 줄에 반드시 JSON 한 줄을 출력하세요.
스키마: {"intent":"chat|subject_info|review","confidence":0~1,"reason":"짧은 한국어 근거"}

intent 정의:
- subject_info: '소년이 온다' 기본정보/작가정보/줄거리/출간정보/장르/수상내역 등
- review: '소년이 온다' 리뷰/후기/평가/평점/독자반응/추천여부/서점별 평가 등  
- chat: 그 외 일반 대화/인사/잡담

출력 형식:
1) 사용자 질문에 대한 답변 (2~4문장)
2) 마지막 줄에 의도 JSON 한 줄
"""


def _build_messages(state: ChatState, user_text: str) -> List[str]:
    """대화 히스토리를 메시지 형태로 구성"""
    msgs = [SYSTEM_PROMPT]
    for msg in state.messages[-10:]:  # 최근 10개 메시지만
        prefix = "User: " if msg["role"] == "user" else "Assistant: "
        msgs.append(prefix + msg["content"])
    msgs.append("User: " + user_text)
    return msgs


def _call_llm_stub(messages: List[str]) -> str:
    """임시 더미 LLM: 내일 실제 API로 교체 예정(Upstage/OpenAI).
    '소년이 온다' 전용 응답. 마지막 줄에 JSON을 반드시 포함해 반환한다."""
    user = messages[-1].lower()
    
    # '소년이 온다' 특화 키워드 분류
    if any(k in user for k in ["줄거리", "저자", "한강", "작가", "출간", "정보", "장르", "🎨", "🎭", "소개", "내용", "수상", "노벨문학상"]):
        j = {"intent": "subject_info", "confidence": 0.85, "reason": "소년이 온다 기본정보 질의"}
        body = "'소년이 온다'는 한강 작가의 2014년 작품으로, 5.18 광주민주화운동을 다룬 소설입니다. 노벨문학상 수상작가의 대표작 중 하나죠."
    elif any(k in user for k in ["리뷰", "후기", "평가", "평점", "반응", "📖", "추천", "감상", "의견", "yes24", "알라딘", "교보"]):
        j = {"intent": "review", "confidence": 0.82, "reason": "소년이 온다 리뷰/평가 질의"}
        body = "'소년이 온다'는 yes24, 알라딘, 교보문고에서 모두 높은 평점을 받고 있습니다. 독자들의 생생한 리뷰를 분석해 드릴게요."
    else:
        j = {"intent": "chat", "confidence": 0.75, "reason": "일반 대화"}
        body = "네, '소년이 온다'에 대해 궁금한 것이 있으시면 언제든 말씀해주세요!"
    
    return f"{body}\n{json.dumps(j, ensure_ascii=False)}"


class ChatNode:
    """기본 대화를 처리하는 노드"""
    name = "chat"
    
    def __init__(self, api_client=None):
        """
        Args:
            api_client: LLM API 클라이언트 (Upstage API 등)
        """
        self.api_client = api_client
        
    def analyze_intent(self, user_message: str, conversation_history: str = "") -> Dict[str, Any]:
        """사용자 메시지에서 의도를 분석"""
        user_message_lower = user_message.lower()
        
        # 키워드 기반 의도 분석
        subject_keywords = ["🎨", "🎭", "책", "작품", "작가", "정보", "소개", "줄거리", "내용"]
        review_keywords = ["📖", "리뷰", "평가", "평점", "후기", "의견", "감상"]
        
        # Subject Info Node 키워드 검사
        subject_score = 0
        for keyword in subject_keywords:
            if keyword in user_message:
                subject_score += 1
        
        # Review Node 키워드 검사
        review_score = 0
        for keyword in review_keywords:
            if keyword in user_message:
                review_score += 1
        
        # 의도 결정
        if subject_score > 0:
            return {
                "intent": "subject_info",
                "confidence": min(0.9, 0.5 + subject_score * 0.2),
                "reason": f"책/작품 정보 관련 키워드 감지 ({subject_score}개)"
            }
        elif review_score > 0:
            return {
                "intent": "review",
                "confidence": min(0.9, 0.5 + review_score * 0.2),
                "reason": f"리뷰/평가 관련 키워드 감지 ({review_score}개)"
            }
        else:
            return {
                "intent": "chat",
                "confidence": 0.8,
                "reason": "일반 대화로 판단"
            }
    
    def generate_response(self, user_message: str, conversation_history: str = "") -> str:
        """LLM을 사용하여 응답 생성"""
        if self.api_client:
            # 실제 LLM API 호출
            try:
                prompt = f"""당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
사용자와 자연스럽게 대화하세요.

대화 히스토리:
{conversation_history}

사용자: {user_message}

어시스턴트:"""
                
                response = self.api_client.chat.completions.create(
                    model="solar-1-mini-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"죄송합니다. 일시적인 오류가 발생했습니다: {str(e)}"
        else:
            # API 클라이언트가 없을 때의 기본 응답
            return self._generate_fallback_response(user_message)
    
    def _generate_fallback_response(self, user_message: str) -> str:
        """API 없이 기본 응답 생성"""
        user_message_lower = user_message.lower()
        
        if any(greeting in user_message_lower for greeting in ["안녕", "hello", "hi", "반가워"]):
            return "안녕하세요! 저는 도서 리뷰 분석 어시스턴트입니다. 무엇을 도와드릴까요?"
        
        elif any(book_word in user_message_lower for book_word in ["책", "도서", "작품"]):
            return "책에 대해서 관심이 있으시군요! 특정 책의 정보나 리뷰가 궁금하시다면 🎨나 📖 이모지와 함께 질문해보세요."
        
        elif any(review_word in user_message_lower for review_word in ["리뷰", "평가", "후기"]):
            return "리뷰에 대해 궁금하시는군요! 📖 이모지와 함께 구체적인 질문을 해주시면 더 자세한 정보를 제공해드릴 수 있습니다."
        
        elif "?" in user_message or "궁금" in user_message_lower:
            return "궁금한 것이 있으시군요! 책 정보는 🎨🎭, 리뷰 정보는 📖 이모지와 함께 질문해주시면 더 정확한 답변을 드릴 수 있습니다."
        
        else:
            return "네, 말씀하신 내용을 잘 들었습니다. 더 구체적으로 도와드릴 수 있는 것이 있다면 언제든 말씀해주세요!"
    
    def run(self, user_text: str, state: ChatState) -> Dict[str, Any]:
        """
        Chat Node 실행 - 팀원 코드 스타일을 참고하여 개선
        
        Args:
            user_text: 사용자 입력 텍스트
            state: 현재 채팅 상태
            
        Returns:
            Dict containing answer, intent, confidence, reason, updated_state
        """
        # 1. 메시지 히스토리 구성
        messages = _build_messages(state, user_text)
        
        # 2. LLM 호출 (실제 API 또는 더미)
        raw = self._call_real_llm(messages).strip() if self.api_client else _call_llm_stub(messages)
        
        # 3. 응답과 의도 JSON 분리
        *body, last = raw.splitlines()
        answer = "\n".join(body).strip() or "(응답 없음)"
        intent_json = {"intent": "chat", "confidence": 0.0, "reason": "parse_failed"}
        
        try:
            intent_json = json.loads(last)
        except Exception:
            # JSON 파싱 실패 시 키워드 기반 폴백
            intent_json = self.analyze_intent(user_text)
        
        # 4. 상태 업데이트
        state.add_message("user", user_text)
        state.add_message("assistant", answer)
        state.add_intent(
            intent_json.get("intent", "chat"),
            intent_json.get("confidence", 0.0),
            intent_json.get("reason", "")
        )
        state.current_node = "chat"
        
        # 5. 결과 반환 (팀원 스펙에 맞춤)
        return {
            "answer": answer,
            "intent": intent_json.get("intent", "chat"),
            "confidence": float(intent_json.get("confidence", 0.0)),
            "reason": intent_json.get("reason", ""),
            "updated_state": state,
            # 기존 호환성을 위한 추가 필드
            "response": f"{answer}\n{json.dumps(intent_json, ensure_ascii=False)}",
            "next_node": intent_json.get("intent", "chat")
        }
