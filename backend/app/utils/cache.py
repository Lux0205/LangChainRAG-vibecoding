"""Redis缓存封装"""
import json
import redis
from typing import Optional, Any
from app.config import settings

# Redis连接池
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=50,
)

redis_client = redis.Redis(connection_pool=redis_pool)


def cache_set(key: str, value: Any, expire: int = 3600) -> bool:
    """设置缓存"""
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        return redis_client.set(key, value, ex=expire)
    except Exception as e:
        print(f"[缓存] 设置失败: {e}")
        return False


def cache_get(key: str) -> Optional[Any]:
    """获取缓存"""
    try:
        value = redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None
    except Exception as e:
        print(f"[缓存] 获取失败: {e}")
        return None


def cache_delete(key: str) -> bool:
    """删除缓存"""
    try:
        return redis_client.delete(key) > 0
    except Exception as e:
        print(f"[缓存] 删除失败: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """按模式删除缓存"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"[缓存] 批量删除失败: {e}")
        return 0
