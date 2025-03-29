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
detector = Detector("./weights/yolov8n.pt")

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

#保存处理后的帧/信息函数
# def save_processed_frame(frame, processedImg, detailedResult):
#
#     # 保存原始帧和处理后的图片
#     timestamp = time.time_ns()
#     origin_name = f"original_{timestamp}.jpg"
#     file_name = f"processed_{timestamp}.jpg"
#     file_path = os.path.join(SAVE_DIR, file_name)
#     origin_path = os.path.join(UPLOAD_FOLDER, origin_name)
#     cv2.imwrite(origin_path, frame)
#     cv2.imwrite(file_path, processedImg)
#
#     # **构造 JSON 数据**
#     result_data = {
#         "filename": file_name,
#         "labels": detailedResult["labels"],
#         "confidence": detailedResult["confidence"],
#         "count": detailedResult["count"]
#     }
#
#     # **存储 JSON 结果**
#     json_file_path = os.path.join(INFO_DIR, f"processed_{timestamp}.json")
#     with open(json_file_path, "w") as json_file:
#         json.dump(result_data, json_file, indent=4)
#
#     print(f"Saved: {file_name} and {json_file_path}")


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

# **视频流生成器——用于处理RSTP协议的摄像头**
async def generate_frames(RTSP_URL:str,camera_id:str):
    """
        :param rtsp_url: 摄像头地址
    """
    #设置超时时间
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

    # 如果还是没打开，直接 return，结束生成器
    if not cap.isOpened():
        print("RTSP摄像头无法连接，已放弃重试")
        return

    print("RTSP摄像头打开成功，开始读帧...")

    db = next(get_db())
    camera_name = get_camera_name_by_id(db,camera_id)

    time_window = 10
    traffic_data = []   # 存储 (time, hold_volume, flow_volume)
    label_map = get_label_mapping(db)
    start_time = time.time()

    # 预警状态变量
    warning_state = "正常"
    warning_start_time = None
    warning_end_time = None
    alert_id = None
    alert_image = None
    last_alert_sent = None

    # 预警检测的历史记录
    hold_warning_count = 0
    flow_warning_count = 0
    hold_clear_count = 0
    flow_clear_count = 0

    # 预警状态变量
    vehicle_warning_state = {}  # 存储每个 alertId 的状态
    vehicle_alert_start_time = {}  # 预警开始时间
    vehicle_clear_count = {}  # 预警清除计数器
    clearThreshold = 3  # 连续 N 个 time_window 未检测到该车辆则结束预警

    while True:
        success, frame = cap.read()
        if not success:
            print("无法接收帧，等待重试...")
        else:
            print("接收到帧")

        #这里获取时间
        current_time = time.time()

        processed ,detailedResult ,hitBarResult= process_frame(frame)

        #获取camera_rule的数据
        camera_rule_response = getCameraRule(camera_id)
        if camera_rule_response["code"] != "200":
            print(f"摄像头规则查询失败: {camera_rule_response['msg']}")
        else:
            camera_rules = camera_rule_response["data"]["cameraRules"]

            # **解析 camera_rules**——————其实可以直接从camera_rule表中查询数据。。。。
            car_category = []
            labels_equal_hold_ids = {}
            labels_equal_flow_ids = {}
            maxVehicleHoldNum = 0
            maxVehicleFlowNum = 0
            minVehicleHoldNum = 0
            minVehicleFlowNum = 0
            maxContinuousTimePeriod = 0
            minContinuousTimePeriod = 0
            rule_type = "未知规则"

            for rule in camera_rules:
                rule_value = rule.get("ruleValue")

                if rule_value == "1":
                    car_category = rule.get("labelId", [])  # 直接赋值，无需 json.loads

                elif rule_value == "2":
                    vehicle_hold = rule.get("VehicleHold", {})
                    data = vehicle_hold.get("LabelsEqual", [])
                    # data 可能是列表，也可能是字符串
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            print("labelsEqual 解析出错", data)
                            data = []  # 或者 continue
                    labels_equal_hold_ids = {
                        label["labelId"]: label["labelHoldNum"] for label in data
                    }
                    maxVehicleHoldNum = int(vehicle_hold.get("maxVehicleHoldNum", 0))
                    minVehicleHoldNum = int(vehicle_hold.get("minVehicleHoldNum", 0))
                    maxContinuousTimePeriod = int(vehicle_hold.get("maxContinuousTimePeriod", 0))
                    minContinuousTimePeriod = int(vehicle_hold.get("minContinuousTimePeriod", 0))

                elif rule_value == "3":
                    vehicle_flow = rule.get("VehicleFlow", {})
                    data = vehicle_flow.get("LabelsEqual", [])
                    # data 可能是列表，也可能是字符串
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            print("labelsEqual 解析出错", data)
                            data = []  # 或者 continue
                    labels_equal_flow_ids = {
                        label["labelId"]: label["labelEqualNum"] for label in data
                    }
                    maxVehicleFlowNum = int(vehicle_flow.get("maxVehicleFlowNum", 0))
                    minVehicleFlowNum = int(vehicle_flow.get("minVehicleFlowNum", 0))

            #计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中

            #车辆类型预警逻辑--------这里的car_category是id，和detailresult对不上，记得改——————————————————
            detected_vehicles = [label for label in detailedResult.get("count", {}).keys() if label in car_category]

            if detected_vehicles:
                for vehicle in detected_vehicles:
                    if vehicle not in vehicle_warning_state:
                        alert_id = str(uuid.uuid4())
                        alert_image = f"{alert_id}.jpg"
                        cv2.imwrite(f"/alerts/on/{alert_image}", frame)        #还有这里的图片存储，存哪？如何访问？——————————

                        rule_type = "1"
                        rule_remark = f"检测到违规车辆: {vehicle}"

                        saveAlert(alert_id, camera_id, camera_name, 1, datetime.now(), None, None, alert_image,
                                  rule_type, rule_remark)
                        sio.emit("updateHappeningAlert", {
                            "alertId": alert_id,
                            "cameraId": camera_id,
                            "cameraName": camera_name
                        })

                        # **记录该车辆的预警信息**
                        vehicle_warning_state[vehicle] = alert_id
                        vehicle_alert_start_time[vehicle] = datetime.now()
                        vehicle_clear_count[vehicle] = 0  # 预警清除计数器重置

            else:
                # **如果 `detailedResult` 中未检测到 `car_category` 车辆**
                for vehicle in list(vehicle_warning_state.keys()):
                    vehicle_clear_count[vehicle] += 1

                    if vehicle_clear_count[vehicle] >= clearThreshold:
                        alert_id = vehicle_warning_state[vehicle]
                        alert_end_time = current_time

                        saveAlert(alert_id, camera_id, camera_name, 2, vehicle_alert_start_time[vehicle],
                                  alert_end_time, None, alert_image, rule_type, f"{vehicle} 车辆消失，预警结束")

                        del vehicle_warning_state[vehicle]
                        del vehicle_alert_start_time[vehicle]
                        del vehicle_clear_count[vehicle]

                        print(f"[✅ 车辆类型预警解除] {vehicle} 已消失，预警结束")


            # 计算 hold 和 flow 的交通当量
            hold_volume = calculate_traffic_volume_hold(detailedResult, labels_equal_hold_ids)
            flow_volume = calculate_traffic_volume_flow(hitBarResult, labels_equal_flow_ids)

            # 根据hitBarResult统计10秒内所有 labelName 的累计总数
            # 计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中
            label_counts = {label_name: 0 for label_name in label_map.values()}  # 初始化所有标签计数为0
            for label_id, count in hitBarResult.get("count", {}).items():
                if label_id in label_map:
                    label_counts[label_map[label_id]] += count

            # 记录数据
            traffic_data.append((current_time, hold_volume, flow_volume,label_counts))

            # **严格控制 10 秒后进行计算**
            if current_time - start_time >= time_window:
                if traffic_data:  # 确保数据不为空
                    avg_hold_volume = sum(h for h, _, _ in traffic_data) / len(traffic_data)
                    avg_flow_volume = sum(f for _, f, _ in traffic_data) / len(traffic_data)

                    # 计算 10 秒内的累计 label 数量
                    aggregated_label_counts = {label: 0 for label in label_map.values()}
                    for _, _, label_dict in traffic_data:
                        for label, count in label_dict.items():
                            aggregated_label_counts[label] += count

                    # 存入数据库
                    save_to_camera_detect_info(camera_id, avg_hold_volume, avg_flow_volume, aggregated_label_counts,
                                               current_time)

                    # **🚨 预警逻辑 🚨**
                    if avg_hold_volume >= maxVehicleHoldNum:
                        hold_warning_count += 1
                        # hold_clear_count = 0
                    else:
                        hold_warning_count = 0
                        # hold_clear_count += 1

                    if avg_flow_volume >= maxVehicleFlowNum:
                        flow_warning_count += 1
                        # flow_clear_count = 0
                    else:
                        flow_warning_count = 0
                        # flow_clear_count += 1

                    if avg_hold_volume <= minVehicleHoldNum:
                        hold_clear_count += 1
                    else:
                        hold_clear_count = 0
                    if avg_flow_volume <= minVehicleFlowNum:
                        flow_clear_count += 1
                    else:
                        flow_clear_count = 0

                        # **连续 N 次触发 "正在发生"**
                    if hold_warning_count >= maxContinuousTimePeriod // time_window or flow_warning_count >= maxContinuousTimePeriod // time_window:
                        if warning_state != "正在发生":
                            warning_state = "正在发生"
                            warning_start_time = current_time
                            alert_id = str(uuid.uuid4())
                            alert_image = f"{alert_id}.jpg"
                            cv2.imwrite(f"/path/to/alerts/{alert_image}", frame)
                            if(hold_warning_count >= maxContinuousTimePeriod // time_window):
                                rule_type = "2"
                                rule_remark = "车辆拥挤度预警"
                            elif(flow_warning_count >= maxContinuousTimePeriod // time_window):
                                rule_type = "3"
                                rule_remark = "车流量预警"

                            saveAlert(
                                alert_id, camera_id, camera_name, 1, warning_start_time, None, None, alert_image,
                                rule_type, rule_remark
                            )

                            sio.emit("updateHappeningAlert", {"alertId": alert_id, "cameraId": camera_id, "cameraName": camera_name})

                    # **连续 N 次触发 "已经发生"**
                    if hold_clear_count >= minContinuousTimePeriod // time_window or flow_clear_count >= minContinuousTimePeriod // time_window:
                        if warning_state == "正在发生":
                            warning_state = "已经发生"
                            warning_end_time = current_time

                            saveAlert(alert_id, camera_id, camera_name, 2, warning_start_time, warning_end_time,
                                            None, alert_image, rule_type, rule_remark)

                # **清空 traffic_data，更新 start_time**
                traffic_data.clear()
                start_time = current_time

        # # **Socket.IO 发送 JSON 结果**
        # sio.emit("detection", detailedResult)

        ret, buffer = cv2.imencode('.jpg', processed)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

#HTTP请求的方式解析MJPEG流
async def generate_frames_http(SNAPSHOT_URL:str,camera_id:str):
    """
        **description**
        通过 HTTP 轮询获取摄像头快照，并逐帧处理。

        **params**
        MJPEG_URL (str): 摄像头的 HTTP MJPEG 地址。

        **returns**
        逐帧返回处理后的 JPEG 数据流。
    """
    try:
        print("摄像头快照模式启动，开始抓取图片...")
        interval = 0.5      #获取快照的时间间隔，默认0.5s
        db = next(get_db())
        camera_name = get_camera_name_by_id(db,camera_id)
        time_window = 10
        traffic_data = []  # 存储 (time, hold_volume, flow_volume)
        label_map = get_label_mapping(db)
        start_time = time.time()

        # 预警状态变量
        warning_state = "正常"
        warning_start_time = None
        warning_end_time = None
        alert_id = None
        alert_image = None
        last_alert_sent = None

        # 预警检测的历史记录
        hold_warning_count = 0
        flow_warning_count = 0
        hold_clear_count = 0
        flow_clear_count = 0

        # 预警状态变量
        vehicle_warning_state = {}  # 存储每个 alertId 的状态
        vehicle_alert_start_time = {}  # 预警开始时间
        vehicle_clear_count = {}  # 预警清除计数器
        clearThreshold = 3  # 连续 N 个 time_window 未检测到该车辆则结束预警

        vehicle_history = {}  # 格式：{ vehicle_no: [ { "time": timestamp, "line": line_name, "label": label }, ... ] }
        history_last_checked = time.time()

        camera_line_response = get_camera_line(db, camera_id)
        lines = []
        if camera_line_response["code"] == "200" and camera_line_response["data"].get("cameraLines"):
            lines = camera_line_response["data"]["cameraLines"]
        else:
            print("该摄像头没有检测线")

        hitBars = []

        while True:
            response = requests.get(SNAPSHOT_URL)  # 直接请求单张图片
            if response.status_code != 200:
                print(f"无法获取摄像头快照: {response.status_code}")
                time.sleep(1)  # 失败时等待 1 秒再尝试
                continue

            # ————这里获取时间
            current_time = time.time()

            # 解析图像
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is None:
                print("无法解码快照，跳过...")
                continue

            # 根据获取的检测线数据构造 hitBars 对象
            if not hitBars:
                frame_h, frame_w = frame.shape[:2]
                for i, line in enumerate(lines):
                    startPoint = (int(line["cameraLineStartX"]), int(line["cameraLineStartY"]))
                    endPoint = (int(line["cameraLineEndX"]), int(line["cameraLineEndY"]))
                    # 主检测线 name 设为 "0"，其他检测线依次为 "1", "2", "3"……
                    name = "0" if line.get("isMainLine", False) else str(i + 1)
                    hb = hitBar(
                        imgSize=(frame_h, frame_w),
                        startPoint=startPoint,
                        endPoint=endPoint,
                        name=name,
                        # 如有其他需要的参数，可在此添加
                    )
                    hitBars.append(hb)

            processed, detailedResult ,hitBarResult= process_frame(frame,hitBars=hitBars)


            # 获取camera_rule的数据
            camera_rule_response = getCameraRule(db,camera_id)
            if camera_rule_response["code"] != "200":
                print(f"摄像头规则查询失败: {camera_rule_response['msg']}")
            else:
                camera_rules = camera_rule_response["data"]["cameraRules"]

                # **解析 camera_rules**——————其实可以直接从camera_rule表中查询数据。。。。这个规则的解析放在外面函数里把
                car_category = []
                labels_equal_hold_ids = {}
                labels_equal_flow_ids = {}
                maxVehicleHoldNum = 0
                maxVehicleFlowNum = 0
                minVehicleHoldNum = 0
                minVehicleFlowNum = 0
                maxContinuousTimePeriod = 0
                minContinuousTimePeriod = 0
                rule_type = "未知规则"
                cameraStartLine = {}
                cameraEndLine = {}
                camera_start_line_id = ""
                camera_end_line_id = ""
                rule_first_camera_line_id = ""

                for rule in camera_rules:
                    rule_value = rule.get("ruleValue")

                    if rule_value == "1":
                        rule_first_label = rule.get("label",[])
                        car_category = rule_first_label.get("labelId", [])  # 直接赋值，无需 json.loads
                        rule_first_camera_line_id = rule_first_label.get("cameraLineId","")

                    elif rule_value == "2":
                        vehicle_hold = rule.get("VehicleHold", {})
                        data = vehicle_hold.get("LabelsEqual", [])
                        # print("raw data =", data)
                        # data 可能是列表，也可能是字符串
                        # if isinstance(data, str):
                        #     try:
                        #         data = json.loads(data)
                        #         print("after json.loads =", data)
                        #     except json.JSONDecodeError:
                        #         print("labelsEqual 解析出错", data)
                        #         data = []  # 或者 continue
                        labels_equal_hold_ids = {
                            label["labelId"]: label["labelHoldNum"] for label in data
                        }
                        maxVehicleHoldNum = float(vehicle_hold.get("maxVehicleHoldNum", 0))
                        minVehicleHoldNum = float(vehicle_hold.get("minVehicleHoldNum", 0))
                        maxContinuousTimePeriod = int(vehicle_hold.get("maxContinuousTimePeriod", 0))
                        minContinuousTimePeriod = int(vehicle_hold.get("minContinuousTimePeriod", 0))

                    elif rule_value == "3":
                        vehicle_flow = rule.get("VehicleFlow", {})
                        data = vehicle_flow.get("LabelsEqual", [])
                        print("raw data =", data)
                        # data 可能是列表，也可能是字符串
                        if isinstance(data, str):
                            try:
                                data = json.loads(data)
                                print("after json.loads =", data)
                            except json.JSONDecodeError:
                                print("labelsEqual 解析出错", data)
                                data = []  # 或者 continue
                        labels_equal_flow_ids = {
                            label["labelId"]: label["labelEqualNum"] for label in data
                        }
                        maxVehicleFlowNum = float(vehicle_flow.get("maxVehicleFlowNum", 0))
                        minVehicleFlowNum = float(vehicle_flow.get("minVehicleFlowNum", 0))
                        cameraStartLine = vehicle_flow.get("cameraStartLine", {})
                        if cameraStartLine:
                            camera_start_line_id = cameraStartLine.get("cameraLineId", "")
                        cameraEndLine = vehicle_flow.get("cameraEndLine", {})
                        if cameraEndLine:
                            camera_end_line_id = cameraEndLine.get("cameraLineId", "")


            # flow_for_line = {}  # 用于存储每条检测线的 flow 当量，键为检测线的名称
            flow_for_line = calculate_traffic_volume_flow(hitBarResult, labels_equal_flow_ids)
            # 示例：打印各检测线的 flow 当量
            print("各检测线 Flow 当量：", flow_for_line)

            #起止线检测
            if camera_start_line_id is not None and camera_end_line_id is not None and camera_start_line_id != camera_end_line_id:
                # 在每一帧处理后，将车辆检测结果存入 history
                # 假设 hitBarResult 中每个检测线的 hitDetails 内含车辆检测信息，其中 "ID" 为车辆唯一标识
                for hb in hitBarResult:
                    line_name = hb.get("name", "unknown")
                    for detail in hb.get("hitDetails", []):
                        vehicle_no = detail.get("ID")  # 车辆唯一标识
                        if not vehicle_no:
                            continue
                        detection_record = {
                            "time": current_time,
                            "line": line_name,
                            "label": detail.get("cat"),
                        }
                        if vehicle_no not in vehicle_history:
                            vehicle_history[vehicle_no] = []
                        vehicle_history[vehicle_no].append(detection_record)

                # -----------------------------
                # 每分钟检查一次车辆历史记录，并计算从起始线到终止线的当量及方向
                if current_time - history_last_checked >= 60:
                    for vehicle_no, records in list(vehicle_history.items()):
                        # 保留最近1分钟内的记录
                        records = [r for r in records if current_time - r["time"] <= 60]
                        if not records:
                            del vehicle_history[vehicle_no]
                            continue
                        vehicle_history[vehicle_no] = records

                        # 筛选出同时在历史记录中出现过起始和终止检测线的车辆
                        vehicles_through_channel = {}
                        for vehicle_no, records in vehicle_history.items():
                            detected_lines = {r["line"] for r in records}
                            if camera_start_line_id in detected_lines and camera_end_line_id in detected_lines:         #好像这里的id不太对的上
                                vehicles_through_channel[vehicle_no] = records

                        # 对每辆车计算方向及其他信息
                        for vehicle_no, records in vehicles_through_channel.items():
                            # 按时间排序，确定起始和终止检测记录
                            sorted_records = sorted(records, key=lambda r: r["time"])
                            start_line = sorted_records[0]["line"]
                            end_line = sorted_records[-1]["line"]

                            # 判断车辆方向
                            if start_line == camera_start_line_id and end_line == camera_end_line_id:
                                direction = "正向"
                            elif start_line == camera_end_line_id and end_line == camera_start_line_id:
                                direction = "逆向"
                            else:
                                direction = "未知"

                            # 直接取最早记录的 label 作为车辆类型（即车辆 id 对应的 label）
                            vehicle_type = sorted_records[0]["label"]

                            # 存储车辆信息：汽车No、类型、起线、止线、检测时间（使用当前时间）以及方向
                            saveCarThroughFixedRoute(db, vehicle_no, vehicle_type, start_line, end_line,
                                                     current_time, direction)
                            print(f"{vehicle_type} {vehicle_no}")

                            # 处理完后从history中移除该车辆记录
                            del vehicle_history[vehicle_no]

                        # 获取 label 映射（label_id -> label_name）
                        label_mapping = get_label_mapping(db)
                        # 为了根据记录中存储的 label_name 获取 label_id，这里构造反向映射：label_name -> label_id
                        inv_label_mapping = {v: k for k, v in label_mapping.items()}

                        total_flow_equivalent = 0
                        for vehicle_no, records in vehicles_through_channel.items():
                            # 统计该车辆在1分钟内各 label 的累计数量
                            label_counts = {}
                            for rec in records:
                                label_name = rec["label"]  # hitDetails中记录的 cat，一般为 label_name
                                label_counts[label_name] = label_counts.get(label_name, 0) + rec["count"]

                            # 计算该车辆的当量：遍历 label_counts，若对应的 label_id 存在于 labels_equal_flow_ids 则计算当量
                            vehicle_equivalent = 0
                            for label_name, count in label_counts.items():
                                label_id = inv_label_mapping.get(label_name)
                                if label_id and label_id in labels_equal_flow_ids:
                                    vehicle_equivalent += count * labels_equal_flow_ids[label_id]
                            total_flow_equivalent += vehicle_equivalent


                        # 丢弃所有超过1分钟未更新的记录（这里只保留有更新的记录）
                        for vehicle_no in list(vehicle_history.keys()):
                            vehicle_history[vehicle_no] = [r for r in vehicle_history[vehicle_no] if
                                                           current_time - r["time"] <= 60]
                            if not vehicle_history[vehicle_no]:
                                del vehicle_history[vehicle_no]
                        history_last_checked = current_time

            #假如规则中的起始线和终止线为空，则设置为主检测线
            if camera_start_line_id is None:
                camera_start_line_id = "0"

            if camera_end_line_id is None:
                camera_end_line_id = "0"

            # 此时目标检测线就是主检测线，此时 target_line_id 设为 "0"
            target_line_id = "0"

            #目标检测线的flow当量
            target_flow = flow_for_line.get(target_line_id,0)
            print(f"目标检测线/主检测线 {target_line_id} 的 Flow 当量：", target_flow)

            # 计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中


            # 计算 hold 和 flow 的交通当量
            hold_volume = calculate_traffic_volume_hold(detailedResult, labels_equal_hold_ids)["hold_volume"]

            # 根据hitBarResult统计10秒内所有 labelName 的累计总数
            # 计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中
            # 车辆类型预警逻辑--------这里的car_category是id，和label对不上，记得改-------
            # detected_vehicles = [label for label in label_counts.keys() if label in car_category]

            #这是所有检测线的所有结果的累计，好像没有什么用处
            for label_id, count in hitBarResult.get("Accumulator", {}).items():
                if label_id in label_map:
                    label_counts[label_map[label_id]] += count

            # 记录数据
            traffic_data.append((current_time, hold_volume, target_flow, label_counts))         #注意这里只存入了主检测线时的车流量检测

            # 同时，为后续 10 秒窗口内的统计，我们建立一个按检测线分类的存储结构
            # 例如，lineWiseTrafficData 为字典：键为检测线名称，值为该线在窗口内各帧的 flow 当量
            if 'lineWiseTrafficData' not in globals():
                lineWiseTrafficData = {}
            for line_name, flow in flow_for_line.items():
                if line_name not in lineWiseTrafficData:
                    lineWiseTrafficData[line_name] = []
                lineWiseTrafficData[line_name].append(flow)

            # 维护各检测线的预警计数，使用字典存储
            if 'flow_warning_count_dict' not in globals():
                flow_warning_count_dict = {}
            if 'flow_clear_count_dict' not in globals():
                flow_clear_count_dict = {}

            # 将规则中车辆类型 id 转换为 label 名称列表
            car_category_names = [label_map.get(cid) for cid in car_category if cid in label_map]
            # 从 hitBarResult 中查找检测线 rule_first_camera_line_id 对应的记录:这两个id好像对应不上————-------------要改


            # 车辆类型预警逻辑--------这里的car_category是id，和label对不上，记得改-------car_category_names是name，已改
            #这里的预警逻辑不对，应该是根据规则中的某条检测线进行的。。。。。
            target_hitbar = None
            for hb in hitBarResult:
                if hb.get("name") == rule_first_camera_line_id:
                    target_hitbar = hb
                    break
            if target_hitbar:
                accumulator = target_hitbar.get("Accumulator", {})
                # 从 accumulator 中提取检测到的车辆类型（键为 label 名称）列表
                detected_vehicle_types = list(accumulator.keys())
                # 如果存在任一车辆类型属于规则定义的 car_category_names，则触发车辆类型预警
                detected_vehicles = [vt for vt in detected_vehicle_types if vt in car_category_names]

                if detected_vehicles:
                    for vehicle in detected_vehicles:
                        if vehicle not in vehicle_warning_state:
                            alert_id = str(uuid.uuid4())
                            alert_image = f"{alert_id}.jpg"
                            cv2.imwrite(f"/alerts/on/{alert_image}", frame)  # 还有这里的图片存储，存哪？如何访问？——————————

                            rule_type = "1"
                            rule_remark = f"检测到违规车辆: {vehicle}"

                            saveAlert(alert_id, camera_id, camera_name, 1, datetime.now(), None, None, alert_image,
                                      rule_type, rule_remark)
                            sio.emit("updateHappeningAlert", {
                                "alertId": alert_id,
                                "cameraId": camera_id,
                                "cameraName": camera_name
                            })

                            # **记录该车辆的预警信息**
                            vehicle_warning_state[vehicle] = alert_id
                            vehicle_alert_start_time[vehicle] = datetime.now()
                            vehicle_clear_count[vehicle] = 0  # 预警清除计数器重置

                else:
                    rule_type = "1"
                    # **如果 `detailedResult` 中未检测到 `car_category` 车辆**
                    for vehicle in list(vehicle_warning_state.keys()):
                        vehicle_clear_count[vehicle] += 1

                        if vehicle_clear_count[vehicle] >= clearThreshold:
                            alert_id = vehicle_warning_state[vehicle]
                            alert_end_time = current_time

                            saveAlert(alert_id, camera_id, camera_name, 2, vehicle_alert_start_time[vehicle],
                                      alert_end_time, None, alert_image, rule_type, f"{vehicle} 车辆消失，预警结束")

                            del vehicle_warning_state[vehicle]
                            del vehicle_alert_start_time[vehicle]
                            del vehicle_clear_count[vehicle]

                            print(f"[✅ 车辆类型预警解除] {vehicle} 已消失，预警结束")


            # **严格控制 10 秒后进行计算**
            if current_time - start_time >= time_window:
                if traffic_data:  # 确保数据不为空
                    avg_hold_volume = sum(h for _, h, _, _ in traffic_data) / len(traffic_data)

                    # 计算 10 秒内的累计 label 数量
                    aggregated_label_counts = {label: 0 for label in label_map.values()}
                    for _,_, _, label_dict in traffic_data:
                        for label, count in label_dict.items():
                            aggregated_label_counts[label] += count

                    # 存入数据库
                    save_to_camera_detect_info(db,camera_id, avg_hold_volume, target_flow, aggregated_label_counts,
                                               current_time)

                    # 如果 active_alerts 不存在，则初始化
                    if 'active_alerts' not in globals():
                        active_alerts = {}  # 键为 rule_type（如 "2" 或 "3"），值为预警详细信息字典

                    # **🚨 预警逻辑 🚨**
                    if avg_hold_volume >= maxVehicleHoldNum:
                        hold_warning_count += 1
                        # hold_clear_count = 0
                    else:
                        hold_warning_count = 0
                        # hold_clear_count += 1

                    if target_flow >= maxVehicleFlowNum:
                        flow_warning_count += 1
                        # flow_clear_count = 0
                    else:
                        flow_warning_count = 0
                        # flow_clear_count += 1

                    if avg_hold_volume <= minVehicleHoldNum:
                        hold_clear_count += 1
                    else:
                        hold_clear_count = 0
                    if target_flow <= minVehicleFlowNum:
                        flow_clear_count += 1
                    else:
                        flow_clear_count = 0

                        # **连续 N 次触发 "正在发生"**
                    if hold_warning_count >= maxContinuousTimePeriod // time_window or flow_warning_count >= maxContinuousTimePeriod // time_window:
                        if (hold_warning_count >= maxContinuousTimePeriod // time_window):
                            rule_type = "2"
                            rule_remark = "车辆拥挤度预警"
                        elif (flow_warning_count >= maxContinuousTimePeriod // time_window):
                            rule_type = "3"
                            rule_remark = "车流量预警"

                            # 如果该类型预警还没有记录，则新增预警，否则不重复生成
                            if rule_type not in active_alerts:
                                warning_state = "正在发生"
                                warning_start_time = current_time
                                new_alert_id = str(uuid.uuid4())
                                alert_image = f"{new_alert_id}.jpg"
                                cv2.imwrite(f"/alerts/on/{alert_image}", frame)

                                # 新增预警记录（alert_type=1 表示预警开始）
                                saveAlert(new_alert_id, camera_id, camera_name, 1, warning_start_time, None, None,
                                          alert_image,
                                          rule_type, rule_remark)
                                sio.emit("updateHappeningAlert", {
                                    "alertId": new_alert_id,
                                    "cameraId": camera_id,
                                    "cameraName": camera_name
                                })
                                # 记录该预警状态到字典中
                                active_alerts[rule_type] = {
                                    "alert_id": new_alert_id,
                                    "warning_start_time": warning_start_time,
                                    "alert_image": alert_image,
                                    "rule_remark": rule_remark
                                }

                    # **连续 N 次触发 "已经发生"**
                    if hold_clear_count >= minContinuousTimePeriod // time_window or flow_clear_count >= minContinuousTimePeriod // time_window:
                        if warning_state == "正在发生":
                            warning_state = "已经发生"
                            warning_end_time = current_time

                            # 对字典中所有预警进行更新，使用原先记录的 alert_id
                            for rule_type, alert_info in active_alerts.items():
                                alert_id = alert_info["alert_id"]
                                warning_start_time = alert_info["warning_start_time"]
                                alert_image = alert_info["alert_image"]
                                rule_remark = alert_info["rule_remark"]
                                # 更新预警（alert_type=2 表示预警结束）
                                saveAlert(alert_id, camera_id, camera_name, 2, warning_start_time, warning_end_time,
                                          None, alert_image, rule_type, rule_remark)
                            # 清空字典，预警状态更新完毕
                            active_alerts.clear()

                    # **清空 traffic_data，更新 start_time**
                traffic_data.clear()
                start_time = current_time


            # ————detailresult有效结果保存到数据库中————从上一次保存到这一次间隔十秒钟count的和
                #————还要计算一段时间内的车的拥挤度：求和【此label交通当量值*这个label的数量】，
                        # 从detailresult中获取的数据进行计算。————这里是为了车的拥挤度预警
                        #（其中每个label的交通当量的设置值要根据此摄像头的camerarule中设置的来计算）当连续maxContinuousTimePeriod秒的帧计算出的交通当量都大于等于maxVihicleHoldNum后显示预警状态正在发生，当检测到交通当量小于等于minVihicleHoldNum且持续了minContinuousTimePeriod秒时，将预警状态置为"已经发生"。这里的数据要保存到alert数据表中

            # —————hitbarresult有效结果保存到数据库中————统计从上一次保存到这一次间隔十秒钟count的和
                #还要hitbarresult中的数据进行计算，和上面计算逻辑一样————这里是为了车流量预警

            # **Socket.IO 发送 JSON 结果**
            # await sio.emit("detection", detailedResult)

            ret, buffer = cv2.imencode('.jpg', processed)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            await asyncio.sleep(interval)  # 控制快照采集速率

    except Exception as e:
        print(f"HTTP协议摄像头连接失败：{e}")
        traceback.print_exc()  # 这里打印完整的错误堆栈信息

# **FastAPI 端点：返回 RTSP 直播流**
@router.get("/storage/getCameraLiveStream")
async def proxy_video_feed(
        cameraId: str = Query(..., description="摄像头 ID"),
        liveStreamType: str = Query(..., description="直播流类型"),
        # X_HAHACAR_TOKEN: str = Header(..., description="管理员访问权限 Token"),
        token: str = Query(..., description="管理员访问权限 Token"),
        db: Session = Depends(get_db)
        ):
    """
    **description**
    代理 RTSP 视频流，并返回处理后的 MJPEG 流

    **params**
    - cameraId (str): 摄像头 ID（必须）
    - liveStreamType (str): 直播流类型（可选，'preview' 或 'full'，默认 'preview'）
    - token (str): 访问权限 Token

    **returns**
    - StreamingResponse: 返回 MJPEG 视频流
    """
    # **验证管理员权限**
    token_payload = verify_jwt_token(token)
    if not token_payload or not token_payload.get("is_admin"):
        return {"code": "403", "msg": "Unorthrize", "data": {}}

    #获取摄像头URL
    cameraURL = get_camera_url(db, cameraId)
    if not cameraURL:
        return JSONResponse(content={"code": "404", "data": {}, "msg": "Camera not found"}, status_code=404)


    #这里要新增获取摄像头类型，根据是http还是rstp来判断使用哪种处理方法
    if cameraURL.startswith("http"):
        print(f"正在拉取 HTTP 直播流: {cameraURL}")
        return StreamingResponse(generate_frames_http(cameraURL,cameraId), media_type="multipart/x-mixed-replace; boundary=frame" )
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

