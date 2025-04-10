from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from dependencies.database import Base

# 主表：摄像头规则
class CameraRule(Base):
    __tablename__ = "camera_rule"

    rule_id = Column(String, primary_key=True, index=True)
    camera_id = Column(String,ForeignKey("camera.id"), index=True)
    rule_value = Column(String)  # 1: 车类别, 2: 车拥堵, 3: 车流量, 4: 预约, 5: 事故检测

# 分表1：规则1，车辆类别
class CameraRule1(Base):
    __tablename__ = "camera_rule_1"

    rule_id = Column(String, primary_key=True, index=True)
    labels = Column(String)  # 假定存储的是 JSON 串，比如：{"labelId": ["l1", "l2"], "cameraLineId": "line1"}

# 分表2：规则2，车拥堵情况（车辆停留检测）
class CameraRule2(Base):
    __tablename__ = "camera_rule_2"

    rule_id = Column(String, primary_key=True, index=True)
    max_vehicle_hold_num = Column(String)
    min_vehicle_hold_num = Column(String)
    max_continuous_time_period = Column(String)  # 虽然建表中为 TEXT
    min_continuous_time_period = Column(String)
    Labels_equal = Column(String)  # 建议存储为 JSON 串，格式为 [{"labelId": "xxx", "labelHoldNum": "1.5"}, ...]

# 分表3：规则3，车流量情况
class CameraRule3(Base):
    __tablename__ = "camera_rule_3"

    rule_id = Column(String, primary_key=True, index=True)
    max_vehicle_flow_num = Column(String)
    min_vehicle_flow_num = Column(String)
    max_continuous_time_period = Column(String)
    min_continuous_time_period = Column(String)
    labels_equal = Column(String)  # JSON 串，格式同上
    camera_start_line = Column(String)  # 存储 JSON 数据，如 {"cameraLineId": "line1", "isAll": true}
    camera_end_line = Column(String)    # 存储 JSON 数据，如 {"cameraLineId": "line2", "isAll": false}

# 分表4：规则4，预约车辆检测
class CameraRule4(Base):
    __tablename__ = "camera_rule_4"

    rule_id = Column(String, primary_key=True, index=True)
    vehicle_reserve = Column(Integer)  # 1 表示开启，0 表示关闭

# 分表5：规则5，事故检测
class CameraRule5(Base):
    __tablename__ = "camera_rule_5"

    rule_id = Column(String, primary_key=True, index=True)
    event_detect = Column(Integer)  # 1 表示开启，0 表示关闭
