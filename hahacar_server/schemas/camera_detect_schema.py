import json
from typing import Optional, Dict

from pydantic import BaseModel

"""
    ***查询车辆类别、车流量、车拥挤度***
"""

class TrafficFlowResponse(BaseModel):
    flowTime: str
    flowNum: str


class TrafficHoldResponse(BaseModel):
    holdTime: str
    holdNum: str


class VehicleLabelResponse(BaseModel):
    labelName: str
    labelNum: str

class GetTrafficFlowRequest(BaseModel):
    timeFrom: Optional[str]
    timeTo: Optional[str]
    cameraId: Optional[str]
    cameraLineIdStart: Optional[str]    #为str或None
    cameraLineIdEnd: Optional[str]
    cameraLineId: Optional[str]

class GetTrafficHoldRequest(BaseModel):
    timeFrom: Optional[str]
    timeTo: Optional[str]
    cameraId: Optional[str]

class GetVehicleLabelRequest(BaseModel):
    timeFrom: Optional[str]
    timeTo: Optional[str]
    cameraId: Optional[str]

"""
    ***存储车辆类别、车流量、车拥挤度***
    暂时设定10s求平均保存一次
"""

class TrafficFlowSaveRequest(BaseModel):
    cameraId: str
    cameraLineId: Optional[str]
    cameraLineIdStart: Optional[str]
    cameraLineIdEnd: Optional[str]
    flowTime: str
    flowNum: str

class TrafficHoldSaveRequest(BaseModel):
    cameraId: str
    holdTime: str
    holdNum: str

class VehicleLabelSaveRequest(BaseModel):
    cameraId: str
    detected_cars_labels: Dict[str,str]