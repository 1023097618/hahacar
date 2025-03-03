#业务逻辑
#封装数据库操作、业务逻辑
#增删改查封装
# 获取项目根目录
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.user import User
from dependencies.database import SessionLocal
from core.security import *

def create_user(user_data):
    """
    **description**
    创建用户，并对密码进行加密。

    **params**
    user_data: 用户创建数据（Pydantic 模型）。

    **returns**
    新建用户对象。
    """
    db = SessionLocal()
    #密码hash加密
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        realName=user_data.realName,
        firstLogin=True,  # 默认用户第一次登录
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return new_user

def authenticate_user(username, password):
    """
    **description**
    通过邮箱和密码验证用户。

    **params**
    email: 用户邮箱。
    password: 明文密码。

    **returns**
    认证成功返回用户对象，失败返回 None。
    """
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if user and verify_password(password, user.password_hash):
        return user
    return None

def get_user_by_token(token):
    """
    **description**
    通过 JWT Token 获取用户信息。

    **params**
    token: JWT 令牌。

    **returns**
    用户对象 或 None。
    """
    from core.security import verify_jwt_token
    payload = verify_jwt_token(token)  #验证传入的token,playload为存储在JWT token 中的数据
    if payload is None:
        return None
    db = SessionLocal()
    user = db.query(User).filter(User.id == payload["sub"]).first() #sub是JWT中代表用户的唯一标识
    db.close()
    return user

def update_password(username, old_password, new_password):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(old_password, user.password_hash):
        db.close()
        return False

    user.password_hash = hash_password(new_password)
    user.firstLogin = False  # 用户已修改默认密码
    db.commit()
    db.close()
    return True

def update_password_by_token(token, new_password):
    payload = verify_jwt_token(token)
    if not payload:
        return False

    db = SessionLocal()
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        db.close()
        return False

    user.password_hash = hash_password(new_password)
    user.firstLogin = False
    db.commit()
    db.close()
    return True


def get_user_list(token, pagenum, pagesize):
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return None, 0

    db = SessionLocal()
    users = db.query(User).offset((pagenum - 1) * pagesize).limit(pagesize).all()
    total_users = db.query(User).count()
    db.close()

    user_list = [
        {"realName": u.realName, "privilege": 1 if u.is_admin else 0, "userName": u.username}
        for u in users
    ]
    return user_list, total_users

def update_user_style(token, style):
    payload = verify_jwt_token(token)
    if not payload:
        return False

    db = SessionLocal()
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        db.close()
        return False

    user.style = style
    db.commit()
    db.close()
    return True