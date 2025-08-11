from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from st_app.rag.embedder import TfidfEmbedder, get_embedder


class RetrievedDocument:
    """검색된 문서를 나타내는 클래스"""
    
    def __init__(self, page_content: str, metadata: Dict[str, Any], score: float):
        self.page_content = page_content
        self.metadata = metadata
        self.score = score


def _load_review_texts(base_dir: str) -> List[RetrievedDocument]:
    """리뷰 텍스트 로드"""
    docs = []
    
    # MongoDB에서 데이터 로드 시도 (배포 환경에서는 비활성화)
    # try:
    #     from database.mongodb_connection import mongo_db
    #     collections = ["yes24_processed", "aladin_processed", "kyobo_processed"]
    #     
    #     for collection_name in collections:
    #         if collection_name in mongo_db.list_collection_names():
    #             collection = mongo_db[collection_name]
    #             cursor = collection.find({}, {"text": 1, "score": 1, "date": 1, "site": 1})
    #             
    #             for doc in cursor:
    #                 text = doc.get("text", "")
    #                 if text and len(text.strip()) > 10:  # 의미있는 텍스트만
    #                     metadata = {
    #                         "source": collection_name,
    #                         "score": doc.get("score", 0),
    #                         "date": doc.get("date"),
    #                         "site": doc.get("site", collection_name.split("_")[0])
    #                     }
    #                     docs.append(RetrievedDocument(text, metadata, 0.0))
    #                     
    # except Exception as e:
    #     print(f"MongoDB 로드 실패: {e}")
    
    print("MongoDB 연결 비활성화 - CSV 파일 사용")
    
    # 로컬 파일에서 데이터 로드 시도
    if not docs:
        try:
            # CSV 파일들에서 데이터 로드
            csv_files = [
                ("preprocessed_reviews_yes24.csv", "yes24"),
                ("preprocessed_reviews_aladin.csv", "aladin"), 
                ("preprocessed_reviews_kyobo.csv", "kyobo")
            ]
            
            import pandas as pd
            for csv_file, site in csv_files:
                file_path = os.path.join(base_dir, csv_file)
                if os.path.exists(file_path):
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')
                        # 텍스트 컬럼 찾기 (다양한 컬럼명 대응)
                        text_col = None
                        for col in ['text', 'review_text', 'content', 'review']:
                            if col in df.columns:
                                text_col = col
                                break
                        
                        if text_col:
                            for _, row in df.iterrows():
                                text = str(row[text_col]).strip()
                                if text and len(text) > 10 and text != 'nan':
                                    metadata = {
                                        "source": site,
                                        "score": float(row.get('score', 0)) if 'score' in df.columns else 0,
                                        "date": str(row.get('date', '')) if 'date' in df.columns else '',
                                        "site": site
                                    }
                                    docs.append(RetrievedDocument(text, metadata, 0.0))
                    except Exception as e:
                        print(f"CSV 파일 {csv_file} 로드 실패: {e}")
                        
        except Exception as e:
            print(f"로컬 파일 로드 실패: {e}")
    
    return docs


class TfIdfRetriever:
    """TF-IDF 기반 검색기"""
    
    def __init__(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        self._embedder = TfidfEmbedder(max_features=5000)
        self._matrix = self._embedder.fit_transform(texts)
        self._texts = texts
        self._metas = metadatas

    def get_relevant_documents(self, query: str) -> List[RetrievedDocument]:
        """관련 문서 검색"""
        if not query or not self._texts:
            return []
        
        try:
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
        except Exception as e:
            print(f"TF-IDF 검색 오류: {e}")
            # 폴백: 모든 문서 반환
            docs: List[RetrievedDocument] = []
            for i, text in enumerate(self._texts):
                docs.append(
                    RetrievedDocument(
                        page_content=text,
                        metadata={**self._metas[i], "score": 0.5},
                        score=0.5,
                    )
                )
            return docs


class FaissRetriever:
    """FAISS 기반 검색기 (API 임베딩)"""

    def __init__(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        index_dir: Optional[str] = None,
        use_api: bool = True,
    ):
        try:
            import faiss  # type: ignore
            import numpy as np
        except Exception as e:
            raise RuntimeError("faiss 라이브러리가 설치되어 있지 않습니다.") from e
        
        self._faiss = faiss
        self._np = np
        self._texts = texts
        self._metas = metadatas
        
        # 임베딩 모델 선택 (API 우선, 실패 시 로컬 폴백)
        try:
            self._embedder = get_embedder(use_api=use_api)
            print(f"임베딩 모델 사용: {'API' if use_api else '로컬'}")
        except Exception as e:
            print(f"API 임베딩 실패, 로컬 모델로 폴백: {e}")
            self._embedder = get_embedder(use_api=False)
        
        self._dim = self._embedder.dimension

        # 임베딩 생성
        print("임베딩 생성 중...")
        vecs = self._embedder.encode(texts)
        
        # 인덱스 디렉토리 설정
        self._index_dir = index_dir
        index_path = os.path.join(index_dir, "index.faiss") if index_dir else None
        meta_path = os.path.join(index_dir, "meta.json") if index_dir else None

        # 기존 인덱스 로드 또는 새로 생성
        if index_path and os.path.exists(index_path):
            self._index = faiss.read_index(index_path)
            print(f"기존 FAISS 인덱스 로드: {index_path}")
        else:
            self._index = faiss.IndexFlatIP(self._dim)
            # 정규화된 벡터로 인덱스 생성
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8
            vecs_norm = vecs / norms
            self._index.add(vecs_norm)
            
            # 새로 만든 경우 저장
            if index_path:
                try:
                    os.makedirs(index_dir, exist_ok=True)
                    faiss.write_index(self._index, index_path)
                    
                    # 메타데이터 저장
                    meta = {
                        "num_texts": len(texts),
                        "dim": int(self._dim),
                        "model": "solar-1-mini-embedding" if use_api else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        "embedder_type": "api" if use_api else "local"
                    }
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False)
                    print(f"새 FAISS 인덱스 저장: {index_path}")
                except Exception as e:
                    print(f"FAISS 인덱스 저장 실패: {e}")

        # 정규화된 벡터 저장 (검색용)
        self._vecs_norm = vecs / (self._np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8)

    def get_relevant_documents(self, query: str) -> List[RetrievedDocument]:
        """관련 문서 검색"""
        if not query:
            return []
        
        # 쿼리 임베딩 및 정규화
        qv = self._embedder.encode([query])
        qv = qv / (self._np.linalg.norm(qv, axis=1, keepdims=True) + 1e-8)
        
        # FAISS 검색
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


# 캐시 변수들
_CACHED: Optional[TfIdfRetriever] = None
_CACHED_FAISS: Optional[FaissRetriever] = None


def get_retriever() -> TfIdfRetriever:
    """TF-IDF 검색기 반환"""
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    
    # 데이터베이스 경로 찾기
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "database"))
    
    docs = _load_review_texts(base_dir)
    texts = [d.page_content for d in docs]
    metas = [d.metadata for d in docs]
    
    _CACHED = TfIdfRetriever(texts, metas)
    return _CACHED


def get_faiss_retriever(use_api: bool = True) -> FaissRetriever:
    """FAISS 검색기 반환
    
    Args:
        use_api: True면 API 임베딩 사용, False면 로컬 임베딩 사용
    """
    global _CACHED_FAISS
    if _CACHED_FAISS is not None:
        return _CACHED_FAISS
    
    # 데이터베이스 경로 찾기
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "database"))
    
    docs = _load_review_texts(base_dir)
    texts = [d.page_content for d in docs]
    metas = [d.metadata for d in docs]
    
    # FAISS 인덱스 디렉토리 설정
    index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "faiss_index"))
    os.makedirs(index_dir, exist_ok=True)
    
    _CACHED_FAISS = FaissRetriever(texts, metas, index_dir=index_dir, use_api=use_api)
    return _CACHED_FAISS


