
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import os

# 确定数据库存储路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(PARENT_DIR, "data", "db.sqlite3")

# 创建数据库引擎（使用 SQLite）
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True,pool_size=20,max_overflow=10)

# 创建 ORM 基类
Base = declarative_base()

# 创建数据库会话工厂
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

#确保每个请求都有独立的数据库会话
def get_db():
    """
    description
    在fastapi处理请求的方法中调用

    example:
    @router.post("/updateCamera")
    def method_name(
            db: Session = Depends(get_db)
    ):
        ...
    """
    db = SessionLocal()
    try:
        yield db  # 生成会话
    finally:
        db.close()  # 关闭会话

def get_db_session() -> Session:
    """
    description：
    在fastapi处理请求之外的方法中调用

    example:
    db,close_db=get_db_session()
    try:
        ...
    finally:
        close_db()
    """
    db_gen = get_db()  # 获取生成器
    db_session = next(db_gen)  # 取出数据库会话
    # 定义一个关闭会话的函数（可以用 try/finally 包裹调用处）
    def close_session():
        try:
            next(db_gen)
        except StopIteration:
            pass
    return db_session, close_session
