from __future__ import annotations

def build_review_prompt(question: str, context: str) -> str:
    return (
        "당신은 도서 리뷰를 기반으로 질문에 대해 풍부하고 사실적인 답변을 제공하는 어시스턴트입니다.\n"
        "아래 CONTEXT에서만 근거를 취해 답하세요.\n"
        "- CONTEXT에 없는 내용은 절대 추측하지 말고 '리뷰에서 해당 정보를 찾을 수 없습니다'라고 답하세요.\n"
        "- 가능한 한 구체적이고 세부적으로 설명하세요.\n"
        "- 리뷰의 뉘앙스, 감정, 사례 등을 포함해도 됩니다.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n"
    )