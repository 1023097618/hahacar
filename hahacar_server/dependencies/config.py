from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    """
    **description**
    项目配置文件，加载环境变量和默认配置。

    **params**
    DATABASE_URL: SQLite 数据库连接字符串。
    SECRET_KEY: JWT 认证秘钥。
    ACCESS_TOKEN_EXPIRE_MINUTES: 访问令牌的有效时间（分钟）。
    DEBUG: 是否开启调试模式。

    **returns**
    None
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, '../../data/db.sqlite3')}"  # SQLite 数据库路径
    SECRET_KEY: str = "your_secret_key_here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # JWT 令牌有效时间（分钟）
    DEBUG: bool = True  # 是否开启调试模式

    class Config:
        env_file = ".env"  # 从 .env 文件加载配置

settings = Settings()
