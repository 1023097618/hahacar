from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, String


class CameraLineUpdate(BaseModel):
    cameraLineName: str = Field(..., description="摄像头检测线名称，可能会叫’成化大道方向‘")
    cameraLineStartX: str = Field(..., description="摄像头检测线起始点的X轴，从左往右占了整个宽度的多少")
    cameraLineStartY: str = Field(..., description="摄像头检测线起始点的Y轴，从下往上占了整个高度的多少")
    cameraLineEndX: str = Field(..., description="摄像头检测线终止点的X轴，从左往右占了整个宽度的多少")
    cameraLineEndY: str = Field(..., description="摄像头检测线终止点的Y轴，从下往上占了整个高度的多少")
    pointCloseToLine: List[str] = Field(..., description="从地图上的哪个点到摄像头过来离这条检测线最近，该数组由两个浮点数性质的字符串组成，如[经度,维度],比如说['116.368904','39.913423']")
    isMainLine: bool = Field(..., description="是否是主要检测线，如果是的话就以这个检测线为准计算通过这个摄像头的整体流量以及这个摄像头整体的车辆类型，’主要检测线‘在所有检测线中只能存在一条")
    cameraLineId: Optional[str] = Field(..., description="摄像头检测线ID")
    class Config:
        orm_mode = True

class CameraLineUpdateRequest(BaseModel):
    cameraLines: List[CameraLineUpdate]
    camera_id: str = Field(..., alias="cameraId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class CameraLineGet(BaseModel):
    line_name: str = Field(..., description="摄像头检测线名称，可能会叫’成化大道方向‘")
    start_x: str = Field(..., description="摄像头检测线起始点的X轴，从左往右占了整个宽度的多少")
    start_y: str = Field(..., description="摄像头检测线起始点的Y轴，从下往上占了整个高度的多少")
    end_x: str = Field(..., description="摄像头检测线终止点的X轴，从左往右占了整个宽度的多少")
    end_y: str = Field(..., description="摄像头检测线终止点的Y轴，从下往上占了整个高度的多少")
    point_close_to_line: List[str] = Field(..., description="从地图上的哪个点到摄像头过来离这条检测线最近，该数组由两个浮点数性质的字符串组成，如[经度,维度],比如说['116.368904','39.913423']")
    is_main_line: bool = Field(..., description="是否是主要检测线，如果是的话就以这个检测线为准计算通过这个摄像头的整体流量以及这个摄像头整体的车辆类型，’主要检测线‘在所有检测线中只能存在一条")
    camera_line_id: str = Field(..., description="摄像头检测线ID")
    class Config:
        orm_mode = True