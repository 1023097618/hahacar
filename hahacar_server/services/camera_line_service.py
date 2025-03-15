from sqlalchemy.orm import Session

from core.security import verify_jwt_token
from models.camera_line import CameraLine
from schemas.camera_line_schema import CameraLineUpdate


def getCameraLine(db: Session, cameraId: str,token:str):
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return verify_jwt_token(token)
    cameraLine = db.query(CameraLine).filter(CameraLine.camera_id == cameraId).first()
    if not cameraLine:
        return {"code": "400",
                "msg": "cameraLine is None",
                "data": {}}
    return {"code": "200",
            "msg": "success",
            "data":{
                "cameraLines": [
                    CameraLineUpdate.from_orm(cameraLine).dict()
                ]
            }
    }


def updateCameraLine(db: Session, cameraLine: CameraLineUpdate):
    if cameraLine is None:
        return {"code": "400", "msg": "cameraLine is None", "data": {}}
        existing_line = db.query(CameraLine).filter(CameraLine.line_name == cameraLine.cameraLineName).first()
        if not existing_line:
            return {"code": "404", "msg": "Camera line not found", "data": {}}

        update_data = {
            "line_name": cameraLine.cameraLineName,
            "start_x": cameraLine.cameraLineStartX,
            "start_y": cameraLine.cameraLineStartY,
            "end_x": cameraLine.cameraLineEndX,
            "end_y": cameraLine.cameraLineEndY,
            "point_close_to_line": cameraLine.pointCloseToLine,  # 这里是 JSON 类型
            "is_main_line": cameraLine.isMainLine,
        }

        db.query(CameraLine).filter(CameraLine.line_name == cameraLine.cameraLineName).update(update_data)
        db.commit()

        updated_camera_line = db.query(CameraLine).filter(CameraLine.line_name == cameraLine.cameraLineName).first()

        return {
            "code": "200",
            "msg": "Update successful",
            "data": CameraLineUpdate.from_orm(updated_camera_line).dict()
        }
