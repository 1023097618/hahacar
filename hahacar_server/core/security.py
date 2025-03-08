#安全管理JWT认证
import os
import sys
import uuid

from passlib.context import CryptContext  #用于管理密码哈希与验证
import jwt  #用于生成和解析JWT令牌
from datetime import datetime, timedelta    #处理时间，如令牌的有效期
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#密码哈希加密存储
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

#验证输入的密码和存储的哈希密码是否匹配
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()  #data的内容没有变化，每次生成的token也会是相同的
    expire = datetime.utcnow() + expires_delta #过期时间
    print(f"DEBUG: data -> {data}")  # 确保 is_admin 存在
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  #加入令牌签发时间
        "jti": str(uuid.uuid4()),    #令牌唯一标识
        "is_admin": bool(int(data.get("is_admin")))
        })   #添加过期时间到playload
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")  #使用SECRET_KEY和HS256进行签名，生成JWT令牌

#这个bug首先是因为jwt中没有存储is_admin字段，其次是因为is_admin类型是以Nonetype存储在数据库中的
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(f"Decoded payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")  # 记录日志
    except jwt.InvalidTokenError:
        print("Invalid token")
    return None
