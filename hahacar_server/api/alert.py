from fastapi import APIRouter, Depends, Query, Header, Body
from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from dependencies.database import get_db
from schemas.alert_schema import *
from services.alerts_service import *
from typing import Optional, List
from fastapi import Query

router = APIRouter(prefix="/api", tags=["Alert"])


"""
    **时间精度问题导致输入准确的世家按无法返回该时间上的数据**
"""
@router.get("/alert/getAlerts")
def get_alerts_api(
    pageNum: str = Query(..., description="页码"),
    pageSize: str = Query(..., description="每页大小"),
    alertType: Optional[List[str]] = Query(None, description="警报类型列表"),
    cameraIds: Optional[str] = Query(None, description="摄像头 ID"),
    alertStartTimeFrom: Optional[str] = Query(None, description="警报开始时间起点"),
    alertStartTimeTo: Optional[str] = Query(None, description="警报开始时间终点"),
    alertId: Optional[str] = Query(None, description="警报 ID"),
    db: Session = Depends(get_db)
):
    request = GetAlertsRequest(
        pageNum=pageNum,
        pageSize=pageSize,
        alertType=alertType,
        cameraId=cameraIds,
        alertStartTimeFrom=alertStartTimeFrom,
        alertStartTimeTo=alertStartTimeTo,
        alertId=alertId
    )
    return getAlerts(db, request)


@router.post("/alert/processAlert")
def process_alert_api( request: ProcessAlertRequest,
                      x_hahacar_token: str = Header(..., alias="X-HAHACAR-TOKEN"),
                        db:Session=Depends(get_db)):
    payload = verify_jwt_token(x_hahacar_token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(x_hahacar_token)
    return processAlert(db, request.alertId)


@router.get("/stat/alert/searchAlertNum")
def get_alert_count_api(db:Session=Depends(get_db),timeFrom: Optional[str] = Query(None),
    timeTo: Optional[str] = Query(None),
    cameraId: Optional[str] = Query(None)):
    print(f"timefrom:{timeFrom}")
    print(f"timeto:{timeTo}")
    print(f"cameraId:{cameraId}")

    request = GetAlertCountRequest(timeFrom=timeFrom, timeTo=timeTo, cameraId=cameraId)
    return getAlertNum(db, request)