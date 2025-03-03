import os
import sys

# 获取项目根目录
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dependencies.database import Base, engine

#导入数据模型模块，可以被create_all扫描到
from models import *

def init_db():
    """
    **description**
    初始化 SQLite 数据库，并创建所有表。

    **params**
    None

    **returns**
    None
    """
    db_path = os.path.join(os.path.dirname(__file__), "../data/db.sqlite3")
    if not os.path.exists(db_path):
        print("数据库文件不存在，正在创建...")
        Base.metadata.create_all(bind=engine)   #创建数据库表;指定数据库引擎
        print("数据库初始化完成！")
    else:
        print("数据库已存在，无需初始化！")

if __name__ == "__main__":
    init_db()
