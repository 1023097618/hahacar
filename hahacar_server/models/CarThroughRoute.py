from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CarThroughRoute(Base):
    __tablename__ = "car_through_route"  # 或者 "CarThroughRoute"，与上面 CREATE TABLE 保持一致


    id = Column(Integer,  autoincrement=True)   #模型识别出来的载具id
    vehicle_no = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    start_line = Column(String, nullable=False)
    end_line = Column(String, nullable=False)
    detection_time = Column(DateTime, nullable=False)
    camera_id = Column(String, nullable=False)
    auto_id = Column(Integer, nullable=False,primary_key=True)  #自增字段
