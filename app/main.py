from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from app.user.user_router import user
from app.review.review_router import router as review_router  # ✅ 추가
from app.config import PORT

app = FastAPI()

@app.get("/")
async def read_root():
    return {"status": "running"}


static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(user)
app.include_router(review_router)  # ✅ 추가

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
