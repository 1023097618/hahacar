from pydantic import BaseModel
from typing import List

class CameraCreate(BaseModel):
    """
    **description**
    添加摄像头请求模型
    """
    cameraURL: str
    cameraLocation: List[str]  # 经纬度坐标 ["经度", "纬度"]
    cameraName: str

class CameraUpdate(BaseModel):
    """
    **description**
    更新摄像头请求模型
    """
    cameraId: str
    cameraURL: str
    cameraLocation: List[str]
    cameraName: str

class CameraDelete(BaseModel):
    """
    **description**
    删除摄像头请求模型
    """
    cameraId: str

class CameraResponse(BaseModel):
    """
    **description**
    摄像头返回模型
    """
    cameraId: str
    cameraURL: str
    cameraLocation: List[str]
    cameraName: str

class CameraListResponse(BaseModel):
    """
    **description**
    摄像头列表返回模型
    """
    cameras: List[CameraResponse]
    cameraNum: int
