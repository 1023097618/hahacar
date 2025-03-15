from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AlertResponse(BaseModel):
    alertId: str
    cameraId: str
    cameraName: str
    alertType: str
    alertStartTime: str
    alertEndTime: Optional[str]
    alertProcessedTime: Optional[str]
    alertImage: str
    ruleType: str
    ruleRemark: str
    alertNum: int

    class Config:
        orm_mode = True

class GetAlertsRequest(BaseModel):
    pageNum: str
    pageSize: str
    alertType: Optional[List[str]]
    cameraId: Optional[str]
    alertStartTimeFrom: Optional[str]
    alertStartTimeTo: Optional[str]
    alertId: Optional[str]

class ProcessAlertRequest(BaseModel):
    alertId: str

class AlertCountResponse(BaseModel):
    AlertTime: str
    AlertNum: str

class GetAlertCountRequest(BaseModel):
    timeFrom: Optional[str]
    timeTo: Optional[str]
    cameraId: Optional[str]
