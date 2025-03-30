import asyncio
import json
import os
import traceback
import uuid
from datetime import datetime

import cv2
import time

import numpy as np
import requests
import aiohttp
from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.camera import authenticate_admin
from core.security import verify_jwt_token
from dependencies.database import get_db
from services.alerts_service import saveAlert
from services.camera_detect_info_service import save_to_camera_detect_info
from services.camera_line_service import get_camera_line
from services.camera_rule_service import getCameraRule
from services.camera_service import get_camera_url, get_camera_name_by_id
from services.car_through_route_service import saveCarThroughFixedRoute
from services.labels_service import getLabels
from services.user_service import is_admin
from util.detector import Detector
from fastapi.responses import JSONResponse, FileResponse
from api.socket_manager import sio
from util.hitBar import hitBar

router = APIRouter(prefix="/api")

# 服务器地址
URL = "http://localhost:8081"

# 加载 YOLO 模型
detector = Detector("util/weights/yolo12s.pt")

# 全局字典，用于存储每个摄像头最新处理后的MJPEG格式帧数据，键为摄像头ID
latest_frame = {}

# RTSP 摄像头地址
# RTSP_URL = "rtsp://admin:zhishidiannaoka1@192.168.1.101:10554/udp/av0_0"

# **确保使用绝对路径**
UPLOAD_FOLDER = os.path.abspath("./static/camera/uploads/")
SAVE_DIR = os.path.abspath("./static/camera/frames/")
INFO_DIR = os.path.abspath("./static/camera/info/")

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)



#获取label_id 和 label_name 的映射关系
def get_label_mapping(db: Session) -> dict:
    labelsResponse = getLabels(db)
    data = labelsResponse.get('data',{})
    labels = data.get('labels',[])
    label_mapping = {label["labelId"]: label["labelName"] for label in labels}
    return label_mapping


#计算交通当量，从表camera_rule中获取当前摄像头的 labels_equal_hold_ids和labels_equal_flow_ids分别计算当前帧的hold和flow的总交通当量 labels_equal_hold_ids= Column(JSON, nullable=True) # 仅 rule_value=2 时适用，包含labelId以及labelHoldNum的json字符串,代表本labelId可以视为多少个交通当量
    # labels_equal_flow_ids = Column(JSON, nullable=True) # 仅 rule_value=3 时适用,包含labelId以及labelFlowNum的json字符串,代表本labelId可以视为多少个交通当量
def calculate_traffic_volume_hold(detailedResult: dict, labels_equal_hold_ids: dict) -> dict:
    hold_volume = 0
    db = next(get_db())
    label_mapping = get_label_mapping(db)
    # 转换 labels_equal_flow_ids，将 labelId 替换为 labelName
    labels_equal_hold_names = {
        label_mapping.get(labelId, labelId): value  # 如果 labelId 不在映射中，则保留原值
        for labelId, value in labels_equal_hold_ids.items()
    }

    for label, count in detailedResult.get("count", {}).items():
        if label in labels_equal_hold_names:                              #这里好像对不上一个是id，一个是labelname————————
            hold_volume += count * int(labels_equal_hold_names[label])

    return {
        "hold_volume": hold_volume,
    }

#检测线还没考虑。。。。。。。。。。。____
def calculate_traffic_volume_flow(hitbarResult: list,labels_equal_flow_ids: dict) -> dict:
    """
        计算每条检测线的 flow 当量
        返回字典，键为检测线的名称，值为该检测线的 flow 当量
        """
    flow_for_line = {}
    db = next(get_db())
    label_mapping = get_label_mapping(db)
    # 将 labels_equal_flow_ids 中的 labelId 替换为 labelName，若找不到则保留原值
    labels_equal_flow_names = {
        label_mapping.get(labelId, labelId): value
        for labelId, value in labels_equal_flow_ids.items()
    }

    for hbResult in hitbarResult:
        # 使用 hitBarResult 中的 "name" 字段作为检测线名称
        line_name = hbResult.get("name", "unknown")
        line_flow = 0
        accumulator = hbResult.get("Accumulator", {})
        for label, count in accumulator.items():
            if label in labels_equal_flow_names:
                line_flow += count * int(labels_equal_flow_names[label])
        flow_for_line[line_name] = line_flow

    return flow_for_line


# **帧处理函数**
def process_frame(frame,hitbars):
    """
    **description**
    yolo模型处理

    **params**
    - frame (np.ndarray): 读取的原始帧

    **returns**
    - np.ndarray: 处理后的帧
    """
    # 运行YOLOv8检测
    processedImg, detailedResult,hitBarResult = detector.detect(frame,
                                                   addingBoxes=True,
                                                   addingLabel=True,
                                                   addingConf=False,
                                                   verbosity=2,
                                                    hitBars=hitbars);
    return processedImg,detailedResult,hitBarResult

def fetch_frame(source_url: str, cap=None):
    """
    **description**
    统一获取摄像头帧：
    - **HTTP 快照模式**: `requests.get()`
    - **RTSP 直播流模式**: `cv2.VideoCapture.read()`

    **params**
    - source_url (str): 摄像头 URL，可以是 HTTP 或 RTSP
    - cap (cv2.VideoCapture, optional): RTSP 模式下的 VideoCapture 对象，HTTP 模式下无需传入

    **returns**
    - frame (np.array or None): 处理后的帧，失败返回 None
    - current_time (float): 帧捕获时间戳
    """
    current_time = time.time()

    if source_url.startswith("http") and not source_url.endswith("video.mjpg"):
        # **HTTP 轮询模式**
        try:
            response = requests.get(source_url)
            if response.status_code != 200:
                print(f"无法获取 HTTP 摄像头快照: {response.status_code}")
                return None, current_time

            image_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is None:
                print("无法解码 HTTP 快照")

            return frame, current_time
        except Exception as e:
            print(f"获取 HTTP 帧失败: {e}")
            return None, current_time

    elif source_url.startswith("rtsp"):
        # **RTSP 直播模式**
        if cap is None or not cap.isOpened():
            print("RTSP 视频流未打开")
            return None, current_time

        success, frame = cap.read()
        if not success:
            print("RTSP 直播流丢帧，等待重试...")
            return None, current_time

        return frame, current_time

    # MJPG 流模式
    elif source_url.endswith("video.mjpg"):
        # 如果 cap 对象不存在或未打开，则新建一个
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(source_url)
            if not cap.isOpened():
                print("无法打开 MJPG 流")
                return None, current_time

        success, frame = cap.read()
        if not success:
            print("MJPG 读取失败")
            return None, current_time

        return frame, current_time

    else:
        print("❌ 不支持的摄像头协议")
        return None, current_time


def build_hitBars(frame, lines: list):
    """根据摄像头检测线数据构造 hitBar 对象列表"""
    hitBars = []
    frame_h, frame_w = frame.shape[:2]
    for i, line in enumerate(lines):
        startPoint = (round(float(line["cameraLineStartX"])*frame_w), round(float(line["cameraLineStartY"])*frame_h))
        endPoint = (round(float(line["cameraLineEndX"])*frame_w), round(float(line["cameraLineEndY"])*frame_h))
        # 主检测线 name 设为 "0"，其它依次为 "1", "2", ...
        name = "0" if line.get("isMainLine", False) else str(i + 1)
        hb = hitBar(
            imgSize=(frame_h, frame_w),
            startPoint=startPoint,
            endPoint=endPoint,
            name=name
        )
        hitBars.append(hb)
    return hitBars

def parse_camera_rules(camera_rules: list) -> dict:
    """
    解析摄像头规则，返回字典，包含：
      - car_category: list of vehicle type IDs (from rule 1)
      - labels_equal_hold_ids: dict from rule 2
      - labels_equal_flow_ids: dict from rule 3
      - maxVehicleHoldNum, minVehicleHoldNum, maxVehicleFlowNum, minVehicleFlowNum
      - maxContinuousTimePeriod, minContinuousTimePeriod
      - rule_first_camera_line_id (用于车辆类型预警)
      - camera_start_line_id, camera_end_line_id (用于车流量预警)
    """
    result = {
        "car_category": [],
        "labels_equal_hold_ids": {},
        "labels_equal_flow_ids": {},
        "maxVehicleHoldNum": 0,
        "minVehicleHoldNum": 0,
        "maxVehicleFlowNum": 0,
        "minVehicleFlowNum": 0,
        "maxContinuousTimePeriod": 0,
        "minContinuousTimePeriod": 0,
        "rule_first_camera_line_id": "",
        "camera_start_line_id": "",
        "camera_end_line_id": "",
        "eventDetect": True,
        "VehicleReserve": False,
    }
    for rule in camera_rules:
        rule_value = rule.get("ruleValue")
        if rule_value == "1":
            # 新格式：{"label": {"labelId": [...], "cameraLineId": "string"}}
            rule_first_label = rule.get("label", {})
            result["car_category"] = rule_first_label.get("labelId", [])
            result["rule_first_camera_line_id"] = rule_first_label.get("cameraLineId", "")
        elif rule_value == "2":
            vehicle_hold = rule.get("VehicleHold", {})
            data = vehicle_hold.get("LabelsEqual", [])
            result["labels_equal_hold_ids"] = {item["labelId"]: item["labelHoldNum"] for item in data}
            result["maxVehicleHoldNum"] = float(vehicle_hold.get("maxVehicleHoldNum", 0))
            result["minVehicleHoldNum"] = float(vehicle_hold.get("minVehicleHoldNum", 0))
            result["maxContinuousTimePeriod"] = int(vehicle_hold.get("maxContinuousTimePeriod", 0))
            result["minContinuousTimePeriod"] = int(vehicle_hold.get("minContinuousTimePeriod", 0))
        elif rule_value == "3":
            vehicle_flow = rule.get("VehicleFlow", {})
            data = vehicle_flow.get("LabelsEqual", [])
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    data = []
            result["labels_equal_flow_ids"] = {item["labelId"]: item["labelEqualNum"] for item in data}
            result["maxVehicleFlowNum"] = float(vehicle_flow.get("maxVehicleFlowNum", 0))
            result["minVehicleFlowNum"] = float(vehicle_flow.get("minVehicleFlowNum", 0))
            cameraStartLine = vehicle_flow.get("cameraStartLine", {})
            if cameraStartLine:
                result["camera_start_line_id"] = cameraStartLine.get("cameraLineId", "")
            cameraEndLine = vehicle_flow.get("cameraEndLine", {})
            if cameraEndLine:
                result["camera_end_line_id"] = cameraEndLine.get("cameraLineId", "")
        elif rule_value == "4":
            result["VehicleReserve"] = rule.get("vehicleReserve", False)  # 解析事故检测是否开启
        elif rule_value == "5":
            result["eventDetect"] = rule.get("eventDetect", False)  # 解析事故检测是否开启
    return result

def update_vehicle_history(vehicle_history: dict, hitBarResult: list, current_time: float):
    """
    更新 vehicle_history，遍历 hitBarResult 中每个检测线的 hitDetails，将检测记录存入 vehicle_history。
    每条记录包含：time, line, label
    """
    for hb in hitBarResult:
        line_name = hb.get("name", "unknown")
        for detail in hb.get("hitDetails", []):
            vehicle_no = detail.get("ID")
            if not vehicle_no:
                continue
            record = {
                "time": current_time,
                "line": line_name,
                "label": detail.get("cat"),
                # "count": detail.get("numInCat", 1)
            }
            if vehicle_no not in vehicle_history:
                vehicle_history[vehicle_no] = []
            vehicle_history[vehicle_no].append(record)


def process_vehicle_history(vehicle_history: dict, current_time: float, start_line_id: str, end_line_id: str,labels_equal_flow_ids, db):
    """
    处理 vehicle_history 中的记录，筛选同时包含起始和终止检测线的车辆，
    根据记录计算车辆行驶方向及类型，并调用 saveCarThroughFixedRoute 保存数据，
    最后从 vehicle_history 中移除该车辆的记录。
    """
    vehicles_through_channel = {}
    total_flow_equivalent = 0
    processed_vehicles = []  # 记录已处理的车辆，避免在循环中直接删除
    label_mapping = get_label_mapping(db)  # {labelId: labelName}
    labels_equal_flow_names = {
        label_mapping.get(label_id, label_id): float(value)
        for label_id, value in labels_equal_flow_ids.items()
    }
    for vehicle_no, records in vehicle_history.items():
        # 保留最近1分钟内记录
        records = [r for r in records if current_time - r["time"] <= 60]
        if records:
            vehicle_history[vehicle_no] = records
            detected_lines = {r["line"] for r in records}
            if start_line_id in detected_lines and end_line_id in detected_lines:
                vehicles_through_channel[vehicle_no] = records
        else:
            processed_vehicles.append(vehicle_no)
            continue

    for vehicle_no, records in vehicles_through_channel.items():
        sorted_records = sorted(records, key=lambda r: r["time"])
        s_line = sorted_records[0]["line"]
        e_line = sorted_records[-1]["line"]
        if s_line == start_line_id and e_line == end_line_id:
            direction = "正向"
        elif s_line == end_line_id and e_line == start_line_id:
            direction = "逆向"
        else:
            direction = "未知"

        # 计算该车辆的当量
        vehicle_type = sorted_records[0]["label"]
        vehicle_equivalent = labels_equal_flow_names.get(vehicle_type, 1)

        # 累加该车辆的当量
        if direction == "正向":
                total_flow_equivalent += vehicle_equivalent

        saveCarThroughFixedRoute(db, vehicle_no, vehicle_type, s_line, e_line, current_time, direction)
        print(f"保存车辆信息: {vehicle_type} {vehicle_no}，方向: {direction}")
        # **标记该车辆为已处理**
        processed_vehicles.append(vehicle_no)

    # **在循环后一次性删除已处理的车辆**
    for vehicle_no in processed_vehicles:
        del vehicle_history[vehicle_no]

    return total_flow_equivalent

def calculate_label_counts(hitBarResult: list, label_map: dict) -> dict:
    """统计所有 hitBarResult 中各 label 的累计数量，返回字典 (label_name -> count)"""
    label_counts = {name: 0 for name in label_map.values()}
    for hb in hitBarResult:
        accumulator = hb.get("Accumulator", {})
        for label_id, count in accumulator.items():
            if label_id in label_map:
                label_counts[label_map[label_id]] += count
    return label_counts

def update_lineWiseTrafficData(flow_for_line: dict, lineWiseTrafficData: dict):
    """将当前每条检测线的 flow 当量加入 lineWiseTrafficData 字典中"""
    for line_name, flow in flow_for_line.items():
        lineWiseTrafficData.setdefault(line_name, []).append(flow)


def process_vehicle_type_pre_warning(hitBarResult: list, rule_first_camera_line_id: str, car_category_names: list, frame, db, camera_id: str, camera_name: str, vehicle_warning_state: dict, vehicle_alert_start_time: dict, vehicle_clear_count: dict, clearThreshold: int,alert_image):
    """
    根据规则中指定的检测线（rule_first_camera_line_id），判断该检测线上检测到的车辆类型是否存在于 car_category_names 中，
    如果存在则触发车辆类型预警；如果后续检测不到，则更新解除计数。
    """
    target_hitbar = None
    for hb in hitBarResult:
        if hb.get("name") == rule_first_camera_line_id:
            target_hitbar = hb
            break
    if target_hitbar:
        accumulator = target_hitbar.get("Accumulator", {})
        detected_vehicle_types = list(accumulator.keys())
        detected = [vt for vt in detected_vehicle_types if vt in car_category_names]
        if detected:
            for vehicle in detected:
                if vehicle not in vehicle_warning_state:
                    new_alert_id = str(uuid.uuid4())
                    alert_image = f"{new_alert_id}.jpg"
                    cv2.imwrite(f"/alerts/on/{alert_image}", frame)
                    rule_type = "1"
                    rule_remark = f"检测到违规车辆: {vehicle}"
                    saveAlert(new_alert_id, camera_id, camera_name, 1, datetime.now(), None, None, alert_image,
                              rule_type, rule_remark)
                    sio.emit("updateHappeningAlert", {
                        "alertId": new_alert_id,
                        "cameraId": camera_id,
                        "cameraName": camera_name
                    })
                    vehicle_warning_state[vehicle] = new_alert_id
                    vehicle_alert_start_time[vehicle] = datetime.now()
                    vehicle_clear_count[vehicle] = 0
        else:   #但其实没有设计，这个先放在这里
            # 如果未检测到，更新解除计数
            for vehicle in list(vehicle_warning_state.keys()):
                vehicle_clear_count[vehicle] += 1
                if vehicle_clear_count[vehicle] >= clearThreshold:
                    alert_id = vehicle_warning_state[vehicle]
                    alert_end_time = time.time()
                    saveAlert(alert_id, camera_id, camera_name, 2, vehicle_alert_start_time[vehicle],
                              alert_end_time, None, alert_image, "1", f"{vehicle} 车辆消失，预警结束")
                    del vehicle_warning_state[vehicle]
                    del vehicle_alert_start_time[vehicle]
                    del vehicle_clear_count[vehicle]
                    print(f"[✅ 车辆类型预警解除] {vehicle} 已消失，预警结束")

def aggregate_label_counts(traffic_data: list, label_map: dict) -> dict:
    """对 traffic_data 中记录的 label_counts 进行累计"""
    aggregated = {name: 0 for name in label_map.values()}
    for _, _, _, counts in traffic_data:
        for label, count in counts.items():
            aggregated[label] += count
    return aggregated

def process_traffic_flow_warning(
    target_flow: float,
    current_time: float,
    maxVehicleFlowNum: float,
    minVehicleFlowNum: float,
    maxContinuousTimePeriod: float,
    minContinuousTimePeriod: float,
    time_window: float,
    flow_warning_count: int,
    flow_clear_count: int,
    active_alerts: dict,
    warning_state: str,
    frame,
    db,
    camera_id: str,
    camera_name: str
):
    """
    处理 **车流量** 预警逻辑。
    - 计算 target_flow 是否超出设定的最大/最小阈值。
    - 触发或解除 **车流量** 相关的预警。

    **params**
    - target_flow: 当前检测线的车流当量
    - maxVehicleFlowNum / minVehicleFlowNum: 车流量上/下限
    - maxContinuousTimePeriod / minContinuousTimePeriod: 触发/解除预警的时间窗口
    """
    # **更新流量预警计数**
    if target_flow >= maxVehicleFlowNum:
        flow_warning_count += 1
    else:
        flow_warning_count = 0

    if target_flow <= minVehicleFlowNum:
        flow_clear_count += 1
    else:
        flow_clear_count = 0

    warning_start_time = None
    warning_end_time = None

    # **触发流量预警**
    if flow_warning_count >= (maxContinuousTimePeriod // time_window):
        rule_type = "3"
        rule_remark = "车流量预警"

        # 如果该类型预警还未记录，则新增预警
        if rule_type not in active_alerts:
            warning_state = "正在发生"
            warning_start_time = current_time
            new_alert_id = str(uuid.uuid4())
            alert_image = f"{new_alert_id}.jpg"
            cv2.imwrite(f"/alerts/on/{alert_image}", frame)

            saveAlert(new_alert_id, camera_id, camera_name, 1, warning_start_time, None, None, alert_image,
                      rule_type, rule_remark)

            sio.emit("updateHappeningAlert", {
                "alertId": new_alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name
            })

            active_alerts[rule_type] = {
                "alert_id": new_alert_id,
                "warning_start_time": warning_start_time,
                "alert_image": alert_image,
                "rule_remark": rule_remark
            }

    # **解除流量预警**
    if flow_clear_count >= (minContinuousTimePeriod // time_window):
        if warning_state == "正在发生":
            warning_state = "已经发生"
            warning_end_time = current_time

            for rule_type, alert_info in active_alerts.items():
                alert_id = alert_info["alert_id"]
                ws = alert_info["warning_start_time"]
                ai = alert_info["alert_image"]
                rr = alert_info["rule_remark"]

                saveAlert(alert_id, camera_id, camera_name, 2, ws, warning_end_time, None, ai, rule_type, rr)

            active_alerts.clear()

    return flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time


def process_vehicle_congestion_warning(
    avg_hold_volume: float,
    current_time: float,
    maxVehicleHoldNum: float,
    minVehicleHoldNum: float,
    maxContinuousTimePeriod: float,
    minContinuousTimePeriod: float,
    time_window: float,
    hold_warning_count: int,
    hold_clear_count: int,
    active_alerts: dict,
    warning_state: str,
    frame,
    db,
    camera_id: str,
    camera_name: str
):
    """
    处理 **车辆拥挤度** 预警逻辑。
    - 计算 avg_hold_volume 是否超出设定的最大/最小阈值。
    - 触发或解除 **车辆拥挤** 相关的预警。

    **params**
    - avg_hold_volume: 该时间窗口内摄像头检测范围的车辆数量
    - maxVehicleHoldNum / minVehicleHoldNum: 拥挤度的上/下限
    """
    # **更新拥挤度预警计数**
    if avg_hold_volume >= maxVehicleHoldNum:
        hold_warning_count += 1
    else:
        hold_warning_count = 0

    if avg_hold_volume <= minVehicleHoldNum:
        hold_clear_count += 1
    else:
        hold_clear_count = 0

    warning_start_time = None
    warning_end_time = None

    # **触发车辆拥挤度预警**
    if hold_warning_count >= (maxContinuousTimePeriod // time_window):
        rule_type = "2"
        rule_remark = "车辆拥挤度预警"

        # 如果该类型预警还未记录，则新增预警
        if rule_type not in active_alerts:
            warning_state = "正在发生"
            warning_start_time = current_time
            new_alert_id = str(uuid.uuid4())
            alert_image = f"{new_alert_id}.jpg"
            cv2.imwrite(f"/alerts/on/{alert_image}", frame)

            saveAlert(new_alert_id, camera_id, camera_name, 1, warning_start_time, None, None, alert_image,
                      rule_type, rule_remark)

            sio.emit("updateHappeningAlert", {
                "alertId": new_alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name
            })

            active_alerts[rule_type] = {
                "alert_id": new_alert_id,
                "warning_start_time": warning_start_time,
                "alert_image": alert_image,
                "rule_remark": rule_remark
            }

    # **解除拥挤度预警**
    if hold_clear_count >= (minContinuousTimePeriod // time_window):
        if warning_state == "正在发生":
            warning_state = "已经发生"
            warning_end_time = current_time

            for rule_type, alert_info in active_alerts.items():
                alert_id = alert_info["alert_id"]
                ws = alert_info["warning_start_time"]
                ai = alert_info["alert_image"]
                rr = alert_info["rule_remark"]

                saveAlert(alert_id, camera_id, camera_name, 2, ws, warning_end_time, None, ai, rule_type, rr)

            active_alerts.clear()

    return hold_warning_count, hold_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time


def process_vehicle_reservation_warning(
    hitBarResult: list,
    vehicle_history: dict,
    current_time: float,
    frame,
    db,
    camera_id: str,
    camera_name: str
):
    """
    **description**
    处理车辆预约预警：
    - 读取预约车辆信息（TXT 文件）
    - 记录当前帧车辆检测数据，并检查是否按照预约路线行进
    - 如果车辆未按照预约路线行进，则触发预警

    **params**
    - hitBarResult (list): 车辆检测数据（包含检测线 ID 和车辆信息）
    - vehicle_history (dict): 车辆历史行进记录 { 车牌号: [最近检测到的线路] }
    - current_time (float): 当前时间戳
    - frame (np.ndarray): 当前帧图像
    - db: 数据库连接
    - camera_id (str): 摄像头 ID
    - camera_name (str): 摄像头名称

    **returns**
    - 是否触发了预警 (bool)
    """

    # **加载预约车辆信息**
    reservation_file = "./data/vehicle_reservations.txt"
    vehicle_reservations = {}

    try:
        with open(reservation_file, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 4:
                    continue

                vehicle_no, start_time, end_time, route_str = parts
                vehicle_reservations[vehicle_no] = {
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "expected_route": route_str.split("->")  # 预约的行进路线（检测线 ID 顺序）
                }
    except Exception as e:
        print(f"❌ 读取预约车辆数据失败: {e}")
        return False

    # **遍历 hitBarResult，记录当前帧的车辆检测信息**
    detected_vehicles = {}
    for hb in hitBarResult:
        line_name = hb.get("name", "unknown")  # 当前检测线 ID
        for detail in hb.get("hitDetails", []):
            vehicle_no = detail.get("ID")
            if not vehicle_no:
                continue
            detected_vehicles[vehicle_no] = line_name  # 记录车辆当前检测线

    # **检测预约违规**
    for vehicle_no, line_id in detected_vehicles.items():
        if vehicle_no in vehicle_reservations:
            reservation = vehicle_reservations[vehicle_no]

            # **1️⃣ 检查预约时间**
            if not (reservation["start_time"] <= current_time <= reservation["end_time"]):
                continue  # 时间不符合，跳过

            # **2️⃣ 记录车辆最近的检测线**
            previous_line = vehicle_history.get(vehicle_no, None)  # 获取该车上一帧的检测线
            vehicle_history[vehicle_no] = line_id  # 更新车辆的最新检测线

            # **3️⃣ 判断是否按照预约路线行进**
            expected_route = reservation["expected_route"]

            if previous_line and previous_line != line_id:  # 车辆从 previous_line 移动到了 line_id
                if line_id not in expected_route:
                    # **触发预约违规预警**
                    alert_id = str(uuid.uuid4())
                    alert_image = f"{alert_id}.jpg"
                    cv2.imwrite(f"/alerts/on/{alert_image}", frame)

                    rule_type = "4"
                    rule_remark = f"🚨 预约车辆违规 - 车牌: {vehicle_no}, 行进至未授权线路 {line_id} (上次检测线: {previous_line})"

                    # **保存预警到数据库**
                    saveAlert(alert_id, camera_id, camera_name, 1, current_time, None, None, alert_image, rule_type, rule_remark)

                    # **发送 WebSocket 预警**
                    sio.emit("updateHappeningAlert", {
                        "alertId": alert_id,
                        "cameraId": camera_id,
                        "cameraName": camera_name,
                    })

                    print(f"🚨 预约车辆 {vehicle_no} 违规！从 {previous_line} 进入未预约检测线 {line_id}")

                    return True  # 预警已触发

    return False  # 未触发预警



def process_accident_warning(detailedResult: dict, frame, current_time: float, db, camera_id: str, camera_name: str):
    """
    **description**
    处理事故检测逻辑：当 detailedResult 返回 accidentBoxes 和 accidentConf 时，触发事故预警。

    **params**
    - detailedResult (dict): YOLO 检测结果，包含 accidentBoxes 和 accidentConf
    - frame (np.ndarray): 当前帧图像
    - current_time (float): 当前时间戳
    - db: 数据库连接
    - camera_id (str): 摄像头 ID
    - camera_name (str): 摄像头名称

    **returns**
    - 触发事故预警并保存到数据库，同时通过 Socket.IO 发送到前端
    """
    accident_boxes = detailedResult.get("accidentBoxes", [])
    accident_conf = detailedResult.get("accidentConf", [])

    if accident_boxes and accident_conf:
        # 事故发生，生成唯一 ID
        alert_id = str(uuid.uuid4())
        alert_image = f"{alert_id}.jpg"
        cv2.imwrite(f"/alerts/on/accident/{alert_image}", frame)

        # 获取最高事故置信度
        max_accident_confidence = max(accident_conf)

        # 事故预警详情
        rule_type = "5"
        rule_remark = f"⚠️ 事故预警 - 最高置信度: {max_accident_confidence:.2f}"

        # 保存事故预警到数据库
        saveAlert(alert_id, camera_id, camera_name, 1, current_time, None, None, alert_image, rule_type, rule_remark)

        # 通过 Socket.IO 发送事故预警到前端
        sio.emit("updateHappeningAlert", {
            "alertId": alert_id,
            "cameraId": camera_id,
            "cameraName": camera_name,
            # "alertType": "事故检测",
            # "alertConfidence": max_accident_confidence,
            # "timestamp": current_time
        })

        print(f"🚨 事故预警触发！最高置信度: {max_accident_confidence:.2f}")

        return True  # 预警已触发

    return False  # 未触发预警



#HTTP请求的方式
async def generate_frames(source_url:str,camera_id:str, liveStreamType: str = None):
    """
    **description**
    统一处理摄像头视频流，无论是 HTTP 轮询还是 RTSP 直播流。
    - **HTTP 轮询**: `requests.get()`
    - **RTSP 直播流**: `cv2.VideoCapture.read()`

    **params**
    - source_url (str): 摄像头 URL
    - camera_id (str): 摄像头 ID
    - liveStreamType (str, optional): 直播流类型，RTSP 模式下可选 ("full" / "preview")

    **returns**
    - StreamingResponse: 逐帧返回处理后的 JPEG 数据流。
    """
    try:
        print(f"正在拉取摄像头视频: {source_url}")

        # **RTSP 直播流特殊处理**
        cap = None
        if source_url.startswith("rtsp"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
            if liveStreamType == 'full':
                source_url = f"{source_url}?stream=full"
            else:
                source_url = f"{source_url}?stream=preview"

            cap = cv2.VideoCapture(source_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print("RTSP 摄像头无法连接")
                return

        interval = 0.5 if source_url.startswith("http") else 0.03  # **HTTP 轮询间隔 / RTSP 直播流帧率**
        db = next(get_db())
        camera_name = get_camera_name_by_id(db,camera_id)
        time_window = 10
        traffic_data = []  # 存储 (time, hold_volume, flow_volume)
        label_map = get_label_mapping(db)
        start_time = time.time()

        # 预警状态变量
        active_alerts = {}
        warning_state = "正常"
        warning_start_time = None
        warning_end_time = None


        # 预警检测的历史记录
        hold_warning_count = 0
        flow_warning_count = 0
        hold_clear_count = 0
        flow_clear_count = 0

        # 预警状态变量
        vehicle_warning_state = {}  # 存储每个 alertId 的状态
        vehicle_alert_start_time = {}  # 预警开始时间
        vehicle_clear_count = {}  # 预警清除计数器
        clearThreshold = 3  # 连续 N 个 time_window 未检测到该车辆则结束预警---------这个？？？？

        vehicle_history = {}  # 格式：{ vehicle_no: [ { "time": timestamp, "line": line_name, "label": label }, ... ] }
        history_last_checked = time.time()

        camera_line_response = get_camera_line(db, camera_id)
        lines = []
        if camera_line_response["code"] == "200" and camera_line_response["data"].get("cameraLines"):
            lines = camera_line_response["data"]["cameraLines"]
        else:
            print("该摄像头没有检测线")

        hitBars = []

        # 存储事故状态
        accident_warning_state = "正常"
        accident_alert_start_time = None
        accident_alert_end_time = None
        accident_active_alerts = {}  # 记录事故报警的 alert_id
        accident_clear_count = 0
        accident_warning_count = 0
        clearAccidentThreshold = 3  # N 个时间窗口内未检测到事故才解除报警
        accident_threshold = 0.8  # 事故置信度阈值（可调整）

        while True:
            # 将阻塞的 fetch_frame 调用放入线程中执行
            frame, current_time = await asyncio.to_thread(fetch_frame, source_url, cap)
            if frame is None:
                await asyncio.sleep(1)
                continue

            # ————这里获取时间
            current_time = time.time()

            # 根据获取的检测线数据构造 hitBars 对象
            if not hitBars:
                hitBars = build_hitBars(frame, lines)

            processed, detailedResult ,hitBarResult= process_frame(frame,hitBars)
            # 打印 detailedResult 和 hitBarResult
            # print("detailedResult:", detailedResult)
            print("hitBarResult:", hitBarResult)

            # 获取camera_rule的数据
            camera_rule_response = getCameraRule(db,camera_id)
            if camera_rule_response["code"] != "200":
                print(f"摄像头规则查询失败: {camera_rule_response['msg']}")
            else:
                camera_rules = camera_rule_response["data"]["cameraRules"]

            # 解析规则
            rules = parse_camera_rules(camera_rules)

            # 假设规则中开启了事故检测 eventDetect
            if rules.get("eventDetect", False):
                accident_detected = process_accident_warning(
                    detailedResult=detailedResult,
                    frame=frame,
                    current_time=current_time,
                    db=db,
                    camera_id=camera_id,
                    camera_name=camera_name
                )

                if accident_detected:
                    print(f"⚠️ 事故检测 - 事故已上报")

            # 🚗 预约车辆预警（基于摄像头规则）
            if rules.get("VehicleReserve", False):
                reservation_alert_triggered = process_vehicle_reservation_warning(
                    hitBarResult=hitBarResult,
                    vehicle_history=vehicle_history,  # 车辆历史行进记录
                    current_time=current_time,
                    frame=frame,
                    db=db,
                    camera_id=camera_id,
                    camera_name=camera_name
                )

                if reservation_alert_triggered:
                    print(f"⚠️ 预约车辆预警 - 违规行为已上报")

            # flow_for_line = {}  用于存储每条检测线的 flow 当量，键为检测线的名称
            flow_for_line = calculate_traffic_volume_flow(hitBarResult, rules["labels_equal_flow_ids"])
            # 示例：打印各检测线的 flow 当量
            print("各检测线 Flow 当量：", flow_for_line)

            # 起止线存在时的车流量预警：当规则中指定了起始与终止检测线且二者不相同
            if rules["camera_start_line_id"] and rules["camera_end_line_id"] and rules["camera_start_line_id"] != rules[
                "camera_end_line_id"]:
                # 在每一帧处理后，将每一条碰撞线的车辆检测结果存入 history
                update_vehicle_history(vehicle_history, hitBarResult, current_time)
                #60s检测一次--------其实可以10s检测一次，这样可以避免60>maxcontiunoustimeperiod检测不到预警
                if current_time - history_last_checked >= 60:
                    #计算60s内的所有车辆当量
                    total_flow_equivalent = process_vehicle_history(vehicle_history, current_time, rules["camera_start_line_id"],
                                            rules["camera_end_line_id"],rules["labels_equal_flow_ids"], db)

                    history_last_checked = current_time

                    # **更新预警状态**
                    # 🚗 车流量预警（基于 target_flow）
                    flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = process_traffic_flow_warning(
                        total_flow_equivalent,
                        current_time,
                        rules["maxVehicleFlowNum"],
                        rules["minVehicleFlowNum"],
                        rules["maxContinuousTimePeriod"],
                        rules["minContinuousTimePeriod"],
                        time_window,
                        flow_warning_count,
                        flow_clear_count,
                        active_alerts,
                        warning_state,
                        frame,
                        db,
                        camera_id,
                        camera_name
                    )

            # 上面没有预警处理，只是保存了历史，没有按预警逻辑检查当量------已解决
            # 这里应该少了一个处理逻辑——————当起止线都存在并相等且不是主检测线的时候的车流量预警的判断——————————这个时候的targetlineid应该为起线或者止线------已解决


            # 默认设置：若起始/终止线为空，则设为主检测线 "0"
            if not rules["camera_start_line_id"]:
                rules["camera_start_line_id"] = "0"
            if not rules["camera_end_line_id"]:
                rules["camera_end_line_id"] = "0"

            # **判断是否起始线 == 终止线且不是主检测线**
            if rules["camera_start_line_id"] == rules["camera_end_line_id"] and rules["camera_start_line_id"] != "0":
                target_line_id = rules["camera_start_line_id"]  # 使用该检测线
                print(f"⚠️ 车流量预警：起止线相同，使用检测线 {target_line_id}")
            else:
                target_line_id = "0"
            target_flow = flow_for_line.get(target_line_id, 0)
            print(f"目标检测线/主检测线 {target_line_id} 的 Flow 当量：", target_flow)

            #计算车拥挤度当量
            hold_volume = calculate_traffic_volume_hold(detailedResult, rules["labels_equal_hold_ids"])["hold_volume"]
            #计算所有 hitBarResult 中各 label 的累计数量————相当于计算这个摄像头在这一帧所有的碰撞线检测到的各label的累计数量————那为什么不用detailresult计算？？？神金
            label_counts = calculate_label_counts(hitBarResult, label_map)
            traffic_data.append((current_time, hold_volume, target_flow, label_counts))

            # 更新各检测线流量数据（全局存储结构），将当前每条检测线的 flow 当量加入 lineWiseTrafficData 字典中
            update_lineWiseTrafficData(flow_for_line, globals().setdefault("lineWiseTrafficData", {}))

            # 车辆类型预警：根据规则中指定的检测线进行判断
            car_category_names = [label_map.get(cid) for cid in rules["car_category"] if cid in label_map]
            process_vehicle_type_pre_warning(hitBarResult, rules["rule_first_camera_line_id"], car_category_names,
                                             frame, db, camera_id, camera_name, vehicle_warning_state,
                                             vehicle_alert_start_time, vehicle_clear_count, clearThreshold,frame)           #————————————这里没有设计完整

            # 每个时间窗口结束后统计数据及预警逻辑（基于主检测线）
            if current_time - start_time >= time_window:
                if traffic_data:
                    avg_hold_volume = sum(h for _, h, _, _ in traffic_data) / len(traffic_data)
                    aggregated_label_counts = aggregate_label_counts(traffic_data, label_map)
                    save_to_camera_detect_info(db, camera_id, avg_hold_volume, target_flow, aggregated_label_counts,
                                               current_time)

                    # 预警计数更新
                    # 🚗 车流量预警（基于 target_flow）
                    flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = process_traffic_flow_warning(
                        target_flow,
                        current_time,
                        rules["maxVehicleFlowNum"],
                        rules["minVehicleFlowNum"],
                        rules["maxContinuousTimePeriod"],
                        rules["minContinuousTimePeriod"],
                        time_window,
                        flow_warning_count,
                        flow_clear_count,
                        active_alerts,
                        warning_state,
                        frame,
                        db,
                        camera_id,
                        camera_name
                    )

                    # 🚙 车辆拥挤度预警（基于 avg_hold_volume）
                    hold_warning_count, hold_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = process_vehicle_congestion_warning(
                        avg_hold_volume,
                        current_time,
                        rules["maxVehicleHoldNum"],
                        rules["minVehicleHoldNum"],
                        rules["maxContinuousTimePeriod"],
                        rules["minContinuousTimePeriod"],
                        time_window,
                        hold_warning_count,
                        hold_clear_count,
                        active_alerts,
                        warning_state,
                        frame,
                        db,
                        camera_id,
                        camera_name
                    )

                traffic_data.clear()
                start_time = current_time


            ret, buffer = await asyncio.to_thread(cv2.imencode, '.jpg', processed)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            await asyncio.sleep(interval)  # 控制快照采集速率

    except Exception as e:
        print(f"摄像头连接失败：{e}")
        traceback.print_exc()  # 这里打印完整的错误堆栈信息


async def background_camera_task(camera_id: str, liveStreamType: str = None):
    """
    后台任务：单个摄像头持续读取帧，并将最新的帧保存到全局字典中
    """
    await asyncio.sleep(5)  # 等待 YOLO 模型加载（根据实际情况调整时间）
    global latest_frames
    latest_frames = {}
    db = next(get_db())
    while True:
        camera_url = get_camera_url(db, camera_id)
        if not camera_url:
            print(f"摄像头 {camera_id} 的 URL 未找到")
            return

        try:
            async for frame in generate_frames(camera_url, camera_id, liveStreamType):
                # 如果 generate_frames 内部出现错误，latest_frames[camera_id] 已被更新为错误信息
                # 否则，持续更新最新帧
                latest_frames[camera_id] = frame
        except Exception as e:
            # 捕获后台任务其他未处理异常
            print(f"后台任务中摄像头 {camera_id} 发生异常：{e}")
            traceback.print_exc()

        # 如果发生异常或循环结束，等待一段时间后重启该任务
        await asyncio.sleep(5)


# **FastAPI 端点**
@router.get("/storage/getCameraLiveStream")
async def proxy_video_feed(
    cameraId: str = Query(..., description="摄像头 ID"),
    liveStreamType: str = Query(..., description="直播流类型"),
    token: str = Query(..., description="管理员访问权限 Token"),
    db: Session = Depends(get_db)
):
    # 验证管理员权限
    token_payload = verify_jwt_token(token)
    if not token_payload or not token_payload.get("is_admin"):
        return JSONResponse(content={"code": "403", "msg": "Unauthorized", "data": {}}, status_code=403)

    # 检查该摄像头是否在全局字典中存在
    if cameraId not in latest_frames:
        return JSONResponse(content={"code": "404", "msg": "Camera not found or not started", "data": {}}, status_code=404)

    # 定义异步生成器，从全局字典中不断读取最新帧数据并返回
    async def video_streamer():
        while True:
            frame = latest_frames.get(cameraId)
            if frame is not None:
                yield frame
            await asyncio.sleep(0.05)

    return StreamingResponse(
        video_streamer(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
    # 这里要新增获取摄像头类型，根据是http还是rstp来判断使用哪种处理方法
    # if cameraURL.startswith("http"):
    # print(f"正在拉取 HTTP 直播流: {cameraURL}")
    # return StreamingResponse(generate_frames(cameraURL, cameraId, liveStreamType if liveStreamType else None),
    #                          media_type="multipart/x-mixed-replace; boundary=frame")
    # elif cameraURL.startswith("rtsp"):
    #
    #     # 根据liveStreamType选择不同的流
    #     if liveStreamType == 'full':
    #         camera_url = f"{cameraURL}?stream=full"
    #     else:
    #         camera_url = f"{cameraURL}?stream=preview"
    #
    #     print(f"正在拉取 RTSP 直播流: {camera_url}")
    #
    #     return StreamingResponse(generate_frames(camera_url,cameraId), media_type="multipart/x-mixed-replace; boundary=frame")


# **Socket.IO 端点：发送 YOLOv8 检测结果**
@sio.event
async def video_feed(sid):
    """
    **description**
    Socket.IO 连接，实时推送 YOLOv8 目标检测结果（不包含视频流）。

    **params**
    - sid: Socket.IO 连接 ID

    **returns**
    - 实时 JSON 数据
    """
    print(f"Socket.IO Client connected: {sid}")

    try:
        # **调用 generate_frames() 处理帧**
        async for frame in generate_frames():  #`async for` 以异步方式处理数据
            # 发送处理结果
            await sio.emit("detection", frame, room=sid)

    except Exception as e:
        print(f"Socket.IO 连接断开: {e}")

