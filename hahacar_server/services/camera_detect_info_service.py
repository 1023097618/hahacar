from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.camea_detect_info import camera_detect_info
from schemas.camera_detect_schema import *

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""
def save_vehicle_labels(db:Session,request: VehicleLabelSaveRequest):
    new_data = camera_detect_info(
        camera_id=request.cameraId,
        #detected_cars_label是包含labelName和labelNum的用于记录一段时间内所有车的类别和不同类别车的数量的json数据
        detected_cars_labels=request.detected_cars_labels,
        created_at=datetime.utcnow()
    )
    db.add(new_data)
    db.commit()
    return {"code": "200", "msg": "save success", "data": {}}

def save_traffic_hold(db:Session, request: TrafficHoldSaveRequest):
    new_data = camera_detect_info(
        camera_id=request.cameraId,
        detected_hold_num=request.holdNum,
        detected_hold_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(new_data)
    db.commit()
    return {"code": "200", "msg": "save success", "data": {}}

def save_traffic_flow(db:Session,request: TrafficFlowSaveRequest):
    new_data = camera_detect_info(
        camera_id=request.cameraId,
        detected_flow_num=request.flowNum,
        detected_flow_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(new_data)
    db.commit()
    return {"code": "200", "msg": "save success", "data": {}}


"""
    ***查询车辆类别、车流量、车拥挤度逻辑***
    没实现：
    需要传回数据每个间隔1h，如果我选择每分钟取平均存储一次，则需要间隔1min
"""



def get_traffic_flow(db: Session,request: GetTrafficFlowRequest):
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_flow_time.label("flowTime")),
        func.avg(camera_detect_info.detected_flow_num.label("flowNum"))
    )

    if request.timeFrom:
        query = query.filter(camera_detect_info.detected_flow_time >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(camera_detect_info.detected_flow_time <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(camera_detect_info.camera_id == request.cameraId)
    if request.cameraLineId:
        query = query.filter(camera_detect_info.camera_line_id == request.cameraLineId)
    if request.cameraLineIdStart:
        query = query.filter(camera_detect_info.camera_line_id_start == request.cameraLineIdStart)
    if request.cameraLineIdEnd:
        query = query.filter(camera_detect_info.camera_line_id_end == request.cameraLineIdEnd)
    query = query.group_by('flowTime').order_by('flowTime')
    flows = query.all()
    return {"code": "200", "msg": "success", "data": {"flows": flows}}

def get_traffic_hold(db: Session,request: GetTrafficHoldRequest):
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_hold_time.label("holdTime")),
        func.avg(camera_detect_info.detected_hold_num.label("holdNum"))
    )

    if request.timeFrom:
        query = query.filter(camera_detect_info.detected_hold_time >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(camera_detect_info.detected_hold_time <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(camera_detect_info.camera_id == request.cameraId)

    query = query.group_by("holdTime").order_by("holdTime")
    results = query.all()

    return {"code": "200", "msg": "success", "data": {"holds": results}}

def get_vehicle_labels(db: Session,request: GetVehicleLabelRequest):
    query = db.query(camera_detect_info.detected_cars_labels).filter(camera_detect_info.detected_cars_labels !=None)
    if request.timeFrom:
        query = query.filter(camera_detect_info.created_at >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(camera_detect_info.created_at <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(camera_detect_info.camera_id == request.cameraId)

    results = []
    for record in query.all():
        results.extend(record[0])   #json数据是数组

    return {"code": "200", "msg": "success", "data": {"labels": results}}