from typing import Optional
from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate


class UserService:
    def __init__(self, userRepository: UserRepository) -> None:
        """
        사용자 서비스 클래스의 생성자입니다.

        Args:
            userRepository (UserRepository): 사용자 데이터를 관리하는 저장소 객체
        """
        self.repo: UserRepository = userRepository

    def login(self, login_data: UserLogin) -> User:
        """
        사용자의 이메일과 비밀번호를 확인하여 로그인합니다.

        Args:
            login_data (UserLogin): 로그인 요청으로 받은 이메일과 비밀번호

        Returns:
            User: 로그인에 성공한 사용자 정보

        Raises:
            ValueError: 이메일이 존재하지 않거나 비밀번호가 일치하지 않을 경우
        """
        user: Optional[User] = self.repo.get_user_by_email(login_data.email)
        if not user:
            raise ValueError("User not Found.")
        if user.password != login_data.password:
            raise ValueError("Invalid ID/PW")
        return user

    def register_user(self, user: User) -> User:
        """
        새로운 사용자를 등록합니다.

        Args:
            user (User): 등록할 사용자 정보

        Returns:
            User: 저장된 사용자 정보

        Raises:
            ValueError: 이미 존재하는 이메일일 경우
        """
        if self.repo.get_user_by_email(user.email):
            raise ValueError("User already Exists.")
        return self.repo.save_user(user)

    def delete_user(self, email: str) -> User:
        """
        주어진 이메일에 해당하는 사용자를 삭제합니다.

        Args:
            email (str): 삭제할 사용자의 이메일

        Returns:
            User: 삭제된 사용자 정보

        Raises:
            ValueError: 사용자가 존재하지 않을 경우
        """
        user: Optional[User] = self.repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not Found.")
        return self.repo.delete_user(user)

    def update_user_pwd(self, update_data: UserUpdate) -> User:
        """
        사용자의 비밀번호를 새 비밀번호로 변경합니다.

        Args:
            update_data (UserUpdate): 이메일과 새 비밀번호가 포함된 업데이트 정보

        Returns:
            User: 비밀번호가 변경된 사용자 정보

        Raises:
            ValueError: 사용자가 존재하지 않을 경우
        """
        user: Optional[User] = self.repo.get_user_by_email(update_data.email)
        if not user:
            raise ValueError("User not Found.")
        
        user.password = update_data.new_password
        return self.repo.save_user(user)