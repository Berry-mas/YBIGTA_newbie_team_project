from __future__ import annotations

import os
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbedder:
    def __init__(self, max_features: int = 5000) -> None:
        self.vectorizer = TfidfVectorizer(max_features=max_features)

    def fit_transform(self, texts: List[str]):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts: List[str]):
        return self.vectorizer.transform(texts)


class SentenceTransformerEmbedder:
    """Sentence-Transformers 임베딩 래퍼 (FAISS용).

    기본 모델: paraphrase-multilingual-MiniLM-L12-v2 (한국어 지원)
    환경변수 EMBEDDING_MODEL 로 교체 가능.
    """

    def __init__(self, model_name: str | None = None) -> None:
        name = model_name or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers가 설치되어 있지 않습니다. requirements를 확인하세요."
            ) from e
        self._model = SentenceTransformer(name)

    @property
    def dimension(self) -> int:
        # 일부 모델은 get_sentence_embedding_dimension 제공
        dim = getattr(self._model, "get_sentence_embedding_dimension", None)
        if callable(dim):
            return int(dim())
        # fallback: 한 문장을 encode하여 차원 확인
        import numpy as np

        v = self._model.encode(["dim"])
        return int(np.asarray(v).shape[1])

    def encode(self, texts: List[str]):
        import numpy as np

        vecs = self._model.encode(texts, normalize_embeddings=False)
        return np.asarray(vecs, dtype="float32")


