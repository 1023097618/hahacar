import os
import sys

from fastapi import APIRouter, Depends, HTTPException, Header, Query

from core.security import create_jwt_token

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemas.user_schema import *
from services.user_service import *

router = APIRouter(prefix="/api")

#用户注册
@router.post("/user/register", response_model=UserCreateResponse)
def register_user(user_data: UserCreate):
    """
    **description**
    用户注册接口。

    **params**
    user_data: 用户注册信息。

    **returns**
    新用户信息。
    """
    user = create_user(user_data)
    if not user:
        # raise HTTPException(status_code=400, detail="Username already registered")
        return {"code":"400", "msg":"Username already registered", "data":""}
    return {
        "code": "200",
        "msg": "Register Successfully"
    }

#用户登录√
@router.post("/auth/login",response_model=JSONResponseSchema)
def login(user_data: UserLogin):
    """
    **description**
    用户登录接口。

    **params**
    user_data: 用户登录信息。

    **returns**
    访问令牌（JWT）。
    """
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        # raise CustomHTTPException(code="400", msg="password not right",data="")
        return {"code": "400", "msg": "password not right", "data": ""}
    token = create_jwt_token({"sub": str(user.id)})
    return {
        "code": "200",
        "msg": "Login Successfully",
        "data":{
            "token": token
        }
    }

#通过Token获取用户信息
@router.get("/auth/info", response_model=JSONResponseSchema)
def get_user_info(token: str):
    """
    **description**
    通过 Token 获取用户信息。

    **params**
    token: 用户 JWT 令牌。

    **returns**
    用户信息。
    """
    user = get_user_by_token(token)
    if not user:
        # raise HTTPException(status_code=401, detail="Token useless")
        # raise CustomHTTPException(code="401", msg="Token useless", data="")
        return {"code": "401", "msg": "Token useless", "data": ""}

    # 构造用户信息
    user_response = UserInfoResponse(
        style=user.style,
        firstLogin=user.first_login,
        realName=user.real_name,
        username=user.username,
        userId=user.id,
        privilege=2 if user.is_admin else 1
    )

    return JSONResponseSchema(
        code="200",
        msg="sucess",
        data=user_response
    )

#通过旧密码修改密码?通过用户名修改
@router.post("/auth/changePasswordByOldpassword", response_model=JSONResponseSchema)
def change_password(password_data: UpdatePasswordRequest):
    """
    **description**
    用户通过旧密码修改密码。

    **params**
    password_data: 旧密码、新密码、用户名。

    **returns**
    修改成功或失败信息。
    """
    success = update_password(password_data.username, password_data.old_password, password_data.new_password)
    if not success:
        # raise HTTPException(status_code=400, detail="旧密码错误或用户不存在")
        # raise CustomHTTPException(code="400", msg="旧密码错误或用户不存在", data="")
        return {"code": "400", "msg": "旧密码错误或用户不存在", "data": ""}
    return {"code": "200", "msg": "密码修改成功", "data": {}}


#基于Token修改密码
@router.post("/auth/changePasswordByToken")
def change_password_by_token(
    token: str = Header(None, alias="X-HAHACAR-TOKEN"),
    password_data: TokenPasswordRequest = Depends()
):
    """
    **description**
    用户通过 Token 修改密码。

    **params**
    token: JWT 令牌（Header 参数）。
    password_data: 新密码。

    **returns**
    修改成功或失败信息。
    """
    success = update_password_by_token(token, password_data.new_password)
    if not success:
        # raise HTTPException(status_code=401, detail="Token 无效或用户不存在")
        # raise CustomHTTPException(code="401", msg="Token 无效或用户不存在", data="")
        return {"code": "400", "msg": "Token 无效或用户不存在", "data": ""}
    return {"code": "200", "msg": "密码修改成功", "data": {}}

#获取用户列表（基于管理员Token）
@router.get("/user/getUsers")
def get_users(
        pagenum: int = Query(..., description="当前页码"),
        pagesize: int = Query(..., description="每页数据量"),
        token: str = Header(None, alias="X-HAHACAR-TOKEN")
):
    """
    **description**
    获取当前用户列表（仅管理员可访问）。

    **params**
    pagenum: 当前页码。
    pagesize: 每页显示数量。
    token: JWT 令牌（Header 参数）。

    **returns**
    用户列表或认证失败信息。
    """
    users, total_users = get_user_list(token, pagenum, pagesize)
    if users is None:
        # raise HTTPException(status_code=401, detail="未认证的管理员")
        # raise CustomHTTPException(code="401", msg="未认证的管理员", data="")
        return {"code": "401", "msg": "未认证的管理员", "data": ""}
    return {
        "code": "200",
        "msg": "获取成功",
        "data": {
            "users": users,
            "userNum": str(total_users)
        }
    }

#修改用户偏好的界面样式
@router.post("/user/styleChange")
def update_user_style_api(
        style_data: UpdateStyleRequest,
        token: str = Header(None, alias="X-HAHACAR-TOKEN")
):
    """
    **description**
    修改用户界面偏好样式。

    **params**
    token: JWT 令牌（Header 参数）。
    style_data: 需要修改的界面风格（1=白天, 2=黑夜, 3=跟随系统）。

    **returns**
    成功或失败信息。
    """
    if style_data.style not in ["1","2", "3"]:
        # raise CustomHTTPException(code="400", msg="样式值必须为 1, 2, 3", data="")
        return {"code": "400", "msg": "样式值必须为 1, 2, 3", "data": ""}
        # raise HTTPException(status_code=400, detail="样式值必须为 1, 2, 3")

    success = update_user_style(token, style_data.style)
    if not success:
        # raise HTTPException(status_code=401, detail="Token 无效或用户不存在")
        # raise CustomHTTPException(code="401", msg="Token 无效或用户不存在", data="")
        return {"code": "401", "msg": "Token 无效或用户不存在", "data": ""}

    return {"code": "200", "msg": "样式更新成功", "data": {}}
