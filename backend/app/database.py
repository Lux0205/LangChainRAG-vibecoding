"""
数据库连接管理 - SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# 创建引擎
# 连接池配置（与 UVICORN_WORKERS 配合，总峰值 = workers × (pool_size + max_overflow)）
# 默认 2 workers × (15 + 35) = 100 峰值连接，远低于 MySQL 默认 151 上限
engine = create_engine(
    settings.database_url,
    pool_size=15,           # 常驻连接数（每worker）
    max_overflow=35,        # 最大溢出连接（每worker），突发流量缓冲
    pool_pre_ping=True,     # 连接前ping检测（避免使用已断开连接）
    pool_recycle=3600,      # 连接回收时间（1小时）
    pool_timeout=30,        # 获取连接超时时间（秒）
    echo=settings.DEBUG,    # 调试模式打印SQL
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    from app.models import user, session, message, knowledge  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("[数据库] 表结构初始化完成")
