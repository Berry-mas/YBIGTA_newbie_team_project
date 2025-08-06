from fastapi import APIRouter, HTTPException

# MongoDB 연결은 실제 사용 시점에 import하도록 변경
# from database.mongodb_connection import mongo_db

from review_analysis.preprocessing.aladin_processor import AladinProcessor
from review_analysis.preprocessing.kyobo_processor import KyoboProcessor
from review_analysis.preprocessing.yes24_processor import Yes24Processor

router = APIRouter(prefix="/review")

@router.post("/preprocess/{site_name}")
def preprocess_reviews(site_name: str):
    if site_name not in ["aladin", "kyobo", "yes24"]:
        raise HTTPException(status_code=400, detail="Invalid site_name")

    try:
        # MongoDB 연결을 실제 사용 시점에 import
        from database.mongodb_connection import mongo_db
        
        raw_collection = mongo_db[f"{site_name}_raw"]
        raw_reviews = list(raw_collection.find({}))
        
        if not raw_reviews:
            raise HTTPException(status_code=404, detail="No reviews found")

        # 전처리 클래스 선택
        processor_class = {
            "aladin": AladinProcessor,
            "kyobo": KyoboProcessor,
            "yes24": Yes24Processor
        }[site_name]

        processor = processor_class(mongo_db, site_name)
        processor.preprocess(raw_reviews)
        
        # Feature engineering with error handling
        try:
            processor.feature_engineering()
            fe_status = "completed"
        except Exception as fe_error:
            print(f"Feature engineering failed for {site_name}: {fe_error}")
            fe_status = "failed (basic preprocessing completed)"
        
        processor.save_to_database()

        return {
            "message": f"{site_name} reviews successfully preprocessed", 
            "count": len(raw_reviews),
            "feature_engineering": fe_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB connection error: {str(e)}")
