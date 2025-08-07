from fastapi import Depends
from sqlalchemy.orm import Session
from app.user.user_repository import UserRepository
from app.user.user_service import UserService
from database.mysql_connection import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    if db is None:
        raise ("DaValueErrortabase session is None")
    return UserRepository()

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    if repo is None:
        raise ValueError("UserRepository is None")
    return UserService(repo)