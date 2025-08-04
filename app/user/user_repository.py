import json

from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.user.user_schema import User
from app.config import USER_DATA

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _load_users(self) -> Dict[str, Dict]:
        try:
            with open(USER_DATA, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError("File not found")

    def get_user_by_email(self, email: str) -> Optional[User]:
        result = self.db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        ).mappings().first()

        return User(**result) if result else None

    def save_user(self, user: User) -> User:
        self.db.execute(
            text("REPLACE INTO users (email, password, username) VALUES (:email, :password, :username)"),
            user.model_dump()
        )
        self.db.commit()
        return user

    def delete_user(self, user: User) -> User:
        self.db.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": user.email}
        )
        self.db.commit()
        return user