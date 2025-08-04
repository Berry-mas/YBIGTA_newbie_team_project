import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["book_reviews"]

def load_and_insert(csv_path, site_name):
    df = pd.read_csv(csv_path)
    
    # 🔧 인덱스 컬럼 제거
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    if site_name == "kyobo":
        df = df.rename(columns={"score": "score", "text": "text", "date": "date"})
    elif site_name == "yes24":
        df["score"] = df["rate"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.rename(columns={"review": "text", "day": "date"})
    elif site_name == "aladin":
        df["score"] = df["별점"] * 2
        df = df.rename(columns={"리뷰": "text", "날짜": "date"})

    df = df[["score", "text", "date"]]
    df["site"] = site_name
    df["text"] = df["text"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["score", "text", "date"])

    records = df.to_dict(orient="records")
    db[site_name].insert_many(records)
    print(f"✅ {site_name}: {len(records)}건 삽입 완료")

load_and_insert("database/reviews_kyobo.csv", "kyobo")
load_and_insert("database/reviews_yes24.csv", "yes24")
load_and_insert("database/reviews_aladin.csv", "aladin")

