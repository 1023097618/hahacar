from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from schemas.camera_rule_schema import *
from services.camera_rule_service import updateCameraRule,getCameraRule

router = APIRouter(prefix="/api/camera")
@router.get("/updateCameraRule")
def update_camera_rule_api(
        rule_update: CameraRuleUpdate,
        db: Session = Depends(get_db)
):
    """
    **description**
    更新摄像头预警信息 API
    """

    return updateCameraRule(db, rule_update)

# 获取摄像头预警规则
@router.get("/getCameraRules", summary="获取摄像头预警规则")
def get_camera_rule_api(cameraId: str, db: Session = Depends(get_db)):
    """
    **description**
    获取摄像头的预警规则信息
    """
    return getCameraRule(db, cameraId)