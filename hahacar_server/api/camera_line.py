from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from dependencies.database import get_db
from schemas.camera_line_schema import CameraLineUpdate
from services.camera_line_service import *

router = APIRouter(
    prefix="/camera",
    tags=["Camera Line"],
)

@router.post("/updateCameraLine")
def updateCameraLine_api(cameraLine: CameraLineUpdate, db: Session = Depends(get_db)):
    return updateCameraLine(db, cameraLine)


@router.get("/getCameraLines")
def getCameraLines_api(cameraId: str, token: str, db: Session = Depends(get_db)):
    return getCameraLine(db,token,cameraId)