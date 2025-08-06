from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

try:
    mongo_client = MongoClient(
        mongo_url,
        tls=True,
        tlsAllowInvalidCertificates=False,  # 가능하면 False 유지
        serverSelectionTimeoutMS=20000,
    )
    mongo_client.admin.command('ping')  # 연결 테스트
except Exception as e:
    print("MongoDB 연결 실패:", e)
    raise

mongo_db = mongo_client.get_database("review_data_9")
