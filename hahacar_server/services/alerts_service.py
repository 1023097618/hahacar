from sqlalchemy import func
from sqlalchemy.orm import Session

from models.alert import Alert
from schemas.alert_schema import *



def saveAlert(db:Session, alert_id: str, camera_id: str, camera_name: str, alert_type: int,alert_start_time, alert_end_time, alert_processed_time, alert_image, rule_type: str, rule_remark: str):
    # 查询是否已有该预警
    existing_alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if existing_alert:
        # **更新预警信息**
        if alert_type == 2:  # "已经发生"
            existing_alert.alert_type = 2
            existing_alert.alert_end_time = alert_end_time

        elif alert_type == 3:  # "已处理"
            existing_alert.alert_type = 3
            existing_alert.alert_processed_time = alert_processed_time

        db.commit()
        print(f"[更新] 预警 {alert_id} 更新为类型 {alert_type}")

    else:
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
            rule_remark=rule_remark
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
        query = query.filter(
            Alert.alert_start_time >= datetime.strptime(request.alertStartTimeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.alertStartTimeTo:
        query = query.filter(Alert.alert_start_time <= datetime.strptime(request.alertStartTimeTo, "%Y-%m-%d %H:%M:%S"))
    if request.alertId:
        query = query.filter(Alert.id == request.alertId)

    alerts = query.offset((int(request.pageNum) - 1) * int(request.pageSize)).limit(int(request.pageSize)).all()

    return {"code": "200", "msg": "success", "data": {"alerts": alerts}}

#处理一条预警，将状态设为“已结束”
def processAlert(db:Session, request: ProcessAlertRequest):
    alert = db.query(Alert).filter(Alert.id == request.alertId).first()
    if not alert:
        return {"code": "400", "msg": "alert not found", "data": {}}
    if alert.alert_type == '3':
        return {"code": "400", "msg": "alert is already ended", "data": {}}
    alert.alert_type = '3'
    alert.alert_processed_time = datetime.utcnow()
    db.commit()
    return {"code": "200", "msg": "success", "data": {}}

#获取预警信息数量

"""
    **这里返回的alert_time和timefrom以及timeto的关系不很清楚
"""
def getAlertNum(db:Session,request: GetAlertCountRequest):
    # **计算 AlertTime 逻辑**
    if request.timeFrom:
        alert_time = request.timeFrom  # 如果提供了 timeFrom，则直接使用
    else:
        alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 否则取当前时间

    query = db.query(func.count(Alert.id).label("alert_count"))  # 计算 Alert 表中的数量

    if request.cameraId:
        query = query.filter(Alert.camera_id == request.cameraId)
    if request.timeFrom:
        query = query.filter(
            Alert.alert_start_time >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(Alert.alert_end_time <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))

    alert_num = query.scalar()


    return {"code": "200", "msg": "success", "data": {"AlertTime": alert_time,"AlertNum": str(alert_num)}}