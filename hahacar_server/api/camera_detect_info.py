from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from dependencies.database import get_db
from schemas.camera_detect_schema import *
from services.camera_detect_info_service import *

router = APIRouter(
    prefix="/api/stat",
    tags=["Camera Detect Info"],
)

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""
@router.get("/category/searchCategoryNum")
def searchCategoryNum(
    timeFrom: Optional[str] = Query(None, description="开始时间"),
    timeTo: Optional[str] = Query(None, description="结束时间"),
    cameraId: Optional[str] = Query(None, description="摄像头 ID"),
    db: Session = Depends(get_db)
):
    request = GetVehicleLabelRequest(
        timeFrom=timeFrom,
        timeTo=timeTo,
        cameraId=cameraId
    )
    formatted_results = get_vehicle_labels(db, request)
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "labels": formatted_results
        }
    }

#获取一段时间车的拥挤度
@router.get("/hold/searchHoldNum")
def searchHoldNum(
    timeFrom: Optional[str] = Query(None, description="开始时间"),
    timeTo: Optional[str] = Query(None, description="结束时间"),
    cameraId: Optional[str] = Query(None, description="摄像头 ID"),
    db: Session = Depends(get_db)
):
    request = GetTrafficHoldRequest(
        timeFrom=timeFrom,
        timeTo=timeTo,
        cameraId=cameraId
    )
    result = get_traffic_hold(db, request)
    return {"code": "200", "msg": "success", "data": {"holds": result}}


@router.get("/flow/searchFlowNum")
def searchFlowNum(
    timeFrom: Optional[str] = Query(None, description="开始时间"),
    timeTo: Optional[str] = Query(None, description="结束时间"),
    cameraId: Optional[str] = Query(None, description="摄像头 ID"),
    cameraLineIdStart: Optional[str] = Query(None, description="起始检测线 ID"),
    cameraLineIdEnd: Optional[str] = Query(None, description="终止检测线 ID"),
    cameraLineId: Optional[str] = Query(None, description="检测线 ID"),
    db: Session = Depends(get_db)
):
    request = GetTrafficFlowRequest(
        timeFrom=timeFrom,
        timeTo=timeTo,
        cameraId=cameraId,
        cameraLineIdStart=cameraLineIdStart,
        cameraLineIdEnd=cameraLineIdEnd,
        cameraLineId=cameraLineId
    )
    formatted_results = get_traffic_flow(db, request)
    return {"code": "200", "msg": "success", "data": {"flows": formatted_results}}

@router.get("/flow/getFlowMat")
def getFlowMat(
    timeFrom: Optional[str] = Query(None, description="开始时间"),
    timeTo: Optional[str] = Query(None, description="结束时间"),
    cameraId: Optional[str] = Query(None, description="摄像头 ID"),
    db: Session = Depends(get_db)
):
    request=GetTrafficFlowMatRequest(
        timeFrom=timeFrom,
        timeTo=timeTo,
        cameraId=cameraId
    )
    return get_traffic_flow_mat(db,request)