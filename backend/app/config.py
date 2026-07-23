"""
全局配置 - 从环境变量或.env文件读取
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # ==================== 应用基础 ====================
    APP_NAME: str = "LangChain RAG 知识库问答系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # 生产环境默认关闭调试
    API_PREFIX: str = "/api"

    # ==================== MySQL ====================
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str  # 强制从环境变量读取，不设默认值
    MYSQL_DATABASE: str = "rag_db"

    # ==================== Redis ====================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ==================== Milvus ====================
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "knowledge_base"

    # ChromaDB embedded storage path
    CHROMA_DIR: str = "../chroma_data"

    # ==================== JWT ====================
    JWT_SECRET_KEY: str  # 强制从环境变量读取
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== LLM配置 ====================
    # 当前使用的模型提供商: "tongyi" 或 "zhipu"
    LLM_PROVIDER: str = "tongyi"

    # Embedding提供商: "tongyi"(云端API) 或 "local"(本地TF-IDF)
    EMBEDDING_PROVIDER: str = "tongyi"

    # 通义千问
    DASHSCOPE_API_KEY: str = ""
    TONGYI_MODEL: str = "qwen-plus"
    TONGYI_EMBEDDING_MODEL: str = "text-embedding-v1"

    # 智谱GLM
    ZHIPU_API_KEY: str = ""
    ZHIPU_MODEL: str = "glm-4"
    ZHIPU_EMBEDDING_MODEL: str = "embedding-3"

    # ==================== RAG配置 ====================
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 3
    RAG_SEARCH_TOP_K: int = 10

    # ==================== 文件上传 ====================
    UPLOAD_DIR: str = "../uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # ==================== 限流 ====================
    RATE_LIMIT_PER_MINUTE: int = 30

    # ==================== 性能配置 ====================
    # 注意：pool_size=15 + max_overflow=35 = 50/worker
    # 总峰值连接 = UVICORN_WORKERS × 50，需 < MySQL max_connections(默认151)
    UVICORN_WORKERS: int = 2         # uvicorn worker 进程数（Windows建议1-2）
    UVICORN_LIMIT_CONCURRENCY: int = 80   # 最大并发连接数（≤ pool_size × workers × 0.8）

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# 全局配置实例
settings = Settings()

# JWT 密钥：未配置时生成随机密钥（每次重启会失效，生产环境请设置 JWT_SECRET_KEY 环境变量）
if not settings.JWT_SECRET_KEY:
    import secrets
    import logging
    settings.JWT_SECRET_KEY = secrets.token_hex(32)
    logging.warning("[安全] JWT_SECRET_KEY 未设置，已生成随机密钥。请设置环境变量以保证 Token 跨重启有效。")

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
