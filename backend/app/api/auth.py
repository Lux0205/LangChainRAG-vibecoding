"""认证API路由"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    ChangePasswordRequest, MessageResponse,
)
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=MessageResponse, summary="用户注册")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户"""
    AuthService.register(db, request.username, request.password)
    return MessageResponse(message="注册成功")


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录，返回JWT Token"""
    return AuthService.login(db, request.username, request.password)


@router.post("/refresh", summary="刷新Token")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """使用Refresh Token获取新的Access Token"""
    new_token = AuthService.refresh_access_token(current_user)
    return {"access_token": new_token, "token_type": "bearer"}


@router.put("/password", response_model=MessageResponse, summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    AuthService.change_password(db, current_user, request.old_password, request.new_password)
    return MessageResponse(message="密码修改成功")


@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user.to_dict()
