from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.camera_line import CameraLine
from models.camera_detect_info import camera_detect_info
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
    # **如果 cameraLineId、cameraLineIdStart、cameraLineIdEnd 未提供，则查找 is_main_line=True 的检测线**
    if not request.cameraLineId and not request.cameraLineIdStart and not request.cameraLineIdEnd:
        main_line = db.query(CameraLine.camera_line_id).filter(CameraLine.is_main_line == True).first()
        if main_line:
            request.cameraLineId = main_line[0]  # 获取 `camera_line_id`

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

    query = query.group_by(func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_flow_time))
    query = query.order_by(func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_flow_time))

    results = query.all()

    formatted_results = [{"flowTime": record[0], "flowNum": str(record[1] if record[1] is not None else "0")} for record
                         in results]

    return {"code": "200", "msg": "success", "data": {"flows": formatted_results}}

def get_traffic_hold(db: Session,request: GetTrafficHoldRequest):
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_hold_time).label("holdTime"),
        func.avg(camera_detect_info.detected_hold_num.label("holdNum"))
    )

    if request.timeFrom:
        query = query.filter(camera_detect_info.detected_hold_time >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(camera_detect_info.detected_hold_time <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(camera_detect_info.camera_id == request.cameraId)

    # **使用 text() 避免 SQLAlchemy 解析错误**
    query = query.group_by(text("holdTime")).order_by(text("holdTime"))     #字符串形式的列名不能直接用于groupby和orderby，需要text进行显式声明
    results = query.all()

    # **格式化返回数据**
    formatted_results = [{"holdTime": record[0], "holdNum": str(record[1] if record[1] is not None else "0")} for record
                         in results]

    return {"code": "200", "msg": "success", "data": {"holds": formatted_results}}

def get_vehicle_labels(db: Session,request: GetVehicleLabelRequest):
    query = db.query(camera_detect_info.detected_cars_labels).filter(camera_detect_info.detected_cars_labels !=None)
    if request.timeFrom:
        query = query.filter(camera_detect_info.created_at >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(camera_detect_info.created_at <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(camera_detect_info.camera_id == request.cameraId)

    results = {}
    # **处理查询结果**
    for record in query.all():
        detected_labels = record[0]  # 取出 detected_cars_labels 字段（JSON 格式）

        if not detected_labels:
            continue  # 跳过空数据

        # **确保 detected_labels 是字典**
        if isinstance(detected_labels, str):
            try:
                detected_labels = json.loads(detected_labels)  # 解析 JSON
            except json.JSONDecodeError:
                print(f"无法解析 JSON: {detected_labels}")
                continue  # 跳过错误数据

        if isinstance(detected_labels, dict):
            for label, num in detected_labels.items():
                if label in results:
                    results[label] += num  # 累加相同类别的数量
                else:
                    results[label] = num

    # **格式化返回数据**
    formatted_results = [{"labelName": label, "labelNum": str(num)} for label, num in results.items()]

    return {
        "code": "200",
        "msg": "success",
        "data": {
            "labels": formatted_results
        }
    }