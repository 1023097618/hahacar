import datetime

from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import relationship

from dependencies.database import Base
from models.vehicle_labels import VehicleLabel

#这里用于计算车的类型、拥挤度和车流量，可在一段时间(固定时间间隔)内求平均后保存在数据库中
class camera_detect_info(Base):
    __tablename__ = "camera_detect_info"

    camera_detect_info_id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    detected_cars_labels = Column(JSON) #包含labelName和labelNum的用于记录当前帧所有【车的类别和该类别车的数量】的json数据

    detected_hold_time = Column(DateTime, default=datetime.datetime.utcnow)

