import uuid
from datetime import datetime, timedelta
from urllib.parse import unquote

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.camera_line import CameraLine
from models.camera_detect_info import camera_detect_info
from models.CarThroughRoute import CarThroughRoute
from models.camera_rule import CameraRule
from models.vehicle_labels import VehicleLabel
from schemas.camera_detect_schema import *

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""


def save_to_camera_detect_info(db:Session, camera_id, avg_hold_volume, avg_flow_volume, aggregated_label_counts,timestamp):
    """
    **description** 将计算出的交通当量存入数据库

    **params**
    - db (Session): 数据库会话
    - camera_id (str): 摄像头 ID
    - avg_hold_volume (float): 10 秒内的平均拥堵量
    - avg_flow_volume (float): 10 秒内的平均车流量
    - vehicle_counts (dict): 10 秒内每种车辆类型的累计数量
    - timestamp (float): 时间戳

    **returns** 无
    """
    new_record = camera_detect_info(
        camera_detect_info_id=str(uuid.uuid4()),
        camera_id=camera_id,
        detected_hold_time = datetime.utcfromtimestamp(timestamp),
        detected_hold_num=avg_hold_volume,

        detected_flow_num=avg_flow_volume,
        detected_flow_time = datetime.utcfromtimestamp(timestamp),

        detected_cars_labels=aggregated_label_counts,

        #检测线还有——————————————————-------

        created_at= datetime.utcnow()
    )
    db.add(new_record)
    db.commit()
    print(
        f"[✅] 交通数据已存入数据库: 摄像头 {camera_id}, 拥堵: {avg_hold_volume}, 车流: {avg_flow_volume}, 车辆计数: {aggregated_label_counts}, 时间: {timestamp}")



# def save_vehicle_labels(db:Session,request: VehicleLabelSaveRequest):
#     new_data = camera_detect_info(
#         camera_id=request.cameraId,
#         #detected_cars_label是包含labelName和labelNum的用于记录一段时间内所有车的类别和不同类别车的数量的json数据
#         detected_cars_labels=request.detected_cars_labels,
#         created_at=datetime.utcnow()
#     )
#     db.add(new_data)
#     db.commit()
#     return {"code": "200", "msg": "save success", "data": {}}
#
# def save_traffic_hold(db:Session, request: TrafficHoldSaveRequest):
#     new_data = camera_detect_info(
#         camera_id=request.cameraId,
#         detected_hold_num=request.holdNum,
#         detected_hold_time=datetime.utcnow(),
#         created_at=datetime.utcnow()
#     )
#     db.add(new_data)
#     db.commit()
#     return {"code": "200", "msg": "save success", "data": {}}
#
# def save_traffic_flow(db:Session,request: TrafficFlowSaveRequest):
#     new_data = camera_detect_info(
#         camera_id=request.cameraId,
#         detected_flow_num=request.flowNum,
#         detected_flow_time=datetime.utcnow(),
#         created_at=datetime.utcnow()
#     )
#     db.add(new_data)
#     db.commit()
#     return {"code": "200", "msg": "save success", "data": {}}

def parse_db_datetime(dt_value):
    """
    如果 dt_value 为字符串，尝试按预期格式解析。
    如果已经是 datetime 对象，直接返回。
    """
    if isinstance(dt_value, datetime):
        return dt_value
    if isinstance(dt_value, str):
        try:
            # 如果字符串是 ISO 格式，可以直接解析
            return datetime.fromisoformat(dt_value)
        except ValueError:
            # 如果不是 ISO 格式，尝试使用指定格式解析
            return datetime.strptime(dt_value, "%b %d, %Y, %I:%M:%S %p")
    return None


"""
    ***查询车辆类别、车流量、车拥挤度逻辑***
    没实现：
    需要传回数据每个间隔1h，如果我选择每分钟取平均存储一次，则需要间隔1min
"""



def get_traffic_flow(db: Session,request: GetTrafficFlowRequest):
    # **如果 cameraLineId、cameraLineIdStart、cameraLineIdEnd 未提供，则不对检测线做限制**
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_flow_time.label("flowTime")),
        func.avg(camera_detect_info.detected_flow_num.label("flowNum"))
    )

    if request.timeFrom:
        decoded_time_from = unquote(request.timeFrom)
        query = query.filter(
            camera_detect_info.detected_flow_time >= datetime.strptime(decoded_time_from, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        decoded_time_to = unquote(request.timeTo)
        query = query.filter(
            camera_detect_info.detected_flow_time <= datetime.strptime(decoded_time_to, "%Y-%m-%d %H:%M:%S"))
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

    formatted_results = []
    for record in results:
        flow_time = record[0]
        # 如果没有数据则视为 0
        avg_flow = record[1] if record[1] is not None else 0
        # 将平均流量转换为 int（这里采用四舍五入）
        avg_flow_int = int(round(avg_flow))
        if avg_flow_int == 0:
            continue
        formatted_results.append({
            "flowTime": flow_time,
            "flowNum": avg_flow_int
        })

    return {"code": "200", "msg": "success", "data": {"flows": formatted_results}}

def get_traffic_flow_mat(db: Session, request: GetTrafficFlowMatRequest):
    # Step 1: Retrieve detection lines for the given cameraId
    camera_lines = db.query(CameraLine).filter(CameraLine.camera_id == request.cameraId).all()
    if not camera_lines:
        return {"code": "404", "msg": "No camera lines found for given cameraId", "data": {}}
    # Sort the detection lines (here by their id, adjust as needed)
    camera_lines = sorted(camera_lines, key=lambda cl: cl.camera_line_id)

    # Step 2: Retrieve vehicle labels in order
    labels = db.query(VehicleLabel).order_by(VehicleLabel.label_id).all()

    # Determine dimensions for the matrix
    num_lines = len(camera_lines)
    num_labels = len(labels)

    # Step 3: Initialize the flow matrix (3D list) with zeros (using float for further processing)
    flowmat = [[[0.0 for _ in range(num_labels)] for _ in range(num_lines)] for _ in range(num_lines)]

    # Build lookup dictionaries for index mapping
    line_index = {cl.camera_line_id: idx for idx, cl in enumerate(camera_lines)}
    label_index = {label.label_id: idx for idx, label in enumerate(labels)}

    # Step 4: Query vehicle flow records (CarThroughRoute) with time filters only
    query = db.query(CarThroughRoute)

    if request.timeFrom:
        time_from = datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S")
        query = query.filter(CarThroughRoute.detection_time >= time_from)
    if request.timeTo:
        time_to = datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S")
        query = query.filter(CarThroughRoute.detection_time <= time_to)

    car_routes = query.all()

    # Step 4.1: Query CameraRule for vehicle flow (rule_value "3") for the given camera
    camera_rule = db.query(CameraRule).filter(
        CameraRule.camera_id == request.cameraId,
        CameraRule.rule_value == "3"
    ).first()

    # Build the multiplier mapping from labels_equal_flow_ids
    multiplier_mapping = {}
    if camera_rule and camera_rule.labels_equal_flow_ids:
        try:
            # If stored as string, parse it as JSON; otherwise assume it's already a JSON object
            if isinstance(camera_rule.labels_equal_flow_ids, str):
                labels_flow = json.loads(camera_rule.labels_equal_flow_ids)
            else:
                labels_flow = camera_rule.labels_equal_flow_ids
            for item in labels_flow:
                multiplier_mapping[item['labelId']] = float(item['labelEqualNum'])
        except Exception as e:
            # In case of error, fallback to no multipliers (i.e. default to 1.0)
            multiplier_mapping = {}

    # Step 5: Accumulate weighted counts in the matrix based on each record's start_line, end_line, and vehicle_type
    for route in car_routes:
        # Ensure the start_line, end_line, and vehicle_type exist in our lookup dictionaries
        if (route.start_line in line_index and
            route.end_line in line_index and
            route.vehicle_type in label_index):

            i = line_index[route.start_line]   # index for start_line
            j = line_index[route.end_line]       # index for end_line
            k = label_index[route.vehicle_type]  # index for vehicle type (label)

            # Use multiplier if available; otherwise default to 1.0
            multiplier = multiplier_mapping.get(route.vehicle_type, 1.0)
            flowmat[i][j][k] += multiplier

    # Step 6: Format the matrix values to strings with one decimal place
    flowmat_str = [[[f"{flowmat[i][j][k]:.1f}" for k in range(num_labels)]
                     for j in range(num_lines)]
                     for i in range(num_lines)]

    # Prepare the camera lines and labels in the desired output format
    camera_lines_res = [{"cameraLineName": cl.line_name, "cameraLineId": cl.camera_line_id}
                          for cl in camera_lines]
    labels_res = [{"labelName": label.label_name, "labelId": label.label_id} for label in labels]

    # Return the response structure as described in the API documentation
    return {
        "code": "200",
        "msg": "Success",
        "data": {
            "flowmat": flowmat_str,
            "cameraLines": camera_lines_res,
            "labels": labels_res
        }
    }




def get_traffic_hold(db: Session,request: GetTrafficHoldRequest):
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00', camera_detect_info.detected_hold_time).label("holdTime"),
        func.avg(camera_detect_info.detected_hold_num.label("holdNum"))
    )

    if request.timeFrom:
        decoded_time_from = unquote(request.timeFrom)
        query = query.filter(camera_detect_info.detected_hold_time >= datetime.strptime(decoded_time_from, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        decoded_time_to = unquote(request.timeTo)
        query = query.filter(camera_detect_info.detected_hold_time <= datetime.strptime(decoded_time_to, "%Y-%m-%d %H:%M:%S"))
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
        decoded_time_from = unquote(request.timeFrom)
        query = query.filter(camera_detect_info.created_at >= datetime.strptime(decoded_time_from, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        decoded_time_to = unquote(request.timeTo)
        query = query.filter(camera_detect_info.created_at <= datetime.strptime(decoded_time_to, "%Y-%m-%d %H:%M:%S"))
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