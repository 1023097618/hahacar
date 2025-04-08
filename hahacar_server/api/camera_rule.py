from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from schemas.camera_rule_schema import *
from services.camera_rule_service import updateCameraRule, getCameraRule

router = APIRouter(prefix="/api/camera", tags=["Camera Rule"])


@router.post("/updateCameraRule")
def update_camera_rule_api(
        rule_update: CameraRuleUpdateRequest,
        db: Session = Depends(get_db)
):
    """
    **description**
    更新摄像头预警信息 API
    """

    # 这是正确的，service中不应该有关于返回的response的外层结构
    is_success = updateCameraRule(db, rule_update)
    if is_success:
        return {"code": "200", "msg": "success", "data": {}}
    else:
        return {"code": "402", "msg": "更新失败", "data": {}}


# 获取摄像头预警规则
@router.get("/getCameraRules", summary="获取摄像头预警规则")
def get_camera_rule_api(cameraId: str, db: Session = Depends(get_db)):
    """
    **description**
    获取摄像头的预警规则信息
    """
    # 这是正确的，service中不应该有关于返回的response的外层结构
    result = getCameraRule(db, cameraId)
    return {"code": "200", "msg": "success", "data": result}
