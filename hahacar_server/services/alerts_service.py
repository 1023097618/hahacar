from datetime import timedelta
from urllib.parse import unquote
from util import timeutil
from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import Session

from api.socket_manager import sio
from dependencies.database import SessionLocal
from models.alert import Alert
from schemas.alert_schema import *
from util.timeutil import parse_frontend_time

domain = "http://localhost:8081"

def saveAlert(db:Session, alert_id: str, camera_id: str, camera_name: str, alert_type: str,alert_start_time, alert_end_time, alert_processed_time, alert_image, rule_type: str, rule_remark: str):
    # 查询是否已有该预警
    existing_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()

    if existing_alert:
        # **更新预警信息**
        if alert_type == '2':  # "已经发生"
            existing_alert.alert_type = '2'

            existing_alert.alert_end_time = timeutil.get_utc_datetime_from_timestamp(alert_end_time)

        elif alert_type == '3':  # "已处理"
            existing_alert.alert_type = '3'
            existing_alert.alert_processed_time = timeutil.get_utc_datetime_from_timestamp(alert_processed_time)
        
        alert_num = existing_alert.alert_num + 1 if bool(existing_alert.alert_num) else 1;

        db.commit()
        print(f"[更新] 预警 {alert_id} 更新为类型 {alert_type}")

    else:
        alert_num = 1;
        if isinstance(alert_start_time, type(1.876876576565)):
            alert_start_time = datetime.fromtimestamp(alert_start_time);
        if not isinstance(alert_end_time, type(alert_start_time)) and alert_end_time is not None:
            alert_end_time = datetime.fromtimestamp(alert_end_time);
        if not isinstance(alert_processed_time, type(alert_start_time)) and alert_processed_time is not None:
            alert_processed_time = datetime.fromtimestamp(alert_processed_time);
        # **新增预警信息**
        new_alert = Alert(
            alert_id=alert_id,
            camera_id=camera_id,
            camera_name=camera_name,
            alert_type=alert_type,
            alert_start_time=alert_start_time,
            alert_end_time=alert_end_time,
            alert_processed_time=alert_processed_time,
            alert_image=alert_image,
            rule_type=rule_type,
            rule_remark=rule_remark,
            alert_num=alert_num
        )
        db.add(new_alert)
        db.commit()
        print(f"[新增] 预警 {alert_id} 已存入数据库")

def getAlerts(db:Session, request:GetAlertsRequest):
    query = db.query(Alert)

    if request.alertType:
        query = query.filter(Alert.alert_type.in_(request.alertType))
    if request.cameraId:
        query = query.filter(Alert.camera_id == request.cameraId)
    if request.alertStartTimeFrom:
        # 对时间参数进行解码（如果前端传递的是 URL 编码的字符串）
        decoded_start = unquote(request.alertStartTimeFrom)
        query = query.filter(
            Alert.alert_start_time >= datetime.strptime(decoded_start, "%Y-%m-%d %H:%M:%S"))
    if request.alertStartTimeTo:
        decoded_end = unquote(request.alertStartTimeTo)
        query = query.filter(Alert.alert_start_time <= datetime.strptime(decoded_end, "%Y-%m-%d %H:%M:%S"))
    if request.alertId:
        query = query.filter(Alert.alert_id == request.alertId)

    # 查询总数量（用于分页显示）
    total_count = query.count()

    # 分页查询
    alerts_paginated = query.offset((int(request.pageNum) - 1) * int(request.pageSize)) \
        .limit(int(request.pageSize)) \
        .all()

    alerts_list = []
    for alert in alerts_paginated:
        if alert is None:
            continue
        alerts_list.append({
            "alertId": str(alert.alert_id),
            "cameraId": str(alert.camera_id),
            "cameraName": alert.camera_name if alert.camera_name else "",
            "alertType": str(alert.alert_type),  # 1: 正在发生, 2: 已经发生, 3: 已经结束
            "alertStartTime": alert.alert_start_time.strftime("%Y-%m-%d %H:%M:%S") if alert.alert_start_time else "",
            "alertEndTime": alert.alert_end_time.strftime("%Y-%m-%d %H:%M:%S") if alert.alert_end_time else None,
            "alertProcessedTime": alert.alert_processed_time.strftime(
                "%Y-%m-%d %H:%M:%S") if alert.alert_processed_time else None,
            "alertImage": alert.alert_image if alert.alert_image else "",
            "ruleType": alert.rule_type if alert.rule_type else "",
            "ruleRemark": alert.rule_remark if alert.rule_remark else ""
        })

    return {
        "code": "200",
        "msg": "success",
        "data": {
            "alerts": alerts_list,
            "alertNum": str(total_count)
        }
    }


#处理一条预警，将状态设为“已结束”
def processAlert(db:Session, alertId:str):
    alert = db.query(Alert).filter(Alert.alert_id == alertId).first()
    if not alert:
        return {"code": "400", "msg": "alert not found", "data": {}}
    if alert.alert_type == '3':
        return {"code": "400", "msg": "alert is already ended", "data": {}}
    alert.alert_type = '3'
    alert.alert_processed_time = datetime.utcnow()
    db.commit()
    return {"code": "200", "msg": "success", "data": {}}

#获取预警信息数量
# TODO 不要这么写！！我说怎么这么卡，原来你是直接代码里统计的，你要在数据库里面统计，你可以看看我统计车流量的分组是怎么做的，搞到这里来
# 因为这个代码可以跑我就先不改了，时间紧急。。。但绝对有性能问题
"""
    **这里返回的alert_time和ti清mefrom以及timeto的关系不很楚
    按照这样的逻辑实现了：
    1.先取出数据库中的预警数据；
    2.对获取到的所有预警数据进行按时间分组：假如起始时间和终止时间存在，则根据这两段时间从头到尾按整小时进行分组：
    例如，timeFrom为2025-03-10 07:20:00，timeFrom为2025-03-10 20:40:00，
    则2025-03-10 07:20:00到2025-03-10 08:00:00分为一组、2025-03-10 08:00:00到2025-03-10 09:00:00分为一组，以此类推。
    然后把这些数据分组返回，例如第一组返回{"AlertTime": "2025-03-10 07:20:00"（这是starttime）, "AlertNum": "数量"}，
    第二组返回 {"AlertTime": "2025-03-10 08:30:00"（这是第二组的中间时间）, "AlertNum": "数量"}，
    第三组返回{"AlertTime": "2025-03-10 09:30:00"（这是第三组的中间时间）, "AlertNum": "数量"}
    3.假如起始和终止时间不存在，那么起始时间其实就是第一条数据的时间，到最后。。
"""
def getAlertNum(db: Session, request: GetAlertCountRequest) -> List[dict]:
    # 解析传入的时间
    time_from = parse_frontend_time(request.timeFrom) if request.timeFrom else None
    time_to = parse_frontend_time(request.timeTo) if request.timeTo else None

    # 构造用于分组的时间表达式
    base_time = func.strftime('%Y-%m-%d %H:', Alert.alert_start_time)
    minutes_interval = func.floor(cast(func.strftime('%M', Alert.alert_start_time), Integer) / 30) * 30
    minutes_interval_padded = func.printf('%02d:00', minutes_interval)
    alert_time_expr = base_time.op("||")(minutes_interval_padded)

    # 构造查询，选择聚合时间和数量
    alert_query = db.query(
        alert_time_expr.label('alert_time'),
        func.count(Alert.alert_id).label('alert_num')
    ).group_by('alert_time')

    # 根据时间范围过滤
    if time_from and time_to:
        alert_query = alert_query.filter(
            Alert.alert_start_time >= time_from,
            Alert.alert_start_time <= time_to
        )
    elif time_from:
        alert_query = alert_query.filter(
            Alert.alert_start_time>=time_from
        )
    elif time_to:
        alert_query = alert_query.filter(
            Alert.alert_end_time>=time_to
        )

    # 处理 cameraId 过滤逻辑
    if request.cameraId:
        alert_query = alert_query.filter(Alert.camera_id == request.cameraId)

    # 获取按 30 分钟区间聚类的预警数量
    alert_data = alert_query.all()

    # 格式化返回结果
    result = []
    for alert_time, alert_num in alert_data:
        result.append({
            "AlertTime": alert_time,
            "AlertNum": str(alert_num)
        })

    return result

# @sio.event
# async def connect(sid, environ,auth):
#     print(f"[socket] Client connected:发送所有预警状态 {sid}")
#
#     # 1) 新建数据库会话
#     db = SessionLocal()
#
#     try:
#         # 查询当前状态为“正在发生”的预警
#         happening_alerts = db.query(Alert).filter(Alert.alert_status == 1).all()
#
#         alert_data = []
#         for alert in happening_alerts:
#             alert_data.append({
#                 "alertId": alert.alert_id,
#                 "cameraId": alert.camera_id,
#                 "cameraName": alert.camera_name,
#                 # "ruleType": alert.rule_type,
#                 # "alertTime": alert.alert_time.strftime("%Y-%m-%d %H:%M:%S") if alert.alert_time else "",
#                 "ruleRemark": alert.remark,
#                 # "imageUrl": f"/alerts/{alert.alert_img}" if alert.alert_img else ""
#             })
#
#         # 发送初始化事件（只发给这个sid）
#         await sio.emit("updateHappeningAlert", alert_data)
#         print(f"[Socket.IO] 已向 {sid} 推送初始化预警，共{len(alert_data)}条")
#     except Exception as e:
#         print(f"初始化推送异常: {e}")
