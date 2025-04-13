import os
import uuid
from datetime import datetime, time

import cv2

from api.socket_manager import sio
from services.alerts_service import saveAlert
from fastapi.staticfiles import StaticFiles

from services.camera_status_service import update_camera_status

# 获取当前工作目录，并构造保存路径，当前目录/alerts/on
base_dir = os.getcwd()
save_dir = os.path.join(base_dir, "alerts", "on")
os.makedirs(save_dir, exist_ok=True)  # 确保目录存在

# 补全这个函数，根据外部传进来的isDetect，如果isDetect就代表检测到了检测线中检测到了相关车辆，需要开始预警
# 这边需要为每一个rule存储一个全局的字典，字典键为rule_id，字典值为某个预警,即这个规则触发的预警。
# 其中字典数据是这么存储的
#             active_alerts[rule_id] = {
#                 "trigger_start": current_time,  # 触发条件第一次成立的时间
#                 "alert_created": False,  # 是否已经创建了预警记录
#                 "recover_start": None,  # 恢复状态开始的时间（预警结束计时）
#                 "alert_id": None  # 记录创建后的alert_id
#             }
# 首先如果isDetect为true之后，我们应该将预警置为的状态置为1，通过这种方式将它保存
#                     saveAlert(db, new_alert_id, camera_id, camera_name, 1, datetime.now(), None, None, alert_image,
#                               rule_type, rule_remark)
# 然后往前端发送一条
#             await sio.emit("updateHappeningAlert", {
#                 "alertId": new_alert_id,
#                 "cameraId": camera_id,
#                 "cameraName": camera_name,
#                 "ruleRemark": rule_remark
#             })
# 当isDetect为false之后且这个rule_id中存在有这条预警，我们需要
# 把它从字典中移除，并且使用
#                    saveAlert(db,
#                               alert_id,
#                               camera_id,
#                               camera_name,
#                               2, ws,
#                               warning_end_time,
#                               None,
#                               ai,
#                               rule_type,
#                               rr)
#                     来将它保存
# alert_id是uuid，你需要自动生成
cameras_alert_count = {}

#TODO 今天刚刚发现这个地方没做，暂时简单的这么实现一下，因为预警我不想去数据库查，我是想走缓存字典的路的
async def add_camera_alert_count(camera_id):
    if camera_id not in cameras_alert_count:
        cameras_alert_count[camera_id] = 0

    cameras_alert_count[camera_id] = cameras_alert_count[camera_id] + 1

    if cameras_alert_count[camera_id] > 0:
        await update_camera_status(camera_id, True, True)


async def sub_camera_alert_count(camera_id):
    if camera_id not in cameras_alert_count:
        cameras_alert_count[camera_id] = 0

    cameras_alert_count[camera_id] = cameras_alert_count[camera_id] - 1

    if cameras_alert_count[camera_id] == 0:
        await update_camera_status(camera_id, True, False)


async def process_vehicle_type_pre_warning(rule_id: str, isDetect: bool, line_id: str, car_category_names: list,
                                           frame, db, camera_id: str, camera_name: str,
                                           vehicle_alert_start_time: dict):
    """
    当 isDetect 为 True 时，检测线中检测到了相关车辆，开始预警：
      - 如果全局预警字典中不包含当前 rule_id，则生成新的 alert_id，
        使用 saveAlert 保存状态为 1（预警开始）的记录，
        并调用 sio.emit 将预警信息推送给前端；
      - 同时将预警信息存入 vehicle_warning_state 字典中。

    当 isDetect 为 False 时，如果该 rule_id 已经存在预警记录：
      - 从全局预警字典中移除，
      - 调用 saveAlert 保存状态为 2（预警结束）的记录。
    """
    current_time = datetime.now()

    if isDetect:
        # 当检测到车辆，且尚未存在该规则的预警记录时进行预警创建
        if rule_id not in active_alerts:
            # 生成全局唯一的预警ID（uuid）
            new_alert_id = str(uuid.uuid4())

            # 构造预警相关信息（你可以根据需要调整 rule_type 与 rule_remark 的具体内容）
            rule_type = "vehicle_type_pre_warning"
            rule_remark = f"检测到车辆在检测线 {line_id}，车辆类型：{', '.join(car_category_names)}"

            alert_image = f"{new_alert_id}.jpg"
            save_path = os.path.join(save_dir, alert_image)
            cv2.imwrite(save_path, frame)

            # 将预警记录存入全局字典
            active_alerts[rule_id] = {
                "trigger_start": current_time,  # 触发条件第一次成立的时间
                "alert_created": True,  # 记录已创建预警
                "recover_start": None,  # 预警恢复时间暂未开始计时
                "alert_id": new_alert_id  # 记录生成的预警ID
            }
            vehicle_alert_start_time[rule_id] = current_time

            # 记录预警开始状态，状态码 1
            saveAlert(db, new_alert_id, camera_id, camera_name, '1', current_time,
                      None, None, alert_image, rule_type, rule_remark)

            # 发送实时消息到前端告知预警信息
            await sio.emit("updateHappeningAlert", {
                "alertId": new_alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name,
                "ruleRemark": rule_remark
            })

            await add_camera_alert_count(camera_id)

        else:
            # 如果该预警记录已存在，可选择在此处更新触发时间或其它数据，此处保持不处理
            pass
    else:
        # 当 isDetect 为 False 时，如果该 rule_id 存在预警记录，表示恢复了
        if rule_id in active_alerts:
            # 弹出预警记录
            alert_info = active_alerts.pop(rule_id)
            alert_id = alert_info["alert_id"]

            # 取出预警开始时间用作 ws 参数
            ws = alert_info["trigger_start"]
            warning_end_time = current_time  # 预警结束时间

            # 构造结束预警的附加信息，可根据需要进行调整
            rule_type = "vehicle_type_pre_warning"
            rule_remark = f"检测恢复，车辆情况恢复正常（检测线：{line_id}）"
            ai = frame  # 结束预警时的图片信息

            # 记录预警结束状态，状态码 2
            saveAlert(db, alert_id, camera_id, camera_name, '2', ws, warning_end_time,
                      None, ai, rule_type, rule_remark)

            await sub_camera_alert_count(camera_id)


# 这边需要为每一个rule存储一个全局的字典，字典键为rule_id，字典值为某个预警,即这个规则触发的预警。这个字典是我刚才第一次任务的时候你写得字典，所以注意保持一致性。
# 首先如果target_flow>maxVehicleFlowNum了maxContinuousTimePeriod秒之后，我们应该将预警置为的状态置为1，通过这种方式将它保存
#             saveAlert(db,
#                       new_alert_id,
#                       camera_id,
#                       camera_name,
#                       1,
#                       warning_start_time,
#                       None,
#                       None,
#                       alert_image,
#                       rule_type,
#                       rule_remark)
# 然后往前端发送一条
#             await sio.emit("updateHappeningAlert", {
#                 "alertId": new_alert_id,
#                 "cameraId": camera_id,
#                 "cameraName": camera_name,
#                 "ruleRemark": rule_remark
#             })
# 当target_flow<minVehicleFlowNum了minContinuousTimePeriod之后且这个rule_id中存在有这条预警，我们需要
# 把它从字典中移除，并且使用
#                    saveAlert(db,
#                               alert_id,
#                               camera_id,
#                               camera_name,
#                               2, ws,
#                               warning_end_time,
#                               None,
#                               ai,
#                               rule_type,
#                               rr)
#                     来将它保存


active_alerts = {}


async def process_traffic_flow_warning(
        rule_id: str,
        target_flow: float,
        current_time: float,
        maxVehicleFlowNum: float,
        minVehicleFlowNum: float,
        maxContinuousTimePeriod: float,
        minContinuousTimePeriod: float,
        frame,
        db,
        camera_id: str,
        camera_name: str
):
    """
    车辆流量预警处理：
      - 当 target_flow > maxVehicleFlowNum 持续达到或超过 maxContinuousTimePeriod 秒后，
        则触发预警：生成预警记录（状态1）、保存预警图片，并通知前端。
      - 当 target_flow < minVehicleFlowNum 持续达到或超过 minContinuousTimePeriod 秒后，
        且该规则已经触发预警时，解除预警（状态2），调用保存函数后将其从 active_alerts 中移除。

    参数说明：
      rule_id: 规则 ID
      target_flow: 当前统计的车流量
      current_time: 当前时间（秒级时间戳）
      maxVehicleFlowNum: 最大车流量阈值
      minVehicleFlowNum: 最小车流量阈值
      maxContinuousTimePeriod: 持续超过最大阈值的时间周期
      minContinuousTimePeriod: 持续低于最小阈值的时间周期
      warning_state: 当前预警状态描述
      frame: 当前帧图像（用于保存预警图片）
      db: 数据库连接或实例
      camera_id: 摄像头ID
      camera_name: 摄像头名称
    """
    warning_state = f"车流量预警，值为：{target_flow}"
    # 预警触发：如果当前车流量大于预设的上限
    if target_flow > maxVehicleFlowNum:
        if rule_id not in active_alerts:
            # 第一次满足高流量条件，记录起始时间与相关信息
            active_alerts[rule_id] = {
                "trigger_start": current_time,  # 记录条件首次满足的时间
                "alert_created": False,  # 是否已经生成了预警记录
                "recover_start": None,  # 开始解除预警计时的时间
                "alert_id": None  # 生成预警记录后的 alert_id
            }
        else:
            # 如果本规则已存在记录，则清空解除计时（防止因短暂满足低流量条件后误解除预警）
            active_alerts[rule_id]["recover_start"] = None

        # 如果连续满足高流量条件达到设定时间且预警未生成
        if (not active_alerts[rule_id]["alert_created"] and
                current_time - active_alerts[rule_id]["trigger_start"] >= maxContinuousTimePeriod):
            new_alert_id = str(uuid.uuid4())
            active_alerts[rule_id]["alert_id"] = new_alert_id
            warning_start_time = active_alerts[rule_id]["trigger_start"]

            # 保存预警图片
            alert_image = f"{new_alert_id}.jpg"
            save_path = os.path.join(save_dir, alert_image)
            cv2.imwrite(save_path, frame)

            rule_type = "vehicle_flow"
            rule_remark = warning_state  # 可根据业务需要设置描述内容

            # 调用预警保存函数，状态1表示预警正在发生
            saveAlert(db,
                      new_alert_id,
                      camera_id,
                      camera_name,
                      '1',  # 预警状态1：触发
                      warning_start_time,
                      None,
                      None,
                      alert_image,
                      rule_type,
                      rule_remark)

            # 通过 socket 向前端发送预警信息
            await sio.emit("updateHappeningAlert", {
                "alertId": new_alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name,
                "ruleRemark": rule_remark
            })

            await add_camera_alert_count(camera_id)
            # 标记该规则预警已创建
            active_alerts[rule_id]["alert_created"] = True

    # 预警解除：如果当前车流量低于预设的下限
    elif target_flow < minVehicleFlowNum:
        if rule_id in active_alerts:
            if active_alerts[rule_id]["alert_created"]:
                # 如果解除计时尚未开始，开始计时
                if active_alerts[rule_id]["recover_start"] is None:
                    active_alerts[rule_id]["recover_start"] = current_time
                # 当低流量状态持续达到设定解除时间
                if current_time - active_alerts[rule_id]["recover_start"] >= minContinuousTimePeriod:
                    alert_id = active_alerts[rule_id]["alert_id"]
                    warning_end_time = current_time
                    alert_image = f"{alert_id}.jpg"
                    rule_type = "vehicle_flow"
                    rule_remark = "车辆流量预警解除"  # 可根据需要调整描述

                    # 调用保存函数记录预警解除（状态2）
                    saveAlert(db,
                              alert_id,
                              camera_id,
                              camera_name,
                              '2',  # 预警状态2：解除
                              warning_end_time,
                              current_time,
                              None,
                              alert_image,
                              rule_type,
                              rule_remark)

                    await sub_camera_alert_count(camera_id)
                    # 从预警字典中移除该规则对应的记录
                    del active_alerts[rule_id]
            else:
                # 若预警记录尚未生成，但数据满足解除条件，则清除该记录
                del active_alerts[rule_id]
    else:
        # 当 target_flow 在上下限之间时
        if rule_id in active_alerts:
            if active_alerts[rule_id]["alert_created"]:
                # 如果预警已经触发，重置解除计时，防止短暂波动造成解除
                active_alerts[rule_id]["recover_start"] = None
            else:
                # 预警尚未生成，清除不必要的记录
                del active_alerts[rule_id]


# 这边需要为每一个rule存储一个全局的字典，字典键为rule_id，字典值为某个预警,即这个规则触发的预警。
# 首先如果avg_hold_volume>maxVehicleHoldNum了maxContinuousTimePeriod秒之后，我们应该将预警置为的状态置为1，通过这种方式将它保存
#             saveAlert(db,
#                       new_alert_id,
#                       camera_id,
#                       camera_name,
#                       1,
#                       warning_start_time,
#                       None,
#                       None,
#                       alert_image,
#                       rule_type,
#                       rule_remark)
# 然后往前端发送一条
#             await sio.emit("updateHappeningAlert", {
#                 "alertId": new_alert_id,
#                 "cameraId": camera_id,
#                 "cameraName": camera_name,
#                 "ruleRemark": rule_remark
#             })
# 当avg_hold_volume<minVehicleHoldNum了minContinuousTimePeriod之后且这个rule_id中存在有这条预警，我们需要
# 把它从字典中移除，并且使用saveAlert(db, alert_id, camera_id, camera_name, 2, ws, warning_end_time, None, ai, rule_type, rr)来将它保存

# 这边还需要check一下current_time和maxContinuousTimePeriod单位对不对的上
async def process_vehicle_congestion_warning(
        rule_id: str,
        avg_hold_volume: float,
        current_time: float,
        maxVehicleHoldNum: float,
        minVehicleHoldNum: float,
        maxContinuousTimePeriod: float,
        minContinuousTimePeriod: float,
        frame,
        db,
        camera_id: str,
        camera_name: str
):
    """
    车辆拥堵预警处理：
      - 当avg_hold_volume > maxVehicleHoldNum持续maxContinuousTimePeriod秒后，触发预警，
        保存记录（状态1），存储预警图片，并通过socket向前端发送通知。
      - 当avg_hold_volume < minVehicleHoldNum持续minContinuousTimePeriod秒后，如果该规则已有预警，
        则调用保存函数更新预警状态为2（解除预警），并从active_alerts中移除该记录。
    """
    # 预警触发情况
    warning_state = "交通拥堵预警"
    if avg_hold_volume > maxVehicleHoldNum:
        # 如果当前规则未在active_alerts中，则记录触发开始时间
        if rule_id not in active_alerts:
            active_alerts[rule_id] = {
                "trigger_start": current_time,  # 触发条件第一次成立的时间
                "alert_created": False,  # 是否已经创建了预警记录
                "recover_start": None,  # 恢复状态开始的时间（预警结束计时）
                "alert_id": None  # 记录创建后的alert_id
            }
        else:
            # 如果检测到拥堵状态，重置恢复计时（如果之前开始了恢复计时）
            active_alerts[rule_id]["recover_start"] = None

        # 如果还没有创建预警，并且条件持续满足超过maxContinuousTimePeriod秒，则创建预警
        if (not active_alerts[rule_id]["alert_created"] and
                current_time - active_alerts[rule_id]["trigger_start"] >= maxContinuousTimePeriod):
            new_alert_id = str(uuid.uuid4())
            # 将新生成的alert_id保存到字典中以便后续使用
            active_alerts[rule_id]["alert_id"] = new_alert_id
            warning_start_time = active_alerts[rule_id]["trigger_start"]

            # 生成预警图片文件名和存储路径
            alert_image = f"{new_alert_id}.jpg"
            save_path = os.path.join(save_dir, alert_image)
            # 保存当前帧到文件中
            cv2.imwrite(save_path, frame)

            # 根据业务设置规则类型和预警描述，可根据需要修改
            rule_type = "vehicle_congestion"
            rule_remark = warning_state

            # 保存预警记录，状态1表示预警正在进行中
            saveAlert(db,
                      new_alert_id,
                      camera_id,
                      camera_name,
                      '1',  # 状态1: 预警触发
                      warning_start_time,
                      current_time,
                      None,
                      alert_image,
                      rule_type,
                      rule_remark)

            await add_camera_alert_count(camera_id)

            # 通过socket向前端发送预警通知
            await sio.emit("updateHappeningAlert", {
                "alertId": new_alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name,
                "ruleRemark": rule_remark
            })

            # 设置标识，表示该预警已创建
            active_alerts[rule_id]["alert_created"] = True

    # 预警解除情况
    elif avg_hold_volume < minVehicleHoldNum:
        # 如果当前规则在active_alerts中存在记录，则可能需要解除预警
        if rule_id in active_alerts:
            # 如果已经生成了预警记录，则开始解除计时
            if active_alerts[rule_id]["alert_created"]:
                # 如果恢复计时尚未开始，则设置恢复开始时间
                if active_alerts[rule_id]["recover_start"] is None:
                    active_alerts[rule_id]["recover_start"] = current_time
                # 如果低于minVehicleHoldNum的状态持续达到minContinuousTimePeriod秒，则解除预警
                if current_time - active_alerts[rule_id]["recover_start"] >= minContinuousTimePeriod:
                    alert_id = active_alerts[rule_id]["alert_id"]
                    warning_end_time = current_time
                    alert_image = f"{alert_id}.jpg"
                    rule_type = "vehicle_congestion"
                    rule_remark = "交通拥堵预警解除"  # 可根据实际情况调整描述

                    # 保存解除预警记录，状态2表示预警已经解除
                    saveAlert(db,
                              alert_id,
                              camera_id,
                              camera_name,
                              '2',  # 状态2: 预警解除
                              warning_end_time,
                              current_time,
                              None,
                              alert_image,
                              rule_type,
                              rule_remark)

                    await sub_camera_alert_count(camera_id)
                    # 从active_alerts中移除该预警记录
                    del active_alerts[rule_id]
            else:
                # 若未生成预警记录就满足恢复条件，则清除该记录
                del active_alerts[rule_id]
    else:
        # 当avg_hold_volume处于两个阈值之间时：
        if rule_id in active_alerts:
            if active_alerts[rule_id]["alert_created"]:
                # 对于已触发的预警，重置恢复计时（防止误解除）
                active_alerts[rule_id]["recover_start"] = None
            else:
                # 对于尚未生成预警的记录，直接清除
                del active_alerts[rule_id]


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
                    save_path = os.path.join(save_dir, alert_image)
                    print(f"图片保存地址：{save_path}")
                    success = cv2.imwrite(save_path, frame)
                    if not success:
                        # 保存失败的处理逻辑
                        print("图片保存失败！")
                    # cv2.imwrite(f"/alerts/on/{alert_image}", frame)

                    rule_type = "4"
                    rule_remark = f"🚨 预约车辆违规 - 车牌: {vehicle_no}, 行进至未授权线路 {line_id} (上次检测线: {previous_line})"

                    # **保存预警到数据库**
                    saveAlert(db, alert_id, camera_id, camera_name, '1', current_time, None, None, alert_image, rule_type,
                              rule_remark)

                    # **发送 WebSocket 预警**
                    await sio.emit("updateHappeningAlert", {
                        "alertId": alert_id,
                        "cameraId": camera_id,
                        "cameraName": camera_name,
                        "ruleRemark": rule_remark
                    })

                    print(f"🚨 预约车辆 {vehicle_no} 违规！从 {previous_line} 进入未预约检测线 {line_id}")

                    return True  # 预警已触发

    return False  # 未触发预警


# TODO 这边的accident_active_alerts也要改成rule_id为键，因为现在代码能跑我就不动它了
async def process_accident_warning(detailedResult: dict, frame, current_time: float, db, camera_id: str,
                                   camera_name: str, accident_active_alerts, clearAccidentThreshold):
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
        # 检测到事故，重置连续清除计数
        if camera_id in accident_active_alerts:
            accident_active_alerts[camera_id]["clear_count"] = 0
            # 已有预警，返回 True 表示仍处于预警状态
            return True, accident_active_alerts
        else:
            alert_id = str(uuid.uuid4())
            alert_image = f"{alert_id}.jpg"
            save_path = os.path.join(save_dir, alert_image)
            print(f"图片保存地址：{save_path}")
            success = cv2.imwrite(save_path, frame)
            if not success:
                # 保存失败的处理逻辑
                print("图片保存失败！")
            # cv2.imwrite(f"/alerts/on/accident/{alert_image}", frame)

            # 获取最高事故置信度
            max_accident_confidence = max(accident_conf)

            # 事故预警详情
            rule_type = "5"
            rule_remark = f"⚠️ 事故预警"

            # 保存事故预警到数据库
            saveAlert(db, alert_id, camera_id, camera_name, '1', current_time, None, None, alert_image, rule_type,
                      rule_remark)

            # 通过 Socket.IO 发送事故预警到前端
            await sio.emit("updateHappeningAlert", {
                "alertId": alert_id,
                "cameraId": camera_id,
                "cameraName": camera_name,
                "ruleRemark": rule_remark
                # "alertType": "事故检测",
                # "alertConfidence": max_accident_confidence,
                # "timestamp": current_time
            })

            await add_camera_alert_count(camera_id)

            # 在全局状态中记录该摄像头的事故预警
            accident_active_alerts[camera_id] = {
                "alert_id": alert_id,
                "warning_start_time": current_time,
                "clear_count": 0  # 清除计数初始化为 0
            }
            # print(f"🚨 事故预警触发！最高置信度: {max_accident_confidence:.2f}")
            print(f"🚨 事故预警触发！")

            return True, accident_active_alerts  # 预警已触发
    else:
        # 未检测到事故
        if camera_id in accident_active_alerts:
            # 增加连续未检测到事故的计数
            accident_active_alerts[camera_id]["clear_count"] += 1
            if accident_active_alerts[camera_id]["clear_count"] >= clearAccidentThreshold:
                # 达到解除预警的条件，更新预警状态为 '2'（已结束）
                alert_id = accident_active_alerts[camera_id]["alert_id"]
                warning_start_time = accident_active_alerts[camera_id]["warning_start_time"]
                warning_end_time = current_time
                # 更新数据库预警状态（例如 saveAlert 用于更新预警状态，类型变为2）
                saveAlert(db, alert_id, camera_id, camera_name, '2', datetime.fromtimestamp(warning_start_time),
                          datetime.fromtimestamp(warning_end_time), None, None, "5", "事故预警解除")

                await sub_camera_alert_count(camera_id)
                # 发送更新事件到前端
                # await sio.emit("updateHappeningAlert", {
                #     "alertId": alert_id,
                #     "cameraId": camera_id,
                #     "cameraName": camera_name,
                #     "ruleRemark": "事故预警解除",
                #     "alertType": "2"
                # })
                print(f"🚨 事故预警解除！ alert_id: {alert_id}")
                # 移除该摄像头的预警记录
                del accident_active_alerts[camera_id]
                return False, accident_active_alerts
        # 如果没有活跃预警，则直接返回 False
        return False, accident_active_alerts
