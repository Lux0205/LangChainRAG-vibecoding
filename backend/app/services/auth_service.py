"""认证服务 - 注册、登录、改密"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token


class AuthService:

    @staticmethod
    def register(db: Session, username: str, password: str) -> User:
        """用户注册"""
        # 检查用户名是否已存在
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )

        # 创建用户
        user = User(
            username=username,
            password_hash=hash_password(password),
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> dict:
        """用户登录，返回Token和用户信息"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        # 生成Token
        token_data = {"user_id": user.id, "username": user.username, "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误",
            )

        user.password_hash = hash_password(new_password)
        db.commit()
        return True

    @staticmethod
    def refresh_access_token(user: User) -> str:
        """刷新Access Token"""
        token_data = {"user_id": user.id, "username": user.username, "role": user.role}
        return create_access_token(token_data)
