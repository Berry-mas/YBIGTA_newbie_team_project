from __future__ import annotations

import os
from typing import List
import requests
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbedder:
    def __init__(self, max_features: int = 5000) -> None:
        self.vectorizer = TfidfVectorizer(max_features=max_features)

    def fit_transform(self, texts: List[str]):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts: List[str]):
        return self.vectorizer.transform(texts)


class UpstageEmbedder:
    """Upstage 임베딩 API 래퍼"""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise RuntimeError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
        
        self.model = model_name or os.getenv("EMBEDDING_MODEL", "solar-1-mini-embedding")
        self.base_url = "https://api.upstage.ai/v1"
        self._dimension = None

    @property
    def dimension(self) -> int:
        """임베딩 차원 반환"""
        if self._dimension is None:
            # 테스트 임베딩으로 차원 확인
            test_embedding = self.encode(["test"])
            self._dimension = test_embedding.shape[1]
        return self._dimension

    def encode(self, texts: List[str]) -> np.ndarray:
        """텍스트들을 임베딩으로 변환"""
        if not texts:
            return np.array([])
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        embeddings = []
        # 배치 크기 제한 (API 제한 고려)
        batch_size = 10
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            payload = {
                "model": self.model,
                "input": batch_texts
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                batch_embeddings = [item["embedding"] for item in data["data"]]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"임베딩 API 호출 실패: {e}")
                print(f"URL: {url}")
                print(f"Payload: {payload}")
                # 폴백: 0으로 채운 임베딩 반환
                fallback_embedding = [0.0] * 384  # 기본 차원
                embeddings.extend([fallback_embedding] * len(batch_texts))
        
        return np.array(embeddings, dtype="float32")


class SentenceTransformerEmbedder:
    """Sentence-Transformers 임베딩 래퍼 (로컬 폴백용).

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


def get_embedder(use_api: bool = True):
    """임베딩 모델 반환
    
    Args:
        use_api: True면 Upstage API 사용, False면 로컬 모델 사용
    """
    if use_api:
        try:
            return UpstageEmbedder()
        except Exception as e:
            print(f"Upstage API 임베딩 실패, 로컬 모델로 폴백: {e}")
            return SentenceTransformerEmbedder()
    else:
        return SentenceTransformerEmbedder()


