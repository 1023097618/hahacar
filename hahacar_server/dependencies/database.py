
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 确定数据库存储路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(PARENT_DIR, "data", "db.sqlite3")

# 创建数据库引擎（使用 SQLite）
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 创建 ORM 基类
Base = declarative_base()

# 创建数据库会话工厂
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

#确保每个请求都有独立的数据库会话
def get_db():
    """
    **description**
    创建数据库会话，并在请求结束时自动关闭。

    **returns**
    数据库会话生成器。
    """
    db = SessionLocal()
    try:
        return db  # 生成会话
    finally:
        db.close()  # 关闭会话