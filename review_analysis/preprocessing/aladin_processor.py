from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import re
import os


class AladinProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)
        self.input_path = input_path
        self.output_path = output_path

    def preprocess(self):

        """
        1. 결측치 제거
        2. 별점 이상치 제거
        3. 텍스트 기준 이상치 제거
        4. 특수 문자 제거

        """
        df = pd.read_csv(os.path.join(self.input_path))
        df["text"] = df["리뷰"].astype(str)
        df["date"] = pd.to_datetime(df["날짜"], errors="coerce")
        df["score"]= df["별점"] * 2
        df.drop(columns=["리뷰", "날짜", "별점"], inplace=True)

        df = df.dropna(subset=["score", "text", "date"])
        df = df[(df["score"] >= 0) & (df["score"] <= 10)]
        df["text_length"] = df["text"].str.len()
        df = df[(df["text_length"] >= 5) & (df["text_length"] <= 1000)]
        df["cleaned_text"] = df["text"].apply(lambda x: re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]", "", x))
        self.df = df
    

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
        output_file = os.path.join(self.output_path, f"preprocessed_reviews_aladin.csv")
        self.df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"파일 저장 완료: {output_file}")
