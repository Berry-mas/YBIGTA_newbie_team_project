from review_analysis.preprocessing.base_processor import BaseDataProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import re
import os

class Yes24Processor(BaseDataProcessor):
    # def __init__(self, input_path: str, output_path: str):
    #     super().__init__(input_path, output_path)
    def __init__(self, mongo_db, site_name: str):
        self.mongo_db = mongo_db
        self.site_name = site_name
        self.df = None

    def preprocess(self, raw_reviews):
        '''
        리뷰 전처리:
        1. rate 숫자만 추출
        2. 컬럼명 통일
        3. 결측치 제거
        4. 이상치 제거
        5. 특수문자 제거
        '''
        
        # df = pd.read_csv(self.input_path)

        
        # df["rate"] = df["rate"].astype(str).str.extract(r"(\d+)").astype(float)
        # MongoDB 데이터를 DataFrame으로 변환
        df = pd.DataFrame(raw_reviews)
        
        # Yes24 데이터 구조: ['_id', 'rate', 'day', 'review']
        
        # 1. rate 컬럼 처리 (평점10점 -> 10)
        if "rate" in df.columns:
            df["score"] = df["rate"].astype(str).str.extract(r"(\d+)").astype(float)
        
        # 2. 컬럼명 통일
        if "review" in df.columns:
            df["text"] = df["review"].astype(str)
        
        if "day" in df.columns:
            df["date"] = pd.to_datetime(df["day"], errors="coerce")
            
        # 3. 불필요한 컬럼 제거 (_id는 MongoDB 기본 키)
        columns_to_drop = ["_id", "rate", "day", "review"]
        df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True, errors='ignore')

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
        '''
        파생변수 생성:
        date를 기반으로 weekday 생성

        텍스트 벡터화:
        cleaned_text를 기반으로 TF-IDF 텍스트 벡터화
        '''
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
        # '''
        # 전처리 데이터 csv 저장
        # '''
        # os.makedirs(self.output_dir, exist_ok=True)
        # output_file = os.path.join(self.output_dir, "preprocessed_reviews_yes24.csv")
        # self.df.to_csv(output_file, index=False, encoding="utf-8-sig")
        # print(f"저장 완료: {output_file}")
        """전처리된 데이터를 MongoDB의 yes24_preprocessed 컬렉션에 저장"""
        if self.df is not None:
            preprocessed_collection = self.mongo_db["yes24_preprocessed"]
            
            # DataFrame을 딕셔너리 리스트로 변환
            records = self.df.to_dict('records')
            
            # MongoDB에 저장
            if records:
                preprocessed_collection.insert_many(records)
                print(f"MongoDB에 {len(records)}개의 전처리된 데이터 저장 완료: yes24_preprocessed")
            else:
                print("저장할 데이터가 없습니다.")
        else:
            print("전처리된 데이터가 없습니다. preprocess()를 먼저 실행하세요.")
