from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from dependencies.database import get_db
from schemas.alert_schema import *
from services.alerts_service import *

router = APIRouter(prefix="/api", tags=["Alert"])

@router.get("/alert/getAlerts")
def get_alerts_api(request:GetAlertsRequest,db:Session=Depends(get_db)):
    return getAlerts(db, request)

@router.post("/alert/processAlert")
def process_alert_api(request:ProcessAlertRequest,token:str,db:Session=Depends(get_db)):
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(token)
    return processAlert(db, request)

@router.get("/stat/alert/searchAlertNum")
def get_alert_count_api(request:GetAlertCountRequest,db:Session=Depends(get_db)):
    return getAlertNum(db, request)