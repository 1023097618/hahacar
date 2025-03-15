import datetime
from sqlalchemy import Column, String, Integer, JSON, Float, DateTime, ForeignKey
from dependencies.database import Base

class CameraRule(Base):
    __tablename__ = "camera_rules"

    id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("camera.id"),index=True)
    rule_value = Column(Integer)  # 1: 车类别, 2: 车拥堵, 3: 车流量
    label_ids = Column(JSON, nullable=True)  # 仅 rule_value=1 时适用,包含labelID
    max_vehicle_hold_num = Column(Float, nullable=True)  # 仅 rule_value=2 时适用
    min_vehicle_hold_num = Column(Float, nullable=True)  # 仅 rule_value=2 时适用
    max_continuous_time_period = Column(Integer, nullable=True)  # 适用于 2 和 3
    min_continuous_time_period = Column(Integer, nullable=True)  # 适用于 2 和 3
    max_vehicle_flow_num = Column(Float, nullable=True)  # 仅 rule_value=3 时适用
    min_vehicle_flow_num = Column(Float, nullable=True)  # 仅 rule_value=3 时适用
    camera_start_line_id = Column(String, ForeignKey("camera_line.camera_line_id"),nullable=True) #和camera_line表关联
    camera_end_line_id = Column(String, ForeignKey("camera_line.camera_line_id"), nullable=True)  # 和camera_line表关联
    created_at = Column(DateTime, default=datetime.utcnow)
    labels_equal_hold_ids = Column(JSON, nullable=True) # 仅 rule_value=2 时适用，包含labelId以及labelHoldNum的json字符串,代表本labelId可以视为多少个交通当量
    labels_equal_flow_ids = Column(JSON, nullable=True) # 仅 rule_value=3 时适用,包含labelId以及labelFlowNum的json字符串,代表本labelId可以视为多少个交通当量
