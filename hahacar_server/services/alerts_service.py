from sqlalchemy import func
from sqlalchemy.orm import Session

from models.alert import Alert
from schemas.alert_schema import *


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
def getAlertNum(db:Session,request: GetAlertCountRequest):
    query = db.query(
        func.strftime('%Y-%m-%d %H:00:00',Alert.alert_start_time).label("AlertTime"),
        func.count(Alert.id).label("AlertNum")
    )
    if request.timeFrom:
        query = query.filter(Alert.alert_start_time >= datetime.strptime(request.timeFrom, "%Y-%m-%d %H:%M:%S"))
    if request.timeTo:
        query = query.filter(Alert.alert_start_time <= datetime.strptime(request.timeTo, "%Y-%m-%d %H:%M:%S"))
    if request.cameraId:
        query = query.filter(Alert.camera_id == request.cameraId)

    query = query.group_by("AlertTime").order_by("AlertNum")
    results = query.all()

    return {"code": "200", "msg": "success", "data": {"alerts": results}}