from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    '''
    Service Layer에 로그인 요청
    1. 로그인 성공 응답 반환
    2. Service에서 발생한 에러를 HTTP 400으로 변환
    '''
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    '''
    Service Layer에 회원가입 요청
    1. 회원가입 성공 응답 반환
    2. 이메일 중복 등 에러 발생 시 HTTP 400으로 변환
    '''
    ## TODO
    try:
        user_data = service.register_user(user)
        return BaseResponse(status="success", data=user_data, message="User registration success.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    '''
    Service Layer에 사용자 삭제 요청
    1. 삭제 성공 응답 반환
    2. 사용자가 존재하지 않을 경우 HTTP 404로 변환
    '''
    try:
        user_data = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=user_data, message="User Deletion Success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    Service Layer에 비밀번호 업데이트 요청
    1. 비밀번호 변경 성공 응답 반환
    2. 사용자가 존재하지 않을 경우 HTTP 404로 변환
    """
    try:
        user_data = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=user_data, message="User password update success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
