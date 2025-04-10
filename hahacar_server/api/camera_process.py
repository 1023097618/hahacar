import asyncio
import json
import os
import traceback
import uuid
from datetime import datetime
import time as t

import cv2
import numpy as np
import requests
import aiohttp

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from api.camera import authenticate_admin
from core.security import verify_jwt_token
from dependencies.database import get_db_session
from models.alert import Alert
from services.alerts_service import saveAlert
from services.camera_detect_info_service import save_to_camera_detect_info
from services.camera_line_service import get_camera_line
from services.camera_rule_service import getCameraRule
from services.camera_service import get_camera_url, get_camera_name_by_id
from services.camera_status_service import update_camera_status
from services.car_through_route_service import saveCarThroughFixedRoute, get_all_car_no
from services.labels_service import getLabels
from services.user_service import is_admin
from services.warning_service import process_accident_warning, process_vehicle_reservation_warning, \
    process_traffic_flow_warning, process_vehicle_congestion_warning, process_vehicle_type_pre_warning
from util.detector import Detector
from util.hitBar import hitBar

router = APIRouter(prefix="/api")
URL = "http://localhost:8081"
MODEL_FOR_DETECTOR = "util/weights/yolov8n.pt"

detectors = {}
latest_frames = {}

UPLOAD_FOLDER = os.path.abspath("./static/camera/uploads/")
SAVE_DIR = os.path.abspath("./static/camera/frames/")
INFO_DIR = os.path.abspath("./static/camera/info/")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)


def get_label_mapping(db: Session) -> dict:
    labels = getLabels(db)
    return labels


def update_label_map(label_map, rule_label):
    for item in rule_label:
        label_id = item['labelId']
        #本来以为这里又是后端的问题，结果我接口就是这么命名的，我也不知道我是不是脑抽了
        if 'labelEqualNum' in item:
            label_equal_num = item['labelEqualNum']
        if 'labelHoldNum' in item:
            label_equal_num = item['labelHoldNum']
        for label in label_map:
            if label.label_id == str(label_id):
                label.default_equal = str(label_equal_num)
                break


def calculate_traffic_volume_hold(detailed_result, label_mapping):
    """
    :param detailed_result: 一个含有 'count' 字段的字典，形如 {"count": {"car": 1, "truck": 1}}
    :param label_mapping:   一个包含 VehicleLabel 对象的列表，每个对象有 .name, .default_equal 等属性
    :return: 返回一个类型权重和(整数或浮点)
    """
    # 1. 拿到 count 字典
    counts = detailed_result.get("count", {})  # 形如 {"car": 1, "truck": 1}

    # 2. 构建一个 name->weight 的字典
    name_to_weight = {}
    for label_obj in label_mapping:
        # 假设 label_obj 里有 .name 和 .default_equal 属性
        try:
            weight_val = float(label_obj.default_equal)  # 也可以用 int，看你们实际需要
        except ValueError:
            # 处理转换异常，比如默认为 1
            weight_val = 1.0
        name_to_weight[label_obj.label_name] = weight_val

    # 3. 遍历 count 字典，累计加和
    total_weight = 0.0
    for vehicle_type, vehicle_count in counts.items():
        if vehicle_type in name_to_weight:
            total_weight += vehicle_count * name_to_weight[vehicle_type]
        else:
            # 如果没有找到对应映射，按需求处理
            # 比如：默认给 0，或者给一个固定值
            pass
    return total_weight


def calculate_traffic_volume_flow(hitBarResult: list, custom_flow: dict, db: Session) -> dict:
    flow_for_line = {}
    flow_map = {lid["label_name"]: lid["default_equal"] for lid in custom_flow}
    for hb in hitBarResult:
        line_name = hb.get("name", "unknown")
        line_flow = 0
        accumulator = hb.get("Accumulator", {})
        for label, count in accumulator.items():
            multiplier = flow_map.get(label, 1)
            line_flow += count * int(multiplier)
        flow_for_line[line_name] = line_flow
    return flow_for_line


def build_hitBars(frame, lines: list):
    hitBars = []
    h, w = frame.shape[:2]
    for line in lines:
        sp = (round(float(line["cameraLineStartX"]) * w), round(float(line["cameraLineStartY"]) * h))
        ep = (round(float(line["cameraLineEndX"]) * w), round(float(line["cameraLineEndY"]) * h))
        hb = hitBar(imgSize=(h, w), startPoint=sp, endPoint=ep, name=line.get("cameraLineId"))
        hitBars.append(hb)
    return hitBars


def parse_camera_rules(camera_rules: list) -> dict:
    parsed = {"1": [], "2": [], "3": [], "4": [], "5": []}
    for rule in camera_rules:
        rv = rule.get("ruleValue")
        if rv in parsed:
            parsed[rv].append(rule)
    return parsed


def update_vehicle_history(vehicle_history: dict, hitBarResult: list, current_time: float):
    for hb in hitBarResult:
        line_name = hb.get("name", "unknown")
        for detail in hb.get("hitDetails", []):
            vehicle_no = detail.get("ID")
            if not vehicle_no:
                continue
            rec = {"time": current_time, "line": line_name, "label": detail.get("cat")}
            vehicle_history.setdefault(vehicle_no, []).append(rec)


def process_vehicle_history(vehicle_history: dict, current_time: float, start_line: str, end_line: str,
                            custom_flow: dict, camera_id: str, db: Session) -> float:
    vehicles = {}
    total_flow = 0
    processed = []
    label_mapping = get_label_mapping(db)
    flow_map = {lid: float(custom_flow.get(lid, 1)) for lid in label_mapping.keys()}
    for vehicle_no, records in vehicle_history.items():
        recs = [r for r in records if current_time - r["time"] <= 60]
        if recs:
            vehicle_history[vehicle_no] = recs
            lines = {r["line"] for r in recs}
            if start_line in lines and end_line in lines:
                vehicles[vehicle_no] = recs
        else:
            processed.append(vehicle_no)
    for vehicle_no, recs in vehicles.items():
        sorted_recs = sorted(recs, key=lambda r: r["time"])
        s_line = sorted_recs[0]["line"]
        e_line = sorted_recs[-1]["line"]
        vehicle_type = sorted_recs[0]["label"]
        equiv = flow_map.get(vehicle_type, 1)
        if s_line == start_line and e_line == end_line:
            total_flow += equiv
            saveCarThroughFixedRoute(
                db,
                vehicle_no=vehicle_no,
                vehicle_type=vehicle_type,
                start_line=s_line,
                end_line=e_line,
                current_time=current_time,
                camera_id=camera_id,
            )
        processed.append(vehicle_no)
    for v in processed:
        vehicle_history.pop(v, None)
    return total_flow


def calculate_label_counts(hitBarResult: list, label_map: dict) -> dict:
    counts = {v: 0 for v in label_map.values()}
    for hb in hitBarResult:
        for label, count in hb.get("Accumulator", {}).items():
            if label in counts:
                counts[label] += count
    return counts


def update_lineWiseTrafficData(flow_for_line: dict, data: dict):
    for line, flow in flow_for_line.items():
        data.setdefault(line, []).append(flow)


def aggregate_label_counts(traffic_data: list, label_map: dict) -> dict:
    agg = {v: 0 for v in label_map.values()}
    for _, _, _, cnts in traffic_data:
        for label, count in cnts.items():
            agg[label] += count
    return agg


def save_car_through_line(hitBarResult: list, current_time: float, camera_id: str, label_map: dict, db: Session):
    reverse_map = {v: k for k, v in label_map.items()}
    for hb in hitBarResult:
        line = hb.get("name", "unknown")
        for vehicle_no, type_name in hb.get("Accumulator", {}).items():
            vehicle_ids = get_all_car_no(db, vehicle_no)
            vehicle_type = reverse_map.get(type_name)
            if vehicle_type:
                if vehicle_ids:
                    saveCarThroughFixedRoute(db, vehicle_no=vehicle_no, vehicle_type=vehicle_type, start_line=None,
                                             end_line=line, current_time=current_time, camera_id=camera_id)
                else:
                    saveCarThroughFixedRoute(db, vehicle_no=vehicle_no, vehicle_type=vehicle_type, start_line=line,
                                             end_line=None, current_time=current_time, camera_id=camera_id)


def db_dependency():
    db, close_db = get_db_session()
    try:
        yield db
    finally:
        close_db()


def fetch_frame(source_url: str, cap=None):
    current_time = t.time()
    if source_url.endswith((".mp4", ".avi", ".mov")):
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(source_url)
            if not cap.isOpened():
                return None, current_time, cap
        success, frame = cap.read()
        if not success:
            return None, current_time, cap
        return frame, current_time, cap

    elif source_url.startswith("http") and not source_url.endswith("video.mjpg"):
        try:
            response = requests.get(source_url)
            if response.status_code != 200:
                return None, current_time, cap
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            current_time = t.time()
            return frame, current_time, cap
        except Exception:
            return None, current_time, cap

    elif source_url.startswith("rtsp"):
        if cap is None or not cap.isOpened():
            return None, current_time, cap
        success, frame = cap.read()
        if not success:
            return None, current_time, cap
        return frame, current_time, cap

    elif source_url.endswith("video.mjpg"):
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(source_url)
            if not cap.isOpened():
                return None, current_time, cap
        success, frame = cap.read()
        current_time = t.time()
        if not success:
            return None, current_time, cap
        return frame, current_time, cap
    else:
        return None, current_time, cap


async def frame_producer(source_url: str, cap, frame_queue: asyncio.Queue):
    while True:
        frame, current_time, cap = await asyncio.to_thread(fetch_frame, source_url, cap)
        if frame is not None:
            try:
                frame_queue.put_nowait((frame, current_time))
            except asyncio.QueueFull:
                pass
        await asyncio.sleep(0.03)


async def frame_consumer(camera_id: str, hitBars, frame_queue: asyncio.Queue, time_window: int = 10):
    start_time = t.time()
    processed_frames = []
    while t.time() - start_time < time_window:
        try:
            frame, current_time = await asyncio.wait_for(frame_queue.get(), timeout=0.1)
            processed, detailedResult, hitBarResult = process_frame(frame, hitBars, camera_id)
            processed_frames.append((processed, detailedResult, hitBarResult, current_time))
        except asyncio.TimeoutError:
            continue
    return processed_frames


def process_frame(frame, hitbars, camera_id: str):
    detector = detectors.get(camera_id, Detector(MODEL_FOR_DETECTOR))
    processedImg, detailedResult, hitBarResult = detector.detect(
        frame,
        addingBoxes=True,
        addingLabel=True,
        addingConf=False,
        verbosity=2,
        hitBars=hitbars
    )
    detectors[camera_id] = detector
    return processedImg, detailedResult, hitBarResult


async def generate_frames(source_url: str, camera_id: str, liveStreamType: str = None):
    try:
        cap = None
        if source_url.startswith("rtsp"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
            source_url = f"{source_url}?stream={'full' if liveStreamType == 'full' else 'preview'}"
            cap = cv2.VideoCapture(source_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                return
        interval = 0.5 if source_url.startswith("http") and not source_url.endswith("video.mjpg") else 0.03
        db, close_db = get_db_session()
        try:
            camera_name = get_camera_name_by_id(db, camera_id)
            time_window = 5
            traffic_data = []
            label_map = get_label_mapping(db)
            start_time = t.time()

            warning_start_time = None
            warning_end_time = None
            vehicle_alert_start_time = {}

            clearThreshold = 3

            vehicle_history = {}
            history_last_checked = t.time()

            camera_line_response = get_camera_line(db, camera_id)
            lines = camera_line_response.get("data", {}).get("cameraLines", [])
            main_line = next((l for l in lines if l.get("isMainLine")), None)
            main_line_id = main_line["cameraLineId"] if main_line else None

            hitBars = []
            the_vehicle_history = {}
            # 过去120秒的车流量数据
            detected_vehicles = {}
            accident_active_alerts = {}
            clearAccidentThreshold = 10
            last_success_time = {}
            fail_count = {}
            MAX_FAIL_COUNT = 5
            OFFLINE_THRESHOLD_SECS = 20
            old_online_state = False

            frame_queue = asyncio.Queue(maxsize=500)
            producer_task = asyncio.create_task(frame_producer(source_url, cap, frame_queue))
            save_path = os.path.join(os.path.abspath("."), "frameTest")
            os.makedirs(save_path, exist_ok=True)

            # 与数据库交互是耗时操作，不应该放在while里面一直循环
            camera_rule_response = getCameraRule(db, camera_id)
            camera_rules = camera_rule_response.get("cameraRules", [])
            rules_parsed = parse_camera_rules(camera_rules)
            last_save_time = None
            while True:
                try:
                    frame, current_time = await asyncio.wait_for(frame_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                filename = f"{camera_id}_{current_time}.jpg"
                file_path = os.path.join(save_path, filename)
                # cv2.imwrite(file_path, frame)

                ongoing_alert = db.query(Alert).filter(
                    Alert.camera_id == camera_id,
                    Alert.alert_type == '1'
                ).first()
                has_alert = True if ongoing_alert else False

                if frame is None:
                    fail_count[camera_id] = fail_count.get(camera_id, 0) + 1
                    if fail_count[camera_id] >= MAX_FAIL_COUNT and old_online_state:
                        old_online_state = False
                        await update_camera_status(camera_id, new_online=False, new_alert=has_alert)
                    await asyncio.sleep(0.1)
                    continue

                fail_count[camera_id] = 0
                last_success_time[camera_id] = current_time
                if not old_online_state:
                    old_online_state = True
                    await update_camera_status(camera_id, new_online=True, new_alert=has_alert)

                if not hitBars:
                    hitBars = build_hitBars(frame, lines)

                processed, detailedResult, hitBarResult = process_frame(frame, hitBars, camera_id)


                #这边avg_hold_volume需要每60秒存储到数据表中，存储的方式save_to_camera_detect_info(db, camera_id,  aggregated_counts, current_time)
                #aggregated_counts格式{"car":1,...}
                #labels数据是 ['bus', 'car', 'car', 'car', 'bus', 'car', 'bus', 'car', 'car', 'bus', 'car', 'car', 'car']，你可能需要把它聚类
                labels=detailedResult["labels"]
                aggregated_counts = {}
                for label in labels:
                    if label in aggregated_counts:
                        aggregated_counts[label] += 1
                    else:
                        aggregated_counts[label] = 1

                if last_save_time is None:
                    last_save_time = current_time
                    save_to_camera_detect_info(db, camera_id, aggregated_counts, current_time)
                else:
                    # 计算当前时间与上次存储时间的间隔
                    elapsed_seconds = current_time - last_save_time
                    if elapsed_seconds >= 60:
                        # 时间间隔超过60秒，更新 last_save_time 并存储数据
                        last_save_time = current_time
                        save_to_camera_detect_info(db, camera_id, aggregated_counts, current_time)

                if any(r.get("eventDetect", False) for r in rules_parsed["5"]):
                    accident_detected, accident_active_alerts = await process_accident_warning(
                        detailedResult=detailedResult,
                        frame=frame,
                        current_time=current_time,
                        db=db,
                        camera_id=camera_id,
                        camera_name=camera_name,
                        accident_active_alerts=accident_active_alerts,
                        clearAccidentThreshold=clearAccidentThreshold
                    )



                for rule in rules_parsed["2"]:
                    rule_id = rule.get("rule_id",None)
                    vh = rule.get("VehicleHold", {})
                    data = vh.get("LabelsEqual", [])
                    custom_label = label_map.copy()
                    update_label_map(custom_label, data)
                    #todo 现在还是瞬时值，rule_avg_hold_volume需要改成最近六十秒的平均值
                    rule_avg_hold_volume = calculate_traffic_volume_hold(detailedResult, custom_label)
                    print(f"当前的hold为{rule_avg_hold_volume}")
                    await process_vehicle_congestion_warning(
                        rule_id,
                        rule_avg_hold_volume,
                        current_time,
                        float(vh.get("maxVehicleHoldNum", 0)),
                        float(vh.get("minVehicleHoldNum", 0)),
                        int(vh.get("maxContinuousTimePeriod", 0)),
                        int(vh.get("minContinuousTimePeriod", 0)),
                        frame,
                        db,
                        camera_id,
                        camera_name
                    )



                #此处通过遍历rules_parsed["3"]，这个检测线车流量规则的相关规则，然后送入process_traffic_flow_warning进行判断
                #每辆车的ID值模型传回来是不重复的，所以如果这辆车是第二次检测到那么就是从这条检测线出
                #所以我们需要一个字典，这个字典的键需要是每辆车的ID值来判断这辆车是不是第一次进来
                #这个字典只留存120秒的数据，也就是说如果数据是120秒前的就把它删了
                #根据这个字典计算出前60秒的检测线流量数据，然后把规则传入process_traffic_flow_warning进行预警判断
                # 调用方式
                #          flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_traffic_flow_warning(
                #             rule_id,
                #             target_flow,
                #             current_time,
                #             float(vf.get("maxVehicleFlowNum", 0)),
                #             float(vf.get("minVehicleFlowNum", 0)),
                #             int(vf.get("maxContinuousTimePeriod", 0)),
                #             int(vf.get("minContinuousTimePeriod", 0)),
                #             active_alerts,
                #             warning_state,
                #             frame,
                #             db,
                #             camera_id,
                #             camera_name
                #         )

                #这是模型传回来的参数的调用方式
                # for hb in hitBarResult:
                #     #这个是检测线lineId
                #     ln = hb.get("name", "unknown")
                #     for detail in hb.get("hitDetails", []):
                #         #这个是每辆车的ID值
                #         vehicle_no = detail.get("ID")
                #         vehicle_category是每辆车的类型
                #         vehicle_category = detail.get("cat", "unknown")
                #         if not vehicle_no:
                #             continue
                #         detected_vehicles[vehicle_no] = ln

                """
                对于车流量检测规则（规则号为3），更新车辆检测信息、清理120秒前数据，
                并统计过去60秒满足规则要求的车流量，然后调用 process_traffic_flow_warning 进行预警判断。
                """
                # ---------------------------
                # 1. 更新 detected_vehicles 数据
                # ---------------------------
                # 这个detected_vehicles


                for hb in hitBarResult:
                    line_name = hb.get("name", "unknown")
                    for detail in hb.get("hitDetails", []):
                        vehicle_no = detail.get("ID")
                        vehicle_category = detail.get("cat", "unknown")  # 假设从hitDetails中可以获取车辆类别
                        if not vehicle_no:
                            continue
                        # 如果该车辆第一次检测（入口）
                        print("检测线检测到车辆了")
                        if vehicle_no not in detected_vehicles:
                            detected_vehicles[vehicle_no] = {
                                "vehicle_category": vehicle_category,  # 车辆类别名
                                "first_line": line_name,              # 首次检测的检测线ID
                                "first_time": current_time,           # 首次检测的时间
                            }
                        else:
                            # 如果已经存在，且还没有记录出口检测信息，则更新为出口检测线
                            detected_vehicles[vehicle_no]["latest_line"] = line_name
                            detected_vehicles[vehicle_no]["latest_time"] = current_time

                detected_vehicles_current = {}

                # 更新detected_vehicles_current
                for hb in hitBarResult:
                    line_name = hb.get("name", "unknown")
                    for detail in hb.get("hitDetails", []):
                        vehicle_no = detail.get("ID")
                        vehicle_category = detail.get("cat", "unknown")  # 假设从hitDetails中可以获取车辆类别
                        if not vehicle_no:
                            continue
                        print("检测线检测到车辆了")
                        # 将当前帧检测到的车辆信息存入字典
                        detected_vehicles_current[vehicle_no] = {
                            "vehicle_category": vehicle_category,  # 车辆类别名
                            "line": line_name,                     # 本帧检测到的检测线ID
                            "time": current_time                   # 当前检测时间
                        }

                # ---------------------------
                # 2. 清除超过120秒的车辆检测记录
                # ---------------------------
                expired_vehicles = []
                for vehicle_no, record in detected_vehicles.items():
                    # 此处以车辆首次进入的时间为基准判断是否过期
                    if current_time - record.get("first_time", current_time) > 120:
                        expired_vehicles.append(vehicle_no)
                        saveCarThroughFixedRoute(db,vehicle_no,record["vehicle_category"],
                                                 record["first_line"],record.get("latest_line",None),
                                                 record["first_time"],camera_id)
                for vehicle_no in expired_vehicles:
                    #TODO 这边在删除车辆检测记录的时候要存入数据表

                    del detected_vehicles[vehicle_no]

                # ---------------------------
                # 3. 遍历车流量规则，并根据规则计算target_flow
                # ---------------------------
                if "3" in rules_parsed:
                    for vf in rules_parsed["3"]:
                        rule_id = vf.get("rule_id")
                        vehicle_flow_info = vf.get("VehicleFlow", {})
                        data = vehicle_flow_info.get("LabelsEqual")
                        custom_label = label_map.copy()
                        update_label_map(custom_label, data)  # 更新label_map，假设这是一个函数

                        # 从规则对象中提取阈值
                        maxVehicleFlowNum = float(vehicle_flow_info.get("maxVehicleFlowNum", 0))
                        minVehicleFlowNum = float(vehicle_flow_info.get("minVehicleFlowNum", 0))
                        maxContinuousTimePeriod = int(vehicle_flow_info.get("maxContinuousTimePeriod", 0))
                        minContinuousTimePeriod = int(vehicle_flow_info.get("minContinuousTimePeriod", 0))

                        # 获取起始检测线和终止检测线的设置
                        cameraStartLine_cfg = vehicle_flow_info.get("cameraStartLine", {})
                        cameraEndLine_cfg = vehicle_flow_info.get("cameraEndLine", {})
                        start_line_id = cameraStartLine_cfg.get("cameraLineId")
                        start_line_all = cameraStartLine_cfg.get("isAll", False)
                        end_line_id = cameraEndLine_cfg.get("cameraLineId")
                        end_line_all = cameraEndLine_cfg.get("isAll", False)

                        # 统计过去60秒内满足条件的车流量（target_flow）
                        target_flow = 0
                        for vehicle_no, record in detected_vehicles.items():
                            # 判断入口检测是否在60秒内
                            if current_time - record.get("first_time", 0) <= 60:
                                valid = False
                                # 如果起始检测线允许所有，或与规则配置匹配，则视为入口满足
                                if start_line_all or (start_line_id and record.get("first_line") == start_line_id):
                                    # 若规则只关注入口检测，则出口配置为all即可满足
                                    if end_line_all:
                                        valid = True
                                    else:
                                        # 若规则要求匹配出口检测，则必须存在出口记录，并匹配对应的检测线
                                        if "latest_line" in record and record.get("latest_line") == end_line_id:
                                            valid = True
                                # 如果满足条件，则进行加权流量计算
                                if valid:
                                    # 计算车流量加权：根据车辆的标签，计算加权流量
                                    weight = 0
                                    for label in custom_label:
                                        if label.label_name == record['vehicle_category']:
                                            weight = float(label.default_equal)
                                    # 加权流量
                                    target_flow += weight
                        # print(f"当前加权流量和{target_flow}")

                        # ---------------------------
                        # 4. 调用 process_traffic_flow_warning 进行预警判断
                        # ---------------------------
                        await process_traffic_flow_warning(
                            rule_id,
                            target_flow,
                            current_time,
                            maxVehicleFlowNum,
                            minVehicleFlowNum,
                            maxContinuousTimePeriod,
                            minContinuousTimePeriod,
                            frame,
                            db,
                            camera_id,
                            camera_name
                        )


                # 你需要看看有没有在对应检测线上检测到规则上预警的车辆类型值，如果检测到了就调用这个进行预警
                # 这是相关模型传回来的检测的信息
                # for hb in hitBarResult:
                #     line_name = hb.get("name", "unknown")
                #     for detail in hb.get("hitDetails", []):
                #         vehicle_no = detail.get("ID")
                #         vehicle_category = detail.get("cat", "unknown")  # 假设从hitDetails中可以获取车辆类别
                #         if not vehicle_no:
                #             continue
                #         # 如果该车辆第一次检测（入口）
                #         print("检测线检测到车辆了")
                #         if vehicle_no not in detected_vehicles:
                #             detected_vehicles[vehicle_no] = {
                #                 "vehicle_category": vehicle_category,  # 车辆类别名
                #                 "first_line": line_name,              # 首次检测的检测线ID
                #                 "first_time": current_time,           # 首次检测的时间
                #                 "latest_line": line_name,             # 最新检测的检测线ID（初始时与first_line相同）
                #                 "latest_time": current_time          # 最新检测的时间
                #             }
                #         else:
                #             # 如果已经存在，且还没有记录出口检测信息，则更新为出口检测线
                #             detected_vehicles[vehicle_no]["latest_line"] = line_name
                #             detected_vehicles[vehicle_no]["latest_time"] = current_time
                # 有三行已经给出
                # for rule in rules_parsed["1"]:
                #     label_obj = rule.get("label", {})
                #     car_category = label_obj.get("labelId", [])
                #     line_id = label_obj.get("cameraLineId", "")
                # car_category里面存的是标签的id形成的一个list，也就是rule要检测的标签id，如果，line_id里面存了
                # 这个rule在哪个检测线检测
                # label_map里面存的是[{"default_equal":"1","label_id":"1","label_name":"2"},...]
                # 你需要得出isDetect来决定是否在对应检测线上检测到了信息
                # process_vehicle_type_pre_warning(
                #         isDetect,
                #         line_id,
                #         car_category_names,
                #         frame,
                #         db,
                #         camera_id,
                #         camera_name,
                #         vehicle_warning_state,
                #         vehicle_alert_start_time
                #     )

                for rule in rules_parsed["1"]:
                    rule_id = rule.get("rule_id", None)
                    label_obj = rule.get("label", {})
                    # 获取需要检测的车辆类型对应的标签 id 列表（注意类型可能为字符串或数字，此处统一处理为字符串）
                    car_category_ids = [str(x) for x in label_obj.get("labelId", [])]
                    rule_line_id = label_obj.get("cameraLineId", "")

                    # 根据 label_map 得到每个标签 id 对应的车辆类别名称
                    car_category_names = []
                    for cat_id in car_category_ids:
                        for label in label_map:
                            # label_map 中 label_id 可能为字符串，这里做字符串比对
                            if str(label.label_id) == cat_id:
                                # 获取 label_name（车辆类别名称），若不存在可做默认处理
                                car_category_names.append(label.label_name)
                                break

                    # 检查在该检测线（rule_line_id）上是否检测到了预警车辆类型
                    isDetect = False
                    for vehicle in detected_vehicles_current.values():
                        # 检查最新检测的检测线与规则要求是否一致，
                        # 且该车辆的类别是否在规则要求的车辆类型名称列表里
                        if vehicle.get("line") == rule_line_id and vehicle.get("vehicle_category") in car_category_names:
                            isDetect = True
                            break

                    # 调用预警处理函数，该函数负责进一步的预警处理
                    await process_vehicle_type_pre_warning(
                        rule_id,
                        isDetect,
                        rule_line_id,
                        car_category_names,
                        frame,
                        db,
                        camera_id,
                        camera_name,
                        vehicle_alert_start_time
                    )

                # if any(r.get("vehicleReserve", False) for r in rules_parsed["4"]) and detected_vehicles:
                #     reservation_alert_triggered = process_vehicle_reservation_warning(
                #         detected_vehicles=detected_vehicles,
                #         the_vehicle_history=the_vehicle_history,
                #         current_time=current_time,
                #         frame=frame,
                #         db=db,
                #         camera_id=camera_id,
                #         camera_name=camera_name
                #     )

                # custom_flow_global = {}
                # for rule in rules_parsed["3"]:
                #     vf = rule.get("VehicleFlow", {})
                #     data = vf.get("LabelsEqual", [])
                #     if isinstance(data, str):
                #         try:
                #             data = json.loads(data)
                #         except Exception:
                #             data = []
                #     custom_label = label_map.copy()
                #     update_label_map(custom_label, data)

                # flow_for_line = calculate_traffic_volume_flow(hitBarResult, label_map, db)


                # label_counts = calculate_label_counts(hitBarResult, label_map)


                # target_flow = 0
                # for rule in rules_parsed["3"]:
                #     vf = rule.get("VehicleFlow", {})
                #     start_line = vf.get("cameraStartLine", {}).get("cameraLineId", "")
                #     end_line = vf.get("cameraEndLine", {}).get("cameraLineId", "")
                #     if not start_line:
                #         start_line = main_line_id
                #     if not end_line:
                #         end_line = main_line_id
                #     if start_line and end_line and start_line != end_line:
                #         target_flow = flow_for_line.get(start_line, 0)
                #         flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_traffic_flow_warning(
                #             target_flow,
                #             current_time,
                #             float(vf.get("maxVehicleFlowNum", 0)),
                #             float(vf.get("minVehicleFlowNum", 0)),
                #             int(vf.get("maxContinuousTimePeriod", 0)),
                #             int(vf.get("minContinuousTimePeriod", 0)),
                #             active_alerts,
                #             warning_state,
                #             frame,
                #             db,
                #             camera_id,
                #             camera_name
                #         )



                # avg_hold_volume = calculate_traffic_volume_hold(detailedResult, label_map)

                # traffic_data.append((current_time, avg_hold_volume, target_flow, label_counts))
                # update_lineWiseTrafficData(flow_for_line, globals().setdefault("lineWiseTrafficData", {}))



                # if current_time - history_last_checked >= 10:
                #     total_flow_equiv = 0
                #     for rule in rules_parsed["3"]:
                #         vf = rule.get("VehicleFlow", {})
                #         start_line = vf.get("cameraStartLine", {}).get("cameraLineId", "")
                #         end_line = vf.get("cameraEndLine", {}).get("cameraLineId", "")
                #         if not start_line:
                #             start_line = main_line_id
                #         if not end_line:
                #             end_line = main_line_id
                #         total_flow_equiv += process_vehicle_history(
                #             vehicle_history,
                #             current_time,
                #             start_line,
                #             end_line,
                #             custom_flow_global,
                #             camera_id,
                #             db
                #         )
                #     history_last_checked = current_time
                #
                #     if traffic_data:
                #         avg_hold = sum(h for _, h, _, _ in traffic_data) / len(traffic_data)
                #         aggregated_counts = aggregate_label_counts(traffic_data, label_map)
                #         sum_flow = sum(f for _, _, f, _ in traffic_data)
                #         save_to_camera_detect_info(db, camera_id, avg_hold, sum_flow, aggregated_counts, current_time)
                #     traffic_data.clear()
                #     start_time = current_time

                if processed is not None:
                    cv2.imshow("Processed Frame", processed)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                ret, buffer = await asyncio.to_thread(cv2.imencode, '.jpg', processed)
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            close_db()
    except Exception as e:
        print(f"摄像头连接失败：{e}")
        traceback.print_exc()


async def background_camera_task(camera_id: str, liveStreamType: str = None):
    db, close_db = get_db_session()
    try:
        while True:
            camera_url = get_camera_url(db, camera_id)
            if not camera_url:
                print(f"摄像头 {camera_id} 的 URL 未找到")
                return
            try:
                async for frame in generate_frames(camera_url, camera_id, liveStreamType):
                    latest_frames[camera_id] = frame
            except Exception as e:
                print(f"后台任务中摄像头 {camera_id} 发生异常：{e}")
                traceback.print_exc()
            await asyncio.sleep(5)
    finally:
        close_db()


@router.get("/storage/getCameraLiveStream")
async def proxy_video_feed(
        cameraId: str = Query(..., description="摄像头 ID"),
        liveStreamType: str = Query(..., description="直播流类型"),
        token: str = Query(..., description="管理员访问权限 Token"),
        db: Session = Depends(db_dependency)
):
    token_payload = verify_jwt_token(token)
    if not token_payload or not token_payload.get("is_admin"):
        return JSONResponse(content={"code": "403", "msg": "Unauthorized", "data": {}}, status_code=403)
    if cameraId not in latest_frames:
        return JSONResponse(content={"code": "404", "msg": "Camera not found or not started", "data": {}},
                            status_code=404)

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
