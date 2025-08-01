from typing import List

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from dependencies.database import get_db
from schemas.camera_line_schema import CameraLineUpdate, CameraLineUpdateRequest
from services.camera_line_service import *

router = APIRouter(
    prefix="/api/camera",
    tags=["Camera Line"],
)

@router.post("/updateCameraLine")
def updateCameraLine_api(cameraLines: CameraLineUpdateRequest, db: Session = Depends(get_db)):
    return updateCameraLine(db, cameraLines)



@router.get("/getCameraLines")
def getCameraLines_api(cameraId: str,
                       X_HAHACAR_TOKEN: str = Header(..., description="管理员访问权限 Token"), db: Session = Depends(get_db)):
    return getCameraLine(db,cameraId,X_HAHACAR_TOKEN)