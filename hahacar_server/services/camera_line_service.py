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


#这里由于没有给出cameralineid，是根据cameralinename进行更新的，所以要求前端返回的cameralinename不同
def updateCameraLine(db: Session, cameraLines: CameraLineUpdateRequest):
    cameraId = cameraLines.camera_id
    for cameraLineUpdate in cameraLines.cameraLines:
        if cameraLineUpdate is None:
            return {"code": "400", "msg": "cameraLine is None", "data": {}}

        existing_line = db.query(CameraLine).filter(
            CameraLine.line_name == cameraLineUpdate.cameraLineName,
        ).first()

        if not existing_line:
            new_line = CameraLine(
                camera_id=cameraId,
                line_name=cameraLineUpdate.cameraLineName,
                start_x=cameraLineUpdate.cameraLineStartX,
                start_y=cameraLineUpdate.cameraLineStartY,
                end_x=cameraLineUpdate.cameraLineEndX,
                end_y=cameraLineUpdate.cameraLineEndY,
                point_close_to_line=cameraLineUpdate.pointCloseToLine,  # 这里是 JSON 类型
                is_main_line=cameraLineUpdate.isMainLine,
            )
            db.add(new_line)
            db.commit()
            # return {"code": "200",
            #         "msg": "success",
            #         "data": {
            #             "cameraLines": [
            #                 CameraLineUpdate.from_orm(new_line).dict()
            #             ],
            #             "cameraId": cameraId
            #         }
            # }

        else:
            update_data = {
                "line_name": cameraLineUpdate.cameraLineName,
                "start_x": cameraLineUpdate.cameraLineStartX,
                "start_y": cameraLineUpdate.cameraLineStartY,
                "end_x": cameraLineUpdate.cameraLineEndX,
                "end_y": cameraLineUpdate.cameraLineEndY,
                "point_close_to_line": cameraLineUpdate.pointCloseToLine,  # 这里是 JSON 类型
                "is_main_line": cameraLineUpdate.isMainLine,
            }

            db.query(CameraLine).filter(CameraLine.line_name == existing_line.line_name).update(update_data)
            db.commit()

    return {
        "code": "200",
        "msg": "success",
        "data": {
        }
    }
