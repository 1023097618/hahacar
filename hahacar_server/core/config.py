#读取环境变量

from pydantic import BaseSettings
from dotenv import load_dotenv  #用于管理环境保变量、加载env变量到程序中
import os

# 加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./default.db")
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# 创建全局配置实例
settings = Settings()
