#sqlalchemy是一个Python SQL工具包和ORM框架，用于数据库访问
from datetime import datetime, timezone
import enum
import os
import sys
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship

# 获取项目根目录
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dependencies.database import Base

#每个表对应一个python类
class User(Base):
    """
    **description**
    用户数据库模型。

    **params**
    id: 主键ID。
    username: 用户名，唯一索引。
    email: 邮箱，唯一索引。
    password_hash: 哈希加密的密码。
    is_active: 是否激活。
    is_admin: 是否管理员。
    区分普通用户和管理员
    firstLogin: 当前用户是否使用的是默认密码，如果是1代表使用的是默认的密码，如果是0代表用户已经修改过默认密码了
    realName: 用户的真实姓名
    style: 当前用户选择界面的样式，如果是1代表"白天样式"，如果是2代表"黑夜样式"，如果是3代表"跟随系统"
    created_at: 记录用户注册时间，默认为当前时间.

    **returns**
    None
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Integer, default=0)
    first_login = Column(Boolean, default=True)
    real_name = Column(String, default="")
    style = Column(Enum("1", "2", "3", name="style_enum"), default="1")  # 限定枚举值
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_remark = Column(String, default="")  # 新增字段：用户备注

    # 反向关系：一个用户可以关联多个摄像头
    user_cameras = relationship("UserCamera", back_populates="user")