from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.user.user_schema import User
#from app.config import USER_DATA
from sqlalchemy import text
from database.mysql_connection import SessionLocal

class UserRepository:
    def __init__(self):
        pass
    
    def _get_db(self) -> Session:
        return SessionLocal()

    # def _load_users(self) -> Dict[str, Dict]:
    #     try:
    #         with open(USER_DATA, "r") as f:
    #             return json.load(f)
    #     except FileNotFoundError:
    #         raise ValueError("File not found")

    def get_user_by_email(self, email: str) -> Optional[User]:
        db = self._get_db()
        try:
            result = db.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email}
            ).mappings().first()

            if result is None:
                return None
            return User(**result)
        finally:
            db.close()

    def save_user(self, user: User) -> User:
        db = self._get_db()
        try:
            db.execute(
                text("REPLACE INTO users (username, email, password) VALUES (:username, :email, :password)"),
                {
                    "username": user.username,
                    "email": user.email,
                    "password": user.password
                }
            )
            db.commit()
            return user
        finally:
            db.close()

    def delete_user(self, user: User) -> User:
        db = self._get_db()
        try:
            db.execute(
                text("DELETE FROM users WHERE email = :email"),
                {"email": user.email}
            )
            db.commit()
            return user
        finally:
            db.close()