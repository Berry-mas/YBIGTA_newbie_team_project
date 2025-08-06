
import os
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from review_analysis.preprocessing.base_processor import BaseDataProcessor

class KyoboProcessor(BaseDataProcessor):
    # def __init__(self, input_path: str, output_path: str):
    # super().__init__(input_path, output_path)
    def __init__(self, mongo_db, site_name: str):
        self.mongo_db = mongo_db
        self.site_name = site_name
        self.df = None

    def preprocess(self, raw_reviews):
        """
        리뷰 데이터 전처리:
        - 결측치 제거 (score, text, date)
        - 이상치 제거 (0~10 범위를 벗어난 score)
        - 너무 짧거나 긴 리뷰 제거 (5~1000자)
        - 특수문자 제거 후 cleaned_text 생성
        """
        # MongoDB 데이터를 DataFrame으로 변환
        df = pd.DataFrame(raw_reviews)
        
        # 컬럼명 매핑 (MongoDB 데이터 구조에 맞게 조정)
        if "리뷰" in df.columns:
            df["text"] = df["리뷰"].astype(str)
        elif "review" in df.columns:
            df["text"] = df["review"].astype(str)
        elif "text" in df.columns:
            df["text"] = df["text"].astype(str)
        
        if "날짜" in df.columns:
            df["date"] = pd.to_datetime(df["날짜"], errors="coerce")
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            
        if "별점" in df.columns:
            df["score"] = df["별점"] * 2
        elif "rating" in df.columns:
            df["score"] = df["rating"] * 2
        elif "score" in df.columns:
            df["score"] = df["score"]
            
        # 불필요한 컬럼 제거 (_id는 MongoDB 기본 키)
        columns_to_drop = ["리뷰", "날짜", "별점", "review", "rating", "_id"]
        df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True, errors='ignore')

        # 결측치 제거
        df = df.dropna(subset=["score", "text", "date"])

        # 이상치 제거 (별점 범위 밖)
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df = df[(df["score"] >= 0) & (df["score"] <= 10)]

        # 텍스트 길이 기준 이상치 제거 (텍스트 데이터 전처리)
        df["text_length"] = df["text"].str.len()
        df = df[(df["text_length"] >= 5) & (df["text_length"] <= 1000)]

        # 특수문자 제거
        df["cleaned_text"] = df["text"].apply(lambda x: re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]", "", x))

        self.df = df
        print("전처리 완료")

    def feature_engineering(self):
        """
        파생 변수 및 텍스트 벡터화:
        - 요일 변수(weekday) 생성
        - cleaned_text 컬럼 기반 TF-IDF 벡터화 (상위 100개 토큰)
        """
        df = self.df

        # 파생변수: 요일
        df["weekday"] = df["date"].dt.day_name()

        # 텍스트 벡터화 (TF-IDF)
        tfidf = TfidfVectorizer(max_features=100)
        tfidf_matrix = tfidf.fit_transform(df["cleaned_text"])
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=[f"tfidf_{i}" for i in range(tfidf_matrix.shape[1])])

        df.reset_index(drop=True, inplace=True)
        df = pd.concat([df, tfidf_df], axis=1)

        self.df = df
        print("FE 완료")

    def save_to_database(self):
        """
        전처리 및 피처 엔지니어링된 데이터를 CSV로 저장
        - 경로: self.output_dir
        - 파일명: preprocessed_reviews_kyobo.csv
        """
        # os.makedirs(self.output_dir, exist_ok=True)
        # output_file = os.path.join(self.output_dir, "preprocessed_reviews_kyobo.csv")
        # self.df.to_csv(output_file, index=False, encoding="utf-8-sig")
        # print(f"저장 완료: {output_file}")
        """전처리된 데이터를 MongoDB의 kyobo_preprocessed 컬렉션에 저장"""
        if self.df is not None:
            preprocessed_collection = self.mongo_db["kyobo_preprocessed"]
            
            # DataFrame을 딕셔너리 리스트로 변환
            records = self.df.to_dict('records')
            
            # MongoDB에 저장
            if records:
                preprocessed_collection.insert_many(records)
                print(f"MongoDB에 {len(records)}개의 전처리된 데이터 저장 완료: kyobo_preprocessed")
            else:
                print("저장할 데이터가 없습니다.")
        else:
            print("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
