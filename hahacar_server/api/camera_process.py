import asyncio
import json
import os
import traceback
import uuid
from datetime import datetime

import cv2
import time as t;

import numpy as np
import requests
import aiohttp
from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.camera import authenticate_admin
from core.security import verify_jwt_token
from dependencies.database import get_db;
from services.alerts_service import saveAlert
from services.camera_detect_info_service import save_to_camera_detect_info
from services.camera_line_service import get_camera_line
from services.camera_rule_service import getCameraRule
from services.camera_service import get_camera_url, get_camera_name_by_id
from services.car_through_route_service import saveCarThroughFixedRoute
from services.labels_service import getLabels
from services.user_service import is_admin
from services.warning_service import *
from util.detector import Detector
from fastapi.responses import JSONResponse, FileResponse
from api.socket_manager import sio
from util.hitBar import hitBar

router = APIRouter(prefix="/api")

# 服务器地址
URL = "http://localhost:8081"

MODEL_FOR_DETECTOR = "util/weights/yolo12s.pt";

global detectors
detectors = {};

# 全局字典，用于存储每个摄像头最新处理后的MJPEG格式帧数据，键为摄像头ID
latest_frame = {};

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
    db = get_db();
    label_mapping = get_label_mapping(db)
    # 转换 labels_equal_flow_ids，将 labelId 替换为 labelName
    labels_equal_hold_names = {
        label_mapping.get(labelId, labelId): value  # 如果 labelId 不在映射中，则保留原值
        for labelId, value in labels_equal_hold_ids.items()
    }
    inverted_mapping = {
            value: label_mapping.get(labelId, labelId)
            for labelId, value in labels_equal_hold_ids.items()
        }

    for label, count in detailedResult.get("count", {}).items():
        label = inverted_mapping.get(label, label)
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
    db = get_db();
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
def process_frame(frame,hitbars, camera_id: str):
    """
    **description**
    yolo模型处理

    **params**
    - frame (np.ndarray): 读取的原始帧

    **returns**
    - np.ndarray: 处理后的帧
    """
    # 运行YOLOv8检测
    detector = detectors.get(camera_id, Detector(MODEL_FOR_DETECTOR));
    processedImg, detailedResult,hitBarResult = detector.detect(frame,
                                                   addingBoxes=True,
                                                   addingLabel=True,
                                                   addingConf=False,
                                                   verbosity=2,
                                                    hitBars=hitbars);
    detectors["camera_id"] = detector;
    return processedImg,detailedResult,hitBarResult;

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
    current_time = t.time()

    # # **本地视频模式**
    # if source_url.endswith((".mp4", ".avi", ".mov")):
    #     if cap is None or not cap.isOpened():
    #         cap = cv2.VideoCapture(source_url)
    #         if not cap.isOpened():
    #             print("❌ 无法打开本地视频文件")
    #             return None, current_time
    #
    #     success, frame = cap.read()
    #     if not success:
    #         print("❌ 读取本地视频帧失败")
    #         return None, current_time
    #
    #     return frame, current_time

    if source_url.startswith("http") and not source_url.endswith("video.mjpg"):
        # **HTTP 轮询模式**
        try:
            response = requests.get(source_url)
            if response.status_code != 200:
                print(f"无法获取 HTTP 摄像头快照: {response.status_code}")
                return None, current_time

            image_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            current_time = t.time();
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
        current_time = t.time();
        if not success:
            print("MJPG 读取失败")
            return None, current_time

        return frame, current_time

    elif source_url.endswith(".mp4"):
        if cap is None or not cap.isOpened:
            cap = cv2.VideoCapture(source_url);
        success, frame = cap.read();
        if success:
            return frame, current_time;
        else:
            print("MP4 读取失败");
            return None, current_time;


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
      - maxContinuoustimePeriod, minContinuoustimePeriod
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
        "maxContinuoustimePeriod": 0,
        "minContinuoustimePeriod": 0,
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
            result["maxContinuoustimePeriod"] = int(vehicle_hold.get("maxContinuoustimePeriod", 0))
            result["minContinuoustimePeriod"] = int(vehicle_hold.get("minContinuoustimePeriod", 0))
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


def process_vehicle_history(vehicle_history: dict, current_time: float, start_line_id: str, end_line_id: str,labels_equal_flow_ids, camera_id:str, db):
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
        vehicle_type = sorted_records[0]["label"]                                   #这个需要从get_label_mapping，存储对应的id，
        vehicle_equivalent = labels_equal_flow_names.get(vehicle_type, 1)

        # 如果你只想统计 "从 start_line_id -> end_line_id" 这条路线的当量：
        if s_line == start_line_id and e_line == end_line_id:                           # 这里的id是hitbar解析出来的id，需要和cameralineid对应上再存--------------
            total_flow_equivalent += vehicle_equivalent
            # 保存车辆信息(无方向)
            saveCarThroughFixedRoute(
                db,
                vehicle_no=vehicle_no,
                vehicle_type=vehicle_type,
                start_line=s_line,  # 实际车辆经过的起线
                end_line=e_line,  # 实际车辆经过的终线
                current_time=current_time,
                camera_id = camera_id,
                # 下面省略 direction 等字段
            )
            print(f"已检测到车辆: {vehicle_type}-{vehicle_no}, 路线: {s_line}->{e_line}")
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
        for label_id, count in accumulator.items():                                     #在这里加上对车辆经过某条检测线的保存
            if label_id in label_map:
                label_counts[label_map[label_id]] += count
    return label_counts

def update_lineWiseTrafficData(flow_for_line: dict, lineWiseTrafficData: dict):
    """将当前每条检测线的 flow 当量加入 lineWiseTrafficData 字典中"""
    for line_name, flow in flow_for_line.items():
        lineWiseTrafficData.setdefault(line_name, []).append(flow)




def aggregate_label_counts(traffic_data: list, label_map: dict) -> dict:
    """对 traffic_data 中记录的 label_counts 进行累计"""
    aggregated = {name: 0 for name in label_map.values()}
    for _, _, _, counts in traffic_data:
        for label, count in counts.items():
            aggregated[label] += count
    return aggregated



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

        interval = 0.5 if source_url.startswith("http") and not source_url.endswith("video.mjpg") else 0.03  # **HTTP 轮询间隔 / RTSP 直播流帧率**
        db = get_db();
        camera_name = get_camera_name_by_id(db,camera_id)
        time_window = 10
        traffic_data = []  # 存储 (time, hold_volume, flow_volume)
        label_map = get_label_mapping(db)
        start_time = t.time();

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
        history_last_checked = t.time();

        camera_line_response = get_camera_line(db, camera_id)
        lines = []
        if camera_line_response["code"] == "200" and camera_line_response["data"].get("cameraLines", []):
            lines = camera_line_response["data"]["cameraLines"]
        else:
            print("该摄像头没有检测线")

        hitBars = []

        #车辆预约路线预警
        the_vehicle_history = {} #该车辆的历史行进记录
        detected_vehicles = {}  # 记录车牌号对应的检测线

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
            # frame, current_time = await asyncio.to_thread(fetch_frame, source_url, cap)
            frame, current_time = fetch_frame(source_url, cap);
            if frame is None:
                await asyncio.sleep(0.1);
                continue


            # 根据获取的检测线数据构造 hitBars 对象
            if not hitBars:
                hitBars = build_hitBars(frame, lines)

            processed, detailedResult ,hitBarResult = process_frame(frame,hitBars, camera_id);
            # 打印 detailedResult 和 hitBarResult
            # print("detailedResult:", detailedResult)
            # print("hitBarResult:", hitBarResult)

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
                accident_detected = await process_accident_warning(
                    detailedResult=detailedResult,
                    frame=frame,
                    current_time=current_time,
                    db=db,
                    camera_id=camera_id,
                    camera_name=camera_name
                )

                if accident_detected:
                    print(f"⚠️ 事故检测 - 事故已上报")

            # 提前解析 hitBarResult，筛选出预约车辆
            for hb in hitBarResult:
                line_name = hb.get("name", "unknown")  # 当前检测线 ID
                for detail in hb.get("hitDetails", []):
                    vehicle_no = detail.get("ID")
                    if not vehicle_no:
                        continue
                    detected_vehicles[vehicle_no] = line_name  # 记录该车当前所在的检测线

            # 🚗 预约车辆预警（仅当有检测到的车辆时才执行）
            if rules.get("VehicleReserve", False) and detected_vehicles:
                reservation_alert_triggered = process_vehicle_reservation_warning(
                    detected_vehicles=detected_vehicles,  # 只传入当前帧检测到的目标车辆
                    the_vehicle_history=the_vehicle_history,  # 车辆历史行进记录
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
                                            rules["camera_end_line_id"],rules["labels_equal_flow_ids"], camera_id,db)

                    history_last_checked = current_time

                    # **更新预警状态**
                    # 🚗 车流量预警（基于 target_flow）
                    flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = process_traffic_flow_warning(
                        total_flow_equivalent,
                        current_time,
                        rules["maxVehicleFlowNum"],
                        rules["minVehicleFlowNum"],
                        rules["maxContinuoustimePeriod"],
                        rules["minContinuoustimePeriod"],
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
                print(f"车流量：起止线相同，使用检测线 {target_line_id}")
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
            await process_vehicle_type_pre_warning(hitBarResult, rules["rule_first_camera_line_id"], car_category_names,
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
                    flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_traffic_flow_warning(
                        target_flow,
                        current_time,
                        rules["maxVehicleFlowNum"],
                        rules["minVehicleFlowNum"],
                        rules["maxContinuoustimePeriod"],
                        rules["minContinuoustimePeriod"],
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
                    hold_warning_count, hold_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_vehicle_congestion_warning(
                        avg_hold_volume,
                        current_time,
                        rules["maxVehicleHoldNum"],
                        rules["minVehicleHoldNum"],
                        rules["maxContinuoustimePeriod"],
                        rules["minContinuoustimePeriod"],
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


            # #在这里添加处理后的image
            # if processed is not None:
            #     latest_frames[camera_id] = processed


            ret, buffer = await asyncio.to_thread(cv2.imencode, '.jpg', processed)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # await asyncio.sleep(interval)  # 控制快照采集速率

    except Exception as e:
        print(f"摄像头连接失败：{e}")
        traceback.print_exc()  # 这里打印完整的错误堆栈信息


async def background_camera_task(camera_id: str, liveStreamType: str = None):
    """
    后台任务：单个摄像头持续读取帧，并将最新的帧保存到全局字典中
    """
    db = get_db();
    global latest_frames
    latest_frames = {}
    while True:
        camera_url = get_camera_url(db, camera_id)
        if not camera_url:
            print(f"摄像头 {camera_id} 的 URL 未找到")
            return

        try:
            async for frame in generate_frames(camera_url, camera_id, liveStreamType):
                # 持续更新最新帧
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