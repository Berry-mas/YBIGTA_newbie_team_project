from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import re
import os

class yes24Processor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)

    def preprocess(self):
        
        df = pd.read_csv(self.input_path)
        
        #컬럼명 통일
        df = df.rename(columns={
        "rate": "score",
        "review": "text",
        "day": "date"
        })

        #data type 변환
        df["text"] = df["text"].astype(str)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # 결측치 제거(EA과정에서 없는 것 확인)
        df = df.dropna(subset=["score", "text", "date"])

        # 이상치 제거 (별점 범위 밖)
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df = df[(df["score"] >= 0) & (df["score"] <= 10)]

        # 이상치 제거 (텍스트 길이/텍스트 데이터 전처리)
        df["text_length"] = df["text"].str.len()
        df = df[(df["text_length"] >= 5) & (df["text_length"] <= 1000)]

        # 특수문자 제거
        df["cleaned_text"] = df["text"].apply(lambda x: re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]", "", x))

        self.df = df
        print("전처리 완료")
    
    def feature_engineering(self):
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
        output_file = os.path.join(self.output_dir, "preprocessed_reviews_yes24.csv")
        self.df.to_csv(output_file, index=False, encoding="utf-8-sig")