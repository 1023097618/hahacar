import traceback
import uuid


from sqlalchemy.orm import Session

from models.CarThroughRoute import CarThroughRoute
from models.alert import Alert
from models.camera import Camera
from models.camera_detect_info import camera_detect_info
from models.camera_line import CameraLine
from models.user_camera import UserCamera
from schemas.camera_line_schema import CameraLineUpdateRequest
from schemas.camera_rule_schema import CameraRuleUpdateRequest
from schemas.camera_schema import CameraCreate, CameraUpdate
from core.security import verify_jwt_token
from services.camera_line_service import updateCameraLine
from services.camera_rule_service import updateCameraRule


def add_camera(db: Session, token: str, camera_data: CameraCreate): #由fastapi依赖注入统一管理不需要手动关闭
    """
    **description**
    添加新的摄像头，需管理员权限

    **params**
    db: 数据库会话
    token: 管理员 JWT 令牌
    camera_data: 摄像头创建数据

    **returns**
    添加成功返回摄像头 ID，失败返回 None
    """
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return None

    camera_id = str(uuid.uuid4())  # 生成唯一 ID
    camera_URL = camera_data.cameraURL.replace("\u202a", " ")
    new_camera = Camera(
        id=camera_id,
        cameraURL=camera_URL,
        cameraLocation=",".join(camera_data.cameraLocation),
        cameraName=camera_data.cameraName
    )
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    from lifespan_manager import add_task
    add_task(camera_id)
    return camera_id

def get_cameras(db: Session, token: str, pageNum: int, pageSize: int, cameraName: str = None):
    """
    **description**
    获取摄像头列表，需管理员权限，支持分页和按名称查询

    **params**
    db: 数据库会话
    token: 管理员 JWT 令牌
    pageNum: 当前页码
    pageSize: 每页大小
    cameraName: 过滤的摄像头名称（可选）

    **returns**
    包含摄像头列表的字典，若无权限返回 None
    """
    payload = verify_jwt_token(token)
    if not payload:
        return None

    query = db.query(Camera)
    if cameraName:
        query = query.filter(Camera.cameraName.like(f"%{cameraName}%"))

    total_count = query.count()
    cameras = query.offset((pageNum - 1) * pageSize).limit(pageSize).all()

    return {
        "cameras": [
            {
                "cameraId": cam.id,
                # "cameraLiveStreamPreviewURL": cam.cameraURL,
                "cameraLocation": cam.cameraLocation.split(","),
                "cameraName": cam.cameraName,
                "cameraURL":cam.cameraURL
            }
            for cam in cameras
        ],
        "cameraNum": total_count
    }

def delete_camera(db: Session, token: str, camera_id: str):
    """
    **description**
    删除摄像头，需管理员权限

    **params**
    db: 数据库会话
    token: 管理员 JWT 令牌
    camera_id: 需要删除的摄像头 ID

    **returns**
    删除成功返回 True，失败返回 False
    """
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return False

    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        return False
    try:
        db.query(CameraLine).filter(CameraLine.camera_id==camera_id)
        camera_rule = CameraRuleUpdateRequest(camera_id=camera_id,cameraRules=[])
        updateCameraRule(db,camera_rule)
        camera_line = CameraLineUpdateRequest(camera_id=camera_id,cameraLines=[])
        updateCameraLine(db,camera_line)
        db.query(camera_detect_info).filter(camera_detect_info.camera_id==camera_id).delete(synchronize_session=False)
        db.query(CarThroughRoute).filter(CarThroughRoute.camera_id==camera_id).delete(synchronize_session=False)
        db.query(UserCamera).filter(UserCamera.camera_id==camera_id).delete(synchronize_session=False)
        db.query(Alert).filter(Alert.camera_id==camera_id).delete(synchronize_session=False)
        db.query(Camera).filter(Camera.id==camera_id).delete(synchronize_session=False)
        from lifespan_manager import cancel_task
        cancel_task(camera_id)
        db.commit()
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        return False

    return True

def update_camera(db: Session, token: str, camera_data: CameraUpdate):
    """
    **description**
    更新摄像头信息，需管理员权限

    **params**
    db: 数据库会话
    token: 管理员 JWT 令牌
    camera_data: 摄像头更新数据

    **returns**
    更新成功返回 True，失败返回 False
    """
    payload = verify_jwt_token(token)
    if not payload or not payload.get("is_admin"):
        return False

    camera = db.query(Camera).filter(Camera.id == camera_data.cameraId).first()
    if not camera:
        return False

    camera.cameraURL = camera_data.cameraURL
    camera.cameraLocation = ",".join(camera_data.cameraLocation)
    camera.cameraName = camera_data.cameraName
    db.commit()
    camera_id=camera_data.cameraId
    from lifespan_manager import refresh_task
    refresh_task(camera_id)
    return True

def get_camera_url(db:Session, camera_id:str):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        print("camera not found")
        return None
    return camera.cameraURL

def get_all_camera_ids(db: Session):
    # 返回一个 ID 组成的 list，而不是 SQLAlchemy Row
    return [row[0] for row in db.query(Camera.id).all()]



def get_camera_name_by_id(db:Session,camera_id:str):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        print("camera not found")
        return None
    return camera.cameraName
