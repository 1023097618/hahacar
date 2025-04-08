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
from services.warning_service import process_accident_warning, process_vehicle_reservation_warning, process_traffic_flow_warning, process_vehicle_congestion_warning, process_vehicle_type_pre_warning
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
    labelsResponse = getLabels(db)
    data = labelsResponse.get("data", {})
    labels = data.get("labels", [])
    return {label["labelId"]: label["labelName"] for label in labels}


def calculate_traffic_volume_hold(detailedResult: dict, custom_hold: dict, db: Session) -> int:
    label_mapping = get_label_mapping(db)
    hold_map = {lid: custom_hold.get(lid, 1) for lid in label_mapping.keys()}
    hold_volume = 0
    for label, count in detailedResult.get("count", {}).items():
        multiplier = hold_map.get(label, 1)
        hold_volume += count * int(multiplier)
    return hold_volume


def calculate_traffic_volume_flow(hitBarResult: list, custom_flow: dict, db: Session) -> dict:
    flow_for_line = {}
    label_mapping = get_label_mapping(db)
    flow_map = {lid: custom_flow.get(lid, 1) for lid in label_mapping.keys()}
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


def process_vehicle_history(vehicle_history: dict, current_time: float, start_line: str, end_line: str, custom_flow: dict, camera_id: str, db: Session) -> float:
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
                    saveCarThroughFixedRoute(db, vehicle_no=vehicle_no, vehicle_type=vehicle_type, start_line=None, end_line=line, current_time=current_time, camera_id=camera_id)
                else:
                    saveCarThroughFixedRoute(db, vehicle_no=vehicle_no, vehicle_type=vehicle_type, start_line=line, end_line=None, current_time=current_time, camera_id=camera_id)


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

            active_alerts = {}
            warning_state = "正常"
            warning_start_time = None
            warning_end_time = None

            hold_warning_count = 0
            flow_warning_count = 0
            hold_clear_count = 0
            flow_clear_count = 0
            vehicle_warning_state = {}
            vehicle_alert_start_time = {}
            vehicle_clear_count = {}
            clearThreshold = 3

            vehicle_history = {}
            history_last_checked = t.time()

            camera_line_response = get_camera_line(db, camera_id)
            lines = camera_line_response.get("data", {}).get("cameraLines", [])
            main_line = next((l for l in lines if l.get("isMainLine")), None)
            main_line_id = main_line["cameraLineId"] if main_line else None

            hitBars = []
            the_vehicle_history = {}
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

                camera_rule_response = getCameraRule(db, camera_id)
                camera_rules = camera_rule_response.get("cameraRules", [])
                rules_parsed = parse_camera_rules(camera_rules)

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

                for hb in hitBarResult:
                    ln = hb.get("name", "unknown")
                    for detail in hb.get("hitDetails", []):
                        vehicle_no = detail.get("ID")
                        if not vehicle_no:
                            continue
                        detected_vehicles[vehicle_no] = ln

                if any(r.get("vehicleReserve", False) for r in rules_parsed["4"]) and detected_vehicles:
                    reservation_alert_triggered = process_vehicle_reservation_warning(
                        detected_vehicles=detected_vehicles,
                        the_vehicle_history=the_vehicle_history,
                        current_time=current_time,
                        frame=frame,
                        db=db,
                        camera_id=camera_id,
                        camera_name=camera_name
                    )

                custom_flow_global = {}
                for rule in rules_parsed["3"]:
                    vf = rule.get("VehicleFlow", {})
                    data = vf.get("LabelsEqual", [])
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception:
                            data = []
                    custom_flow_global.update({item["labelId"]: item["labelEqualNum"] for item in data})
                flow_for_line = calculate_traffic_volume_flow(hitBarResult, custom_flow_global, db)

                target_flow = 0
                for rule in rules_parsed["3"]:
                    vf = rule.get("VehicleFlow", {})
                    start_line = vf.get("cameraStartLine", {}).get("cameraLineId", "")
                    end_line = vf.get("cameraEndLine", {}).get("cameraLineId", "")
                    if not start_line:
                        start_line = main_line_id
                    if not end_line:
                        end_line = main_line_id
                    if start_line and end_line and start_line != end_line:
                        target_flow = flow_for_line.get(start_line, 0)
                        flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_traffic_flow_warning(
                            target_flow,
                            current_time,
                            float(vf.get("maxVehicleFlowNum", 0)),
                            float(vf.get("minVehicleFlowNum", 0)),
                            int(vf.get("maxContinuousTimePeriod", 0)),
                            int(vf.get("minContinuousTimePeriod", 0)),
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

                for rule in rules_parsed["1"]:
                    label_obj = rule.get("label", {})
                    car_category = label_obj.get("labelId", [])
                    line_id = label_obj.get("cameraLineId", "")
                    car_category_names = [label_map.get(cid) for cid in car_category if cid in label_map]
                    await process_vehicle_type_pre_warning(
                        hitBarResult,
                        line_id,
                        car_category_names,
                        frame,
                        db,
                        camera_id,
                        camera_name,
                        vehicle_warning_state,
                        vehicle_alert_start_time,
                        vehicle_clear_count,
                        clearThreshold,
                        frame
                    )

                avg_hold_volume = calculate_traffic_volume_hold(detailedResult, {}, db)
                label_counts = calculate_label_counts(hitBarResult, label_map)
                traffic_data.append((current_time, avg_hold_volume, target_flow, label_counts))
                update_lineWiseTrafficData(flow_for_line, globals().setdefault("lineWiseTrafficData", {}))

                for rule in rules_parsed["2"]:
                    vh = rule.get("VehicleHold", {})
                    custom_hold = {item["labelId"]: item["labelHoldNum"] for item in vh.get("LabelsEqual", [])}
                    hold_warning_count, hold_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time = await process_vehicle_congestion_warning(
                        avg_hold_volume,
                        current_time,
                        float(vh.get("maxVehicleHoldNum", 0)),
                        float(vh.get("minVehicleHoldNum", 0)),
                        int(vh.get("maxContinuousTimePeriod", 0)),
                        int(vh.get("minContinuousTimePeriod", 0)),
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

                if current_time - history_last_checked >= 10:
                    total_flow_equiv = 0
                    for rule in rules_parsed["3"]:
                        vf = rule.get("VehicleFlow", {})
                        start_line = vf.get("cameraStartLine", {}).get("cameraLineId", "")
                        end_line = vf.get("cameraEndLine", {}).get("cameraLineId", "")
                        if not start_line:
                            start_line = main_line_id
                        if not end_line:
                            end_line = main_line_id
                        total_flow_equiv += process_vehicle_history(
                            vehicle_history,
                            current_time,
                            start_line,
                            end_line,
                            custom_flow_global,
                            camera_id,
                            db
                        )
                    history_last_checked = current_time

                    if traffic_data:
                        avg_hold = sum(h for _, h, _, _ in traffic_data) / len(traffic_data)
                        aggregated_counts = aggregate_label_counts(traffic_data, label_map)
                        sum_flow = sum(f for _, _, f, _ in traffic_data)
                        save_to_camera_detect_info(db, camera_id, avg_hold, sum_flow, aggregated_counts, current_time)
                    traffic_data.clear()
                    start_time = current_time

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
        return JSONResponse(content={"code": "404", "msg": "Camera not found or not started", "data": {}}, status_code=404)

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
