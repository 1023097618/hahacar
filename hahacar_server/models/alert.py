import datetime

from sqlalchemy import Column, String, Integer, JSON, Float, DateTime, ForeignKey

from dependencies.database import Base

#预警信息
class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    camera_name = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # 1: 进行中, 2: 已发生, 3: 已结束
    alert_start_time = Column(DateTime, nullable=False)
    alert_end_time = Column(DateTime, nullable=True)
    alert_processed_time = Column(DateTime, nullable=True)
    alert_image = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    rule_remark = Column(String, nullable=False)
    alert_num = Column(Integer, nullable=False)
