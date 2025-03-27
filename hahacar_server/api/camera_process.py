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
from services.camera_rule_service import getCameraRule
from services.camera_service import get_camera_url, get_camera_name_by_id
from services.labels_service import getLabels
from services.user_service import is_admin
from util.detector import Detector
from fastapi.responses import JSONResponse, FileResponse
from api.socket_manager import sio

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

#检测线还没考虑。。。。。。。。。。。
def calculate_traffic_volume_flow(hitbarResult: list,labels_equal_flow_ids: dict) -> dict:
    flow_volume = 0
    db = next(get_db())
    label_mapping = get_label_mapping(db)
    # 转换 labels_equal_flow_ids，将 labelId 替换为 labelName
    labels_equal_flow_names = {
        label_mapping.get(labelId, labelId): value  # 如果 labelId 不在映射中，则保留原值
        for labelId, value in labels_equal_flow_ids.items()
    }

    #如果是主要检测线就不需要循环-----------还有591行
    for hbResult in hitbarResult:
        for label, count in hbResult.items():
            if label in labels_equal_flow_names:
                flow_volume += count * int(labels_equal_flow_names[label])

    return {
        "flow_volume": flow_volume
    }

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
def process_frame(frame):
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
                                                   verbosity=2);
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
                        cv2.imwrite(f"/path/to/alerts/{alert_image}", frame)        #还有这里的图片存储，存哪？如何访问？——————————

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

            processed, detailedResult ,hitBarResult= process_frame(frame)

            # 获取camera_rule的数据
            camera_rule_response = getCameraRule(db,camera_id)
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

                # 计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中

                # 车辆类型预警逻辑--------这里的car_category是id，和detailresult对不上，记得改——————————————————
                detected_vehicles = [label for label in detailedResult.get("count", {}).keys() if label in car_category]

                if detected_vehicles:
                    for vehicle in detected_vehicles:
                        if vehicle not in vehicle_warning_state:
                            alert_id = str(uuid.uuid4())
                            alert_image = f"{alert_id}.jpg"
                            cv2.imwrite(f"/path/to/alerts/{alert_image}", frame)  # 还有这里的图片存储，存哪？如何访问？——————————

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
                hold_volume = calculate_traffic_volume_hold(detailedResult, labels_equal_hold_ids)["hold_volume"]
                flow_volume = calculate_traffic_volume_flow(hitBarResult, labels_equal_flow_ids)["flow_volume"]

                # 根据hitBarResult统计10秒内所有 labelName 的累计总数
                # 计算各种类型汽车car_counts在十秒中的累计保存到数据库中，首先要通过getLabels方法获取labelid和labelname的映射关系，再统计十秒中该种类型汽车的合计保存到camera_detect_info表中
                label_counts = {label_name: 0 for label_name in label_map.values()}  # 初始化所有标签计数为0
                for hbResult in hitBarResult:
                    for label, count in hbResult.items():
                        if label in label_counts:
                            label_counts[label] += count

                # for label_id, count in hitBarResult.get("count", {}).items():
                #     if label_id in label_map:
                #         label_counts[label_map[label_id]] += count

                # 记录数据
                traffic_data.append((current_time, hold_volume, flow_volume, label_counts))

                # **严格控制 10 秒后进行计算**
                if current_time - start_time >= time_window:
                    if traffic_data:  # 确保数据不为空
                        avg_hold_volume = sum(h for _, h, _, _ in traffic_data) / len(traffic_data)
                        avg_flow_volume = sum(f for _,_, f, _ in traffic_data) / len(traffic_data)

                        # 计算 10 秒内的累计 label 数量
                        aggregated_label_counts = {label: 0 for label in label_map.values()}
                        for _,_, _, label_dict in traffic_data:
                            for label, count in label_dict.items():
                                aggregated_label_counts[label] += count

                        # 存入数据库
                        save_to_camera_detect_info(db,camera_id, avg_hold_volume, avg_flow_volume, aggregated_label_counts,
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
                                if (hold_warning_count >= maxContinuousTimePeriod // time_window):
                                    rule_type = "2"
                                    rule_remark = "车辆拥挤度预警"
                                elif (flow_warning_count >= maxContinuousTimePeriod // time_window):
                                    rule_type = "3"
                                    rule_remark = "车流量预警"

                                saveAlert(
                                    alert_id, camera_id, camera_name, 1, warning_start_time, None, None, alert_image,
                                    rule_type, rule_remark
                                )

                                sio.emit("updateHappeningAlert",
                                         {"alertId": alert_id, "cameraId": camera_id, "cameraName": camera_name})

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

            time.sleep(interval)  # 控制快照采集速率

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

