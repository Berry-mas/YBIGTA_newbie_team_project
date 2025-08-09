# st_app/graph/nodes/subject_info_node.py
import os, json, re
from functools import lru_cache
from typing import Dict, Any, Optional, List

from langchain_upstage import ChatUpstage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── 데이터
with open("st_app/db/subject_information/subjects.json", encoding="utf-8") as f:
    SUBJECT_DB: Dict[str, Any] = json.load(f)

SLOTS = ["title","author","publisher","published_date","summary","pages","genres","awards","language"]

# ── LLM
@lru_cache(maxsize=1)
def _get_llm():
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY 없음")
    return ChatUpstage(api_key=api_key, model="solar-1-mini-chat", temperature=0)

# ── 프롬프트 (하나의 체인에서 의도판단+사실판단+출력포맷까지)
SYS = (
"너는 책 정보 전용 어시스턴트다. 아래 JSON만 근거로 답하라. 추측 금지.\n"
"1) 질문이 예/아니오형이면 반드시 다음 형식 중 하나로 시작하라:\n"
"   - '네, ...입니다.'  (주장이 JSON과 일치할 때)\n"
"   - '아니요, ...입니다.' (주장이 JSON과 다를 때)\n"
"   이어지는 설명도 JSON 근거로만, 질문한 항목(필드)만 간단히 말하라.\n"
"2) 예/아니오형이 아니면, 질문에서 필요한 슬롯만 간결히 한 문단으로 답하라.\n"
"3) 절대 JSON에 없는 정보/수상/해설을 덧붙이지 말라. 불확실하면 생략.\n"
"4) 숫자/날짜/쪽수/장르/수상/언어 등은 JSON 값과 정확히 일치시켜 서술하라."
)

USR = (
"질문: {question}\n\n"
"책 정보(JSON):\n{subject_json}\n\n"
"도움말:\n- 가능한 키: " + ", ".join(SLOTS) + "\n"
"- 질문이 예/아니오인지 스스로 판단하라.\n"
"- 예/아니오라면 위 규칙에 맞는 한두 문장만 출력.\n"
"- 일반 질문이면 관련 슬롯만 간결히 요약.\n"
"- 출력은 한국어로만."
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYS),
    ("human", USR)
])

chain = prompt | _get_llm() | StrOutputParser()

# ── 유틸
def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()

def _find_subject(user_msg: str, hint: Optional[str] = None) -> Optional[str]:
    q = _norm(hint or user_msg)
    for name, info in SUBJECT_DB.items():
        if _norm(name) in q:
            return name
        for alias in info.get("aliases", []):
            if _norm(alias) in q:
                return name
    if len(SUBJECT_DB) == 1:
        return list(SUBJECT_DB.keys())[0]
    return None

# ── 메인 노드
def subject_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("user_msg", "") or ""
    name = _find_subject(question, state.get("subject_name"))
    if not name:
        state["last_answer"] = "어떤 작품인지 알려줘!"
        return state

    info = SUBJECT_DB[name]
    subject_json = json.dumps(info, ensure_ascii=False)

    try:
        reply = (chain.invoke({"question": question, "subject_json": subject_json}) or "").strip()
        state["last_answer"] = reply if reply else "정보를 찾을 수 없습니다."
    except Exception:
        # LLM 오류 시 최소 Fallback
        title = info.get("title", name)
        state["last_answer"] = f"『{title}』에 대해 더 구체적으로 물어봐!"
    return state
