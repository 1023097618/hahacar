#业务逻辑
#封装数据库操作、业务逻辑
#增删改查封装
# 获取项目根目录
import os
import sys
from http.client import HTTPException
from typing import List

from fastapi import Header
from sqlalchemy.orm import Session

from models.camera import Camera
from models.user_camera import UserCamera

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.user import User
from dependencies.database import SessionLocal
from core.security import *

default_password = "123456"
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
    hashed_password = hash_password(default_password)
    new_user = User(
        username=user_data.username,
        # email=user_data.email,
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
    # if not payload or not payload.get("is_admin"):
    #     return None, 0
    if not payload :
        return None, 0

    db = SessionLocal()
    users = db.query(User).offset((pagenum - 1) * pagesize).limit(pagesize).all()
    total_users = db.query(User).count()
    db.close()

    user_list = [
        {"realName": u.real_name, "privilege": 2 if u.is_admin else 1, "username": u.username,"userId":u.id,"userRemark":u.user_remark}
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

def is_admin(token):
    payload = verify_jwt_token(token)
    if not payload:
        print('not playload')
        return False

    return bool(payload.get("is_admin"))


def update_user_service(username: str, real_name: str, user_remark: str, user_id: str, privilege: int, db: Session):
    # 根据 user_id 获取用户对象
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise Exception("User not found")

    # 更新用户信息
    user.username = username
    user.real_name = real_name
    user.user_remark = user_remark
    # privilege 对应 is_admin 字段，1 表示普通用户，2 表示管理员
    user.is_admin = 1 if privilege==2 else 0

    db.commit()
    db.refresh(user)

    # 返回更新后的关键信息
    return {
        "id": user.id,
        "username": user.username,
        "realName": user.real_name,
        "userRemark": user.user_remark,
        "privilege": user.is_admin
    }


def get_user_camera_privilege_service(user_id: int, db: Session):
    """
    根据用户ID查询该用户具有权限的摄像头信息
    """
    records = db.query(UserCamera).filter(UserCamera.user_id == user_id).all()
    cameras = []
    for record in records:
        if record.camera:
            cameras.append({
                "cameraId": record.camera.id,
                "cameraName": record.camera.cameraName
            })
    return cameras


def add_user_service(username: str, real_name: str, user_remark: str, privilege: int, db: Session):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"code": "400", "msg": "User added already", "data": {}}

    try:
        # 新建用户，注意 password_hash 必填，此处设置默认密码哈希值
        new_user = User(
            username=username,
            real_name=real_name,
            user_remark=user_remark,
            is_admin=1 if privilege==2 else 0,  # privilege1 表示普通用户，2 表示管理员
            password_hash=hash_password("666666"),  # 实际应使用合适的密码加密算法处理
            first_login=True  # 新用户默认使用默认密码
        )
    except Exception as e:
        print(f"Error adding user: {e}")  # 日志输出详细异常信息
        raise HTTPException(status_code=400, detail=str(e))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 返回新用户关键信息
    return {
        # "id": new_user.id,
        "username": new_user.username,
        "realName": new_user.real_name,
        "userRemark": new_user.user_remark,
        "privilege": new_user.is_admin
    }


def delete_user_service(user_id: str, db: Session):
    # 将 user_id 转换为整数，如果 User.id 为整数类型
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise Exception("Invalid userId format")

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise Exception("User not found")

    db.delete(user)
    db.commit()


def update_user_camera_privilege_service(user_id: str, cameras: List[str], db: Session):
    # 将 user_id 转换为整数，假定 User.id 为整数类型
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise Exception("Invalid userId format")

    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise Exception("User not found")

    # 校验传入的每个摄像头 id 是否存在
    for camera_id in cameras:
        cam = db.query(Camera).filter(Camera.id == camera_id).first()
        if not cam:
            raise Exception(f"Camera id {camera_id} does not exist")

    # 删除该用户原有的摄像头权限记录
    db.query(UserCamera).filter(UserCamera.user_id == user_id_int).delete()

    # 插入新的摄像头权限记录
    for camera_id in cameras:
        new_record = UserCamera(user_id=user_id_int, camera_id=camera_id)
        db.add(new_record)

    db.commit()