"""
数据库连接管理 - SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# 创建引擎
engine = create_engine(
    settings.database_url,
    pool_size=20,           # 连接池大小
    max_overflow=30,        # 最大溢出连接
    pool_pre_ping=True,     # 连接前ping检测
    pool_recycle=3600,      # 连接回收时间
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
