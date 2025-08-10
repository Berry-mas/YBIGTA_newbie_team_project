from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import os
import json
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from st_app.rag.embedder import TfidfEmbedder, SentenceTransformerEmbedder


@dataclass
class RetrievedDocument:
    page_content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None


class TfIdfRetriever:
    def __init__(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        self._embedder = TfidfEmbedder(max_features=5000)
        self._matrix = self._embedder.fit_transform(texts)
        self._texts = texts
        self._metas = metadatas

    def get_relevant_documents(self, query: str) -> List[RetrievedDocument]:
        if not query:
            return []
        qv = self._embedder.transform([query])
        sims = cosine_similarity(qv, self._matrix)[0]
        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
        docs: List[RetrievedDocument] = []
        for idx, score in ranked:
            docs.append(
                RetrievedDocument(
                    page_content=self._texts[idx],
                    metadata={**self._metas[idx], "score": float(score)},
                    score=float(score),
                )
            )
        return docs


def _load_review_texts(base_dir: str) -> List[RetrievedDocument]:
    csv_candidates = [
        os.path.join(base_dir, "preprocessed_reviews_yes24.csv"),
        os.path.join(base_dir, "preprocessed_reviews_kyobo.csv"),
        os.path.join(base_dir, "preprocessed_reviews_aladin.csv"),
    ]
    docs: List[RetrievedDocument] = []
    for path in csv_candidates:
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
            # Prefer cleaned_text, fallback to text
            text_col = "cleaned_text" if "cleaned_text" in df.columns else "text"
            if text_col not in df.columns:
                continue
            for i, row in df.iterrows():
                text = str(row[text_col]) if pd.notna(row[text_col]) else ""
                if not text:
                    continue
                meta = {
                    "source": os.path.basename(path),
                    "row_index": int(i),
                }
                if "date" in df.columns and pd.notna(row.get("date")):
                    meta["date"] = str(row["date"])  # type: ignore[index]
                if "score" in df.columns and pd.notna(row.get("score")):
                    meta["rating"] = float(row["score"])  # type: ignore[index]
                docs.append(RetrievedDocument(page_content=text, metadata=meta))
        except Exception:
            continue
    return docs


_CACHED: Optional[TfIdfRetriever] = None
_CACHED_FAISS: Optional[Any] = None  # lazy type for faiss retriever


def get_retriever() -> TfIdfRetriever:
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
    # If running from repo layout, database is at project root / database
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "database"))
    docs = _load_review_texts(base_dir)
    texts = [d.page_content for d in docs]
    metas = [d.metadata for d in docs]
    _CACHED = TfIdfRetriever(texts, metas)
    return _CACHED


class FaissRetriever:
    """FAISS 기반 retriever (문장 임베딩)."""

    def __init__(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        index_dir: Optional[str] = None,
    ):
        try:
            import faiss  # type: ignore
            import numpy as np
        except Exception as e:  # pragma: no cover
            raise RuntimeError("faiss 라이브러리가 설치되어 있지 않습니다.") from e
        self._faiss = faiss
        self._np = np
        self._texts = texts
        self._metas = metadatas
        self._embedder = SentenceTransformerEmbedder()
        self._dim = self._embedder.dimension

        vecs = self._embedder.encode(texts)
        self._index_dir = index_dir
        index_path = os.path.join(index_dir, "index.faiss") if index_dir else None
        meta_path = os.path.join(index_dir, "meta.json") if index_dir else None

        if index_path and os.path.exists(index_path):
            self._index = faiss.read_index(index_path)
        else:
            self._index = faiss.IndexFlatIP(self._dim)
            # 내적 기반 유사도, normalize로 코사인과 유사하게 동작
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8
            vecs_norm = vecs / norms
            self._index.add(vecs_norm)
            # 새로 만든 경우 저장
            if index_path:
                try:
                    os.makedirs(index_dir, exist_ok=True)
                    faiss.write_index(self._index, index_path)
                    # 메타 저장
                    meta = {
                        "num_texts": len(texts),
                        "dim": int(self._dim),
                        "model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
                    }
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False)
                except Exception:
                    pass

        self._vecs_norm = vecs / (self._np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8)

    def get_relevant_documents(self, query: str) -> List[RetrievedDocument]:
        if not query:
            return []
        qv = self._embedder.encode([query])
        qv = qv / (self._np.linalg.norm(qv, axis=1, keepdims=True) + 1e-8)
        scores, idxs = self._index.search(qv, k=min(50, len(self._texts)))
        idxs = idxs.flatten()
        scores = scores.flatten()
        docs: List[RetrievedDocument] = []
        for i, s in zip(idxs, scores):
            if i < 0:
                continue
            docs.append(
                RetrievedDocument(
                    page_content=self._texts[i],
                    metadata={**self._metas[i], "score": float(s)},
                    score=float(s),
                )
            )
        return docs


def get_faiss_retriever() -> Any:
    global _CACHED_FAISS
    if _CACHED_FAISS is not None:
        return _CACHED_FAISS
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",  "database"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
    docs = _load_review_texts(base_dir)
    texts = [d.page_content for d in docs]
    metas = [d.metadata for d in docs]
    index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "faiss_index"))
    os.makedirs(index_dir, exist_ok=True)
    _CACHED_FAISS = FaissRetriever(texts, metas, index_dir=index_dir)
    return _CACHED_FAISS


