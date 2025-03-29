import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from dependencies.database import Base


class CarThroughRoute(Base):
    __tablename__ = 'car_through_route'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_no = Column(String, nullable=False, index=True)     # 车辆编号
    vehicle_type = Column(String, nullable=False)               # 车辆类型
    start_line = Column(String, nullable=False)                 # 起始检测线ID
    end_line = Column(String, nullable=False)                   # 终止检测线ID
    detection_time = Column(DateTime, nullable=False)           # 检测时间
    direction = Column(String, nullable=False)                  # 车辆方向