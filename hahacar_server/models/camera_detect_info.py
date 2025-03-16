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

    detected_cars_labels = Column(JSON) #包含labelName和labelNum的用于记录一段时间内所有车的类别和不同类别车的数量的json数据
    detected_hold_time = Column(DateTime, default=datetime.datetime.utcnow)
    detected_hold_num = Column(String)

    camera_line_id_start = Column(String,nullable = True)   #可选参数，一个id，从哪个起始线驶入的，没有指定就是所有其他线驶入的都算
    camera_line_id_end = Column(String,nullable = True)     #可选参数，一个id，从哪个结束线驶出的，没有指定就是所有其他线驶出的都算
    camera_line_id = Column(String, nullable = True)    #可选参数，只记录某个检测线驶入驶出的交通量，和驶入起始线和驶出起始线相矛盾

    detected_flow_time = Column(DateTime, default=datetime.datetime.utcnow) #记录哪一段时间内所有车的总流量
    detected_flow_num = Column(String)  #记录一段时间内所有车的总流量

