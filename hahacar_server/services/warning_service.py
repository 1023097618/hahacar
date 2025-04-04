import uuid
from datetime import datetime, time

import cv2

from api.socket_manager import sio
from services.alerts_service import saveAlert


async def process_vehicle_type_pre_warning(hitBarResult: list, rule_first_camera_line_id: str, car_category_names: list, frame, db, camera_id: str, camera_name: str, vehicle_warning_state: dict, vehicle_alert_start_time: dict, vehicle_clear_count: dict, clearThreshold: int,alert_image):
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
                    saveAlert(db, new_alert_id, camera_id, camera_name, 1, datetime.now(), None, None, alert_image,
                              rule_type, rule_remark)
                    await sio.emit("updateHappeningAlert", {
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
                    saveAlert(db, alert_id, camera_id, camera_name, 2, vehicle_alert_start_time[vehicle],
                              alert_end_time, None, alert_image, "1", f"{vehicle} 车辆消失，预警结束")
                    del vehicle_warning_state[vehicle]
                    del vehicle_alert_start_time[vehicle]
                    del vehicle_clear_count[vehicle]
                    print(f"[✅ 车辆类型预警解除] {vehicle} 已消失，预警结束")

async def process_traffic_flow_warning(
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
            warning_start_time = datetime.fromtimestamp(current_time)
            new_alert_id = str(uuid.uuid4());
            print(type(warning_start_time))
            alert_image = f"{new_alert_id}.jpg"
            cv2.imwrite(f"/alerts/on/{alert_image}", frame)

            saveAlert(db,
                      new_alert_id, 
                      camera_id, 
                      camera_name, 
                      1, 
                      warning_start_time, 
                      None, 
                      None, 
                      alert_image,
                      rule_type, 
                      rule_remark)

            await sio.emit("updateHappeningAlert", {
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

                saveAlert(db,
                          alert_id, 
                          camera_id, 
                          camera_name, 
                          2, ws, 
                          warning_end_time, 
                          None, 
                          ai, 
                          rule_type, 
                          rr)

            active_alerts.clear()

    return flow_warning_count, flow_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time


async def process_vehicle_congestion_warning(
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

            saveAlert(db, 
                      new_alert_id, 
                      camera_id, 
                      camera_name, 
                      1, 
                      warning_start_time, 
                      None, 
                      None, 
                      alert_image,
                      rule_type, 
                      rule_remark)

            await sio.emit("updateHappeningAlert", {
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

                saveAlert(db, alert_id, camera_id, camera_name, 2, ws, warning_end_time, None, ai, rule_type, rr)

            active_alerts.clear()

    return hold_warning_count, hold_clear_count, active_alerts, warning_state, warning_start_time, warning_end_time


async def process_vehicle_reservation_warning(
    detected_vehicles: dict,
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
    - 仅检查 **当前帧中检测到的车辆** 是否符合预约路线
    - 如果车辆未按照预约路线行进，则触发预警

    **params**
    - detected_vehicles (dict): 仅包含当前帧检测到的车辆 {车牌号: 当前检测线}
    - vehicle_history (dict): 车辆历史行进记录 { 车牌号: 最近检测线 }
    - current_time (float): 当前时间戳
    - frame (np.ndarray): 当前帧图像
    - db: 数据库连接
    - camera_id (str): 摄像头 ID
    - camera_name (str): 摄像头名称

    **returns**
    - 是否触发了预警 (bool)
    """

    # **加载预约车辆信息**
    reservation_file = "./static/vehicle_reservations.txt"
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

    # **遍历当前帧的检测车辆**
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
                    saveAlert(db, alert_id, camera_id, camera_name, 1, current_time, None, None, alert_image, rule_type, rule_remark)

                    # **发送 WebSocket 预警**
                    await sio.emit("updateHappeningAlert", {
                        "alertId": alert_id,
                        "cameraId": camera_id,
                        "cameraName": camera_name,
                    })

                    print(f"🚨 预约车辆 {vehicle_no} 违规！从 {previous_line} 进入未预约检测线 {line_id}")

                    return True  # 预警已触发

    return False  # 未触发预警




async def process_accident_warning(detailedResult: dict, frame, current_time: float, db, camera_id: str, camera_name: str):
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
        saveAlert(db, alert_id, camera_id, camera_name, 1, current_time, None, None, alert_image, rule_type, rule_remark)

        # 通过 Socket.IO 发送事故预警到前端
        await sio.emit("updateHappeningAlert", {
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

