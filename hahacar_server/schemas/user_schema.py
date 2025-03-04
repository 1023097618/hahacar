#SQLAlchemy 的 ORM 模型 适用于数据库，但不能直接用于 API 请求/响应
#定义Pydantic模型，用于请求和响应的数据格式的数据传输
from typing import Optional, Any

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """
    **description**
    创建用户请求模型。

    **params**
    username: 用户名。
    email: 邮箱地址。
    password: 明文密码。

    **returns**
    None
    """
    username: str
    realName: str

class UserCreateResponse(BaseModel):
    """
    **description**
    返回给前端的用户信息。

    **params**
    id: 用户ID。
    username: 用户名。
    email: 邮箱地址。

    **returns**
    None
    """
    id: int
    username: str
    email: str

class UserLogin(BaseModel):
    """
    **description**
    用户登录请求模型。

    **params**
    email: 用户邮箱。
    password: 明文密码。

    **returns**
    None
    """
    username: str
    password: str


#返回用户信息响应
class UserInfoResponse(BaseModel):
    """
    **description**
    返回给前端的用户信息。

    **params**
    id: 用户ID。
    username: 用户名。
    email: 邮箱地址。

    **returns**
    None
    """
    style: int
    firstLogin: bool
    realName: str
    username: str
    userId: int
    privilege: int

class UpdatePasswordRequest(BaseModel):
    """
    **description**
    更新密码请求模型。

    **params**
    old_password: 原密码。
    new_password: 新密码。

    **returns**
    None
    """
    old_password: str
    new_password: str
    username: str

class JSONResponseSchema(BaseModel):
    """
    统一 JSON 响应格式
    """
    code: str
    msg: str
    data: Optional[Any]  # `data` 可以是任何数据类型，例如 UserResponse

    class Config:
        orm_mode = True

class TokenPasswordRequest(BaseModel):
    """
    **description**
    更新密码请求模型。

    **params**
    new_password: 新密码。

    **returns**
    None
    """
    new_password: str

class UpdateStyleRequest(BaseModel):
    style: str


class Exception(BaseModel):
    code: str
    msg: str
    data: Optional[Any]  # `data` 可以是任何数据类型，例如 UserResponse

