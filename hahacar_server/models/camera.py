from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from dependencies.database import Base

class Camera(Base):
    """
    **description**
    摄像头数据库模型

    **params**
    id: 摄像头ID
    cameraURL: 摄像头的拉流地址
    cameraLocation: 摄像头的经纬度坐标，存储为字符串格式
    cameraName: 摄像头名称
    """
    __tablename__ = "camera"

    id = Column(String, primary_key=True, index=True)
    cameraURL = Column(String, nullable=False)
    cameraLocation = Column(String, nullable=False)  # 存储 ["经度", "纬度"]
    cameraName = Column(String, nullable=False)

    #反向关系：一个摄像头可以有多个规则
    rules = relationship("CameraRule", back_populates="camera")
