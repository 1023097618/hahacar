import datetime

from sqlalchemy import Column, String, Integer, JSON, Float, DateTime, Boolean

from dependencies.database import Base

# 摄像头检测线相关信息，前端可以划线传回后端
class CameraLine(Base):
    __tablename__ = "camera_lines"

    #前后端通讯的时候同一条线的起始点和终点是一样的，没有设置则应有一个默认值
    camera_line_id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    line_name = Column(String)
    start_x = Column(String,description = "摄像头检测线起始点的X轴，从左往右占了整个宽度的多少")
    start_y = Column(String,description = "摄像头检测线起始点的Y轴，从下往上占了整个高度的多少")
    end_x = Column(String)
    end_y = Column(String,description = "车从地图上的哪个点到摄像头过来离这条检测线最近，[经度，维度]")
    point_close_to_line = Column(JSON)  # 记录 [经度, 纬度]
    created_at = Column(DateTime, default=datetime.utcnow)
    is_main_line = Column(Boolean, default=False,description="是否是主要检测线，如果是的话就以这个检测线为准计算通过这个摄像头的整体流量以及这个摄像头整体的车辆类型，’主要检测线‘在所有检测线中只能存在一条")