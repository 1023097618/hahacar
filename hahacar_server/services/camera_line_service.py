import json
from typing import List

from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from models.camera_line import CameraLine
from schemas.camera_line_schema import CameraLineUpdate, CameraLineGet, CameraLineUpdateRequest
from schemas.camera_rule_schema import CameraRuleUpdateRequest


def getCameraLine(db: Session, cameraId: str,token:str):
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(token)
    cameraLines = db.query(CameraLine).filter(CameraLine.camera_id == cameraId).all()
    if not cameraLines:
        return {"code": "200",
                "msg": "cameraLine is None",
                "data": {}}

    camera_lines_data = [
        {
            "cameraLineName": line.line_name,
            "cameraLineStartX": line.start_x,
            "cameraLineStartY": line.start_y,
            "cameraLineEndX": line.end_x,
            "cameraLineEndY": line.end_y,
            "pointCloseToLine": line.point_close_to_line,
            "isMainLine": line.is_main_line,
            "cameraLineId": line.camera_line_id,
        }
        for line in cameraLines
    ]

    return {
        "code": "200",
        "msg": "success",
        "data": {
            "cameraLines": camera_lines_data,
            "isDefault": not any(line["isMainLine"] for line in camera_lines_data)
        }
    }


def get_camera_line(db: Session, cameraId: str):
    cameraLines = db.query(CameraLine).filter(CameraLine.camera_id == cameraId).all()
    if not cameraLines:
        return {"code": "200",
                "msg": "cameraLine is None",
                "data": {}}

    camera_lines_data = [
        {
            "cameraLineName": line.line_name,
            "cameraLineStartX": line.start_x,
            "cameraLineStartY": line.start_y,
            "cameraLineEndX": line.end_x,
            "cameraLineEndY": line.end_y,
            "pointCloseToLine": line.point_close_to_line,
            "isMainLine": line.is_main_line,
            "cameraLineId": line.camera_line_id,
        }
        for line in cameraLines
    ]

    return {
        "code": "200",
        "msg": "success",
        "data": {
            "cameraLines": camera_lines_data,
            "isDefault": not any(line["isMainLine"] for line in camera_lines_data)
        }
    }

#  TODO 这边删掉cameraLineId的时候需要同时删掉其他表中和这个cameraLineId相关联的数据，需要使用try catch更新
#   TODO 失败的话则db.rollback()
def updateCameraLine(db: Session, cameraLines: CameraLineUpdateRequest):
    cameraId = cameraLines.camera_id

    # 查询该摄像头下所有检测线
    existing_lines = db.query(CameraLine).filter(CameraLine.camera_id == cameraId).all()

    # 从请求中提取所有提供了 cameraLineId 的记录（过滤掉 None）
    request_line_ids = {line.cameraLineId for line in cameraLines.cameraLines if line and line.cameraLineId is not None}

    # 删除数据库中存在但请求中未包含的检测线记录
    for line in existing_lines:
        if line.camera_line_id not in request_line_ids:
            db.delete(line)
    db.commit()

    # 遍历请求中的每条检测线，进行新增或更新操作
    for cameraLineUpdate in cameraLines.cameraLines:
        if cameraLineUpdate is None:
            return {"code": "400", "msg": "Camera line data is None", "data": {}}

        # 如果请求中携带 cameraLineId，则尝试查找已有记录进行更新；否则视为新增
        if cameraLineUpdate.cameraLineId:
            existing_line = db.query(CameraLine).filter(
                CameraLine.camera_line_id == cameraLineUpdate.cameraLineId
            ).first()
        else:
            existing_line = None

        if not existing_line:
            # 创建新的检测线记录
            new_line = CameraLine(
                camera_id=cameraId,
                line_name=cameraLineUpdate.cameraLineName,
                start_x=cameraLineUpdate.cameraLineStartX,
                start_y=cameraLineUpdate.cameraLineStartY,
                end_x=cameraLineUpdate.cameraLineEndX,
                end_y=cameraLineUpdate.cameraLineEndY,
                point_close_to_line=cameraLineUpdate.pointCloseToLine,
                is_main_line=cameraLineUpdate.isMainLine,
            )
            db.add(new_line)
        else:
            # 更新已有检测线记录
            update_data = {
                "line_name": cameraLineUpdate.cameraLineName,
                "start_x": cameraLineUpdate.cameraLineStartX,
                "start_y": cameraLineUpdate.cameraLineStartY,
                "end_x": cameraLineUpdate.cameraLineEndX,
                "end_y": cameraLineUpdate.cameraLineEndY,
                "point_close_to_line": cameraLineUpdate.pointCloseToLine,
                "is_main_line": cameraLineUpdate.isMainLine,
            }
            db.query(CameraLine).filter(
                CameraLine.camera_line_id == existing_line.camera_line_id
            ).update(update_data)
    db.commit()
    from lifespan_manager import refresh_task
    refresh_task(cameraId)
    return {"code": "200", "msg": "success", "data": {}}
