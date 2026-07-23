"""
JWT认证依赖 - 用于FastAPI的Depends注入
带缓存：验证过的Token在一定时间内不重复查DB，减少数据库压力
注意：当前使用进程内缓存，多worker部署时每个worker有独立缓存
"""
import time
import logging
from collections import OrderedDict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.jwt import verify_access_token
from app.models.user import User

# Bearer Token安全方案
security_scheme = HTTPBearer(auto_error=False)

# ==================== Token缓存 ====================
# 结构: OrderedDict {token_str: (user_dict, expire_at)}
# 使用OrderedDict实现LRU淘汰，避免clear()导致的数据库压力突刺
# 缓存有效期与Token过期时间一致（默认30分钟）
_token_cache: OrderedDict = OrderedDict()
CACHE_TTL_SECONDS = 60 * 30  # 30分钟
CACHE_MAX_SIZE = 1000         # 最大缓存条数


def _get_cached_user(token_str: str):
    """从缓存获取用户数据字典，过期或不存在返回None"""
    entry = _token_cache.get(token_str)
    if entry is None:
        return None
    user_dict, expire_at = entry
    if time.time() > expire_at:
        # 缓存已过期，清除
        del _token_cache[token_str]
        return None
    # 移动到末尾（标记为最近使用）
    _token_cache.move_to_end(token_str)
    return user_dict


def _set_cached_user(token_str: str, user_dict: dict):
    """将用户数据字典存入缓存（LRU淘汰策略）"""
    _token_cache[token_str] = (user_dict, time.time() + CACHE_TTL_SECONDS)
    _token_cache.move_to_end(token_str)
    # LRU淘汰：超过最大值时移除最旧的条目（而非清空全部）
    while len(_token_cache) > CACHE_MAX_SIZE:
        _token_cache.popitem(last=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户（带缓存优化）
    - 从Authorization头提取Bearer Token
    - 验证Token有效性
    - 优先从缓存获取用户ID，缓存未命中再查DB
    - 查询并返回用户对象
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token_str = credentials.credentials
    payload = verify_access_token(token_str)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # 优先从缓存获取用户数据（避免每次请求都查DB）
    cached_user_dict = _get_cached_user(token_str)
    if cached_user_dict is not None:
        # 缓存命中：从缓存数据重建User对象（无DB查询）
        user = User(
            id=cached_user_dict["id"],
            username=cached_user_dict["username"],
            role=cached_user_dict["role"],
            password_hash="",
        )
        return user

    # 缓存未命中：查DB并写入缓存
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # 缓存用户数据字典（仅缓存必要字段，不缓存整个ORM对象）
    _set_cached_user(token_str, {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    })
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    验证当前用户是管理员
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可操作",
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选认证 - 不强制要求登录"""
    if not credentials:
        return None
    payload = verify_access_token(credentials.credentials)
    if payload is None:
        return None
    user_id = payload.get("user_id")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()
