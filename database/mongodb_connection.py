from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

# SSL/TLS 연결 문제 해결을 위한 설정 (더 관대한 설정)
try:
    mongo_client = MongoClient(
        mongo_url,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=60000,  # 60초로 증가
        connectTimeoutMS=60000,
        socketTimeoutMS=60000,
        retryWrites=True,
        maxPoolSize=1  # 연결 풀 크기 제한
    )
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")
    # 폴백: 더 간단한 연결 시도
    mongo_client = MongoClient(mongo_url)

mongo_db = mongo_client.get_database("review_data_9")