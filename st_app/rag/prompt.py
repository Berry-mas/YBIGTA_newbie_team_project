from __future__ import annotations


def build_review_prompt(question: str, context: str) -> str:
    return (
        "당신은 도서 리뷰를 기반으로 사실적인 요약과 근거 인용을 제공하는 어시스턴트입니다.\n"
        "아래 CONTEXT에서만 근거를 취해 답하세요.\n"
        "- 근거가 없으면 모른다고 답하세요.\n"
        "- 핵심 요점 위주로 5문장 이내로 요약하세요.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "마지막 줄에 '출처: [DOC i, ...]' 형식으로 문서 번호를 기재하세요."
    )


