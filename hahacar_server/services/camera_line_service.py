import json
from typing import List

from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from models.camera_line import CameraLine
from schemas.camera_line_schema import CameraLineUpdate, CameraLineGet



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


def updateCameraLine(db: Session, cameraLine: CameraLineUpdate,cameraId: str):
    if cameraLine is None:
        return {"code": "400", "msg": "cameraLine is None", "data": {}}

    existing_line = db.query(CameraLine).filter(
        CameraLine.camera_id == cameraId,
    ).first()

    if not existing_line:
        new_line = CameraLine(
            camera_id=cameraId,
            line_name=cameraLine.cameraLineName,
            start_x=cameraLine.cameraLineStartX,
            start_y=cameraLine.cameraLineStartY,
            end_x=cameraLine.cameraLineEndX,
            end_y=cameraLine.cameraLineEndY,
            point_close_to_line=cameraLine.pointCloseToLine,  # 这里是 JSON 类型
            is_main_line=cameraLine.isMainLine,
        )
        db.add(new_line)
        db.commit()
        return {"code": "200",
                "msg": "success",
                "data": {
                    "cameraLines": [
                        CameraLineUpdate.from_orm(new_line).dict()
                    ],
                    "cameraId": cameraId
                }
        }


    update_data = {
        "line_name": cameraLine.cameraLineName,
        "start_x": cameraLine.cameraLineStartX,
        "start_y": cameraLine.cameraLineStartY,
        "end_x": cameraLine.cameraLineEndX,
        "end_y": cameraLine.cameraLineEndY,
        "point_close_to_line": cameraLine.pointCloseToLine,  # 这里是 JSON 类型
        "is_main_line": cameraLine.isMainLine,
    }

    db.query(CameraLine).filter(CameraLine.camera_line_id == existing_line.camera_line_id).update(update_data)
    db.commit()

    return {
        "code": "200",
        "msg": "success",
        "data": {
        }
    }
