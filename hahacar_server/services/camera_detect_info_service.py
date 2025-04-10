import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import unquote
from sqlalchemy import or_, true
from sqlalchemy import func, text, Integer, cast, String
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.camera import Camera
from models.camera_line import CameraLine
from models.camera_detect_info import camera_detect_info
from models.CarThroughRoute import CarThroughRoute
from models.camera_rule import CameraRule
from models.vehicle_labels import VehicleLabel
from schemas.camera_detect_schema import *
from util import timeutil
from util.timeutil import parse_frontend_time

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""


def save_to_camera_detect_info(db:Session, camera_id, aggregated_label_counts,timestamp):
    """
    **description** 将计算出的交通当量存入数据库

    **params**
    - db (Session): 数据库会话
    - camera_id (str): 摄像头 ID
    - aggregated_label_counts (dict): 每60秒存一次的瞬时车辆标签数量(后面会考虑改成平均)
    - timestamp (float): 时间戳

    **returns** 无
    """
    created_time = datetime.utcnow()
    new_record = camera_detect_info(
        camera_detect_info_id=str(uuid.uuid4()),
        camera_id=camera_id,
        detected_hold_time = timeutil.get_utc_datetime_from_timestamp(timestamp),

        detected_cars_labels=aggregated_label_counts,
        created_at= timeutil.get_utc_datetime_from_timestamp(created_time)
    )
    db.add(new_record)
    db.commit()
    print(
        f"[✅] 交通数据已存入数据库: 摄像头 {camera_id}, 车辆计数: {aggregated_label_counts}, 时间: {timestamp}")



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


# TODO 这边没有考虑用户的摄像头权限，后面补

# 你要做的任务是根据前端传过来的request来返回相关的车流数据，30分钟为聚类统计
# 这是你要返回的数据格式
#         [{
#             "flowTime": flow_time,
#             "flowNum": avg_flow_int
#         }]
#flowTime为你聚类的开始时间
# 这是摄像头表
# create table camera
# (
#     id             TEXT
#         primary key,
#     cameraURL      TEXT not null,
#     cameraLocation TEXT not null,
#     cameraName     TEXT not null
# );
# 这是一张摄像头检测线表
# create table camera_lines
# (
#     camera_line_id      TEXT
#         primary key,
#     camera_id           TEXT,
#     line_name           TEXT,
#     start_x             TEXT,
#     start_y             TEXT,
#     end_x               TEXT,
#     end_y               TEXT,
#     point_close_to_line TEXT,
#     created_at          DATETIME default CURRENT_TIMESTAMP,
#     is_main_line        BOOLEAN  default 0
# );
# 这是一个车流量记录的表
# create table car_through_route
# (
#     id             INTEGER
#         primary key autoincrement,
#     vehicle_no     TEXT     not null,
#     vehicle_type   TEXT     not null,
#     start_line     TEXT     not null,
#     end_line       TEXT,
#     detection_time DATETIME not null,
#     camera_id      TEXT     not null
# );
# 这是前端传过来的GetTrafficFlowRequest的数据结构
# class GetTrafficFlowRequest(BaseModel):
#     timeFrom: Optional[str]
#     timeTo: Optional[str]
#     cameraId: Optional[str]
#     cameraLineIdStart: Optional[str]
#     cameraLineIdEnd: Optional[str]
#     cameraLineId: Optional[str]
#   其中timeFrom是开始统计时间，timeTo是结束统计时间，cameraId是当前摄像头的id，cameraLineIdStart指车辆是从哪个检测线驶入的
#   ，cameraLineIdEnd指车辆是从哪个检测线驶出的，cameraLineId如果传过来cameraLineIdStart和cameraLineIdEnd就不传过来
#   ，意思代表统计cameraLineId驶入驶出的值。如果没有指定cameraId，则从数据库中查询所有的摄像头id，然后查询这些摄像头id对应的主要
#   检测线，然后按时间相加聚类。如果只指定了cameraId，剩下三个lineId都没指定，则只以这个cameraId的主要检测线算它驶入驶出的值。
#   这个函数已经定义def parse_frontend_time(time_str: str) -> datetime.datetime:使用它来进行时间的转换
#   函数的第一行已经给出
#   直接根据vehicle_labels中的default_value来算吧
def get_traffic_flow(db: Session, request: GetTrafficFlowRequest) -> List[dict]:
    # 解析传入的时间
    time_from = parse_frontend_time(request.timeFrom) if request.timeFrom else None
    time_to = parse_frontend_time(request.timeTo) if request.timeTo else None

    # 构造用于分组的时间表达式
    # 先取出形如 "2025-04-10 20:" 的前半部分
    base_time = func.strftime('%Y-%m-%d %H:', CarThroughRoute.detection_time)
    # 提取分钟部分，转换为整数后除以30取整再乘30，得到该时间所在的30分钟段（例如：若分钟为55则 floor(55/30)=1, 1*30=30）
    minutes_interval = func.floor(cast(func.strftime('%M', CarThroughRoute.detection_time), Integer) / 30) * 30
    # 使用 SQLite 的字符串拼接运算符 || 拼接成完整的时间字符串
    minutes_interval_padded = func.printf('%02d:00', minutes_interval)
    flow_time_expr = base_time.op("||")(minutes_interval_padded)

    # 构造查询，选择聚合时间和数量
    car_query = db.query(
        flow_time_expr.label('flow_time'),
        func.sum(VehicleLabel.default_equal).label('flow_count')
    ).join(VehicleLabel,VehicleLabel.label_name==CarThroughRoute.vehicle_type)

    # 根据时间范围过滤
    if time_from and time_to:
         car_query = car_query.filter(
             CarThroughRoute.detection_time >= time_from,
             CarThroughRoute.detection_time <= time_to
         )

    # 处理 cameraId 与 cameraLine 的过滤逻辑
    if request.cameraId:
        car_query = car_query.filter(CarThroughRoute.camera_id == request.cameraId)
        # 如果没有传入具体的 lineId，则只以该摄像头的主检测线进行统计
        if not (request.cameraLineId or request.cameraLineIdStart or request.cameraLineIdEnd):
            subq = (db.query(CameraLine.camera_line_id).filter(
                CameraLine.camera_id == request.cameraId,
                CameraLine.is_main_line == True
            ).subquery())
            car_query = car_query.filter(
                CarThroughRoute.start_line.in_(subq) |
                CarThroughRoute.end_line.in_(subq)
            )
    else:
        # 如果未指定摄像头，则以所有摄像头的主检测线进行统计
        subq = (db.query(CameraLine.camera_line_id).where(CameraLine.is_main_line == True).subquery())
        car_query = car_query.filter(
            CarThroughRoute.start_line.in_(subq) |
            CarThroughRoute.end_line.in_(subq)
        )

    # 如果传入了具体的 lineId，按传入的过滤
    if request.cameraLineId:
         car_query = car_query.filter(
             or_(CarThroughRoute.start_line == request.cameraLineId
                 ,CarThroughRoute.end_line == request.cameraLineId))

    if request.cameraLineIdStart and request.cameraLineIdEnd:
         # 使用 start_line 与 end_line 对应过滤
         car_query = car_query.filter(
            CarThroughRoute.start_line == request.cameraLineIdStart,
            CarThroughRoute.end_line == request.cameraLineIdEnd
         )

    # 按照构造的 flow_time 分组，统计每个30分钟区间的记录
    car_query = car_query.group_by('flow_time')
    traffic_flow_data = car_query.all()

    # 格式化返回结果
    result = []
    for flow_time, flow_count in traffic_flow_data:
         result.append({
             "flowTime": flow_time,  # 现在 flow_time 是完整的时间字符串
             "flowNum": flow_count
         })

    return result

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
    label_index = {label.label_name: idx for idx, label in enumerate(labels)}

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

    # # Build the multiplier mapping from labels_equal_flow_ids
    # multiplier_mapping = {}
    # if camera_rule and camera_rule.labels_equal_flow_ids:
    #     try:
    #         # If stored as string, parse it as JSON; otherwise assume it's already a JSON object
    #         if isinstance(camera_rule.labels_equal_flow_ids, str):
    #             labels_flow = json.loads(camera_rule.labels_equal_flow_ids)
    #         else:
    #             labels_flow = camera_rule.labels_equal_flow_ids
    #         for item in labels_flow:
    #             multiplier_mapping[item['labelId']] = float(item['labelEqualNum'])
    #     except Exception as e:
    #         # In case of error, fallback to no multipliers (i.e. default to 1.0)
    #         multiplier_mapping = {}
    multiplier_mapping = {label.label_name:float(label.default_equal) for label in labels}

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
    time_from = parse_frontend_time(request.timeFrom) if request.timeFrom else None
    time_to = parse_frontend_time(request.timeTo) if request.timeTo else None

    # 构造用于分组的时间表达式
    # 先取出形如 "2025-04-10 20:55:" 的前半部分
    base_time = func.strftime('%Y-%m-%d %H:', camera_detect_info.detected_hold_time)
    # 提取分钟部分，转换为整数后除以30取整再乘30，得到该时间所在的30分钟段（例如：若分钟为55则 floor(55/30)=1, 1*30=30）
    minutes_interval = func.floor(cast(func.strftime('%M', camera_detect_info.detected_hold_time), Integer) / 30) * 30
    # 使用 SQLite 的字符串拼接运算符 || 拼接成完整的时间字符串
    minutes_interval_padded = func.printf('%02d:00', minutes_interval)
    hold_time_expr = base_time.op("||")(minutes_interval_padded)

    j = func.json_each(camera_detect_info.detected_cars_labels).table_valued("key", "value")  # 解析JSON

    car_query = db.query(
            hold_time_expr.label("hold_time"),
            func.sum(
                j.c.value.cast(Integer) * VehicleLabel.default_equal
            ).label("hold_count")
    ).join(VehicleLabel, VehicleLabel.label_name == j.c.key).join(j, true())

    if time_from and time_to:
         car_query = car_query.filter(
             camera_detect_info.detected_hold_time >= time_from,
             camera_detect_info.detected_hold_time <= time_to
         )
    elif time_from:
         car_query = car_query.filter(
             camera_detect_info.detected_hold_time >= time_from
         )
    elif time_to:
         car_query = car_query.filter(
             camera_detect_info.detected_hold_time <= time_to
         )
    if request.cameraId:
        car_query = car_query.filter(camera_detect_info.camera_id == request.cameraId)

    car_query = car_query.group_by("hold_time").order_by("hold_time")
    traffic_hold_data = car_query.all()
    result = []
    for hold_time, hold_count in traffic_hold_data:
         result.append({
             "holdTime": hold_time,  # 现在 hold_time 是完整的时间字符串
             "holdNum": hold_count
         })

    return result


def get_vehicle_labels(db: Session,request: GetVehicleLabelRequest):
    query = db.query(camera_detect_info.detected_cars_labels).filter(camera_detect_info.detected_cars_labels !=None)
    if request.timeFrom:
        decoded_time_from = timeutil.parse_frontend_time(request.timeFrom)
        query = query.filter(
            camera_detect_info.detected_hold_time >= decoded_time_from)
    if request.timeTo:
        decoded_time_to = timeutil.parse_frontend_time(request.timeTo)
        query = query.filter(
            camera_detect_info.detected_hold_time <= decoded_time_to)
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

    valid_labels = [label[0] for label in db.query(VehicleLabel.label_name).all()]
    # 做一次过滤，仅仅返回vehicle_labels中的值
    formatted_results = [{"labelName": label, "labelNum": str(num)} for label, num in results.items() if label in valid_labels]

    return formatted_results