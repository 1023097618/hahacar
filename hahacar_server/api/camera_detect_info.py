from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from schemas.camera_detect_schema import *
from services.camera_detect_info_service import *

router = APIRouter(
    prefix="/api/stat",
    tags=["camera_detect_info"],
)

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""
@router.get("/category/searchCategoryNum")
def searchCategoryNum(
    request: GetTrafficFlowRequest,
    db: Session = Depends(get_db)
):
    return get_vehicle_labels(db,request)

#获取一段时间车的拥挤度
@router.get("/hold/searchHoldNum")
def searchHoldNum(
    request: GetTrafficHoldRequest,
    db: Session = Depends(get_db)
):
    return get_traffic_hold(db,request)

#获取一段时间内车流量
@router.get("/flow/searchFlowNum")
def searchFlowNum(
    request: GetTrafficFlowRequest,
    db: Session = Depends(get_db)
):
    return get_traffic_flow(db,request)

"""
    ***存储车辆类别、车流量、车拥挤度***
"""
@router.post("/category/saveCategoryNum")
def saveCategoryNum(
    request: VehicleLabelSaveRequest,
    db: Session = Depends(get_db)
):
    return save_vehicle_labels(db,request)

@router.post("/hold/saveHoldNum")
def saveHoldNum(
    request: TrafficHoldSaveRequest,
    db: Session = Depends(get_db)
):
    return save_traffic_hold(db,request)

@router.post("/flow/saveFlowNum")
def saveFlowNum(
    request: TrafficFlowSaveRequest,
    db: Session = Depends(get_db)
):
    return save_traffic_flow(db,request)