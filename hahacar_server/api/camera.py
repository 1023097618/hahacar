import os
import sys
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from dependencies.database import get_db
from core.security import verify_jwt_token
from schemas.camera_schema import CameraCreate, CameraUpdate, CameraDelete
from services.camera_service import add_camera, get_cameras, delete_camera, update_camera

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

router = APIRouter(prefix="/api/camera", tags=["Camera"])


def authenticate_admin(X_HAHACAR_TOKEN: str = Header(...)):
    """
    **description**
    验证管理员权限，不知道为什么总是测的相反——这个bug待会再改
    """
    payload = verify_jwt_token(X_HAHACAR_TOKEN)
    print(verify_jwt_token(X_HAHACAR_TOKEN))
    if "is_admin" not in payload:
        print("Warning: is_admin not found in JWT payload")
        return {"code": "403", "msg": "is_admin not found in JWT payload", "data": {}}
    if not payload or not bool(payload.get("is_admin")):
        return {"code": "403", "msg": "Forbidden", "data": {}}
    return X_HAHACAR_TOKEN


@router.post("/addCamera")
def add_camera_api(
        camera_data: CameraCreate,
        db: Session = Depends(get_db),
        token: str = Depends(authenticate_admin)
):
    """
    **description**
    添加摄像头 API

    **params**
    camera_data: 摄像头信息
    db: 数据库会话
    token: 管理员 JWT 令牌

    **returns**
    添加成功返回摄像头 ID
    """
    camera_id = add_camera(db, token, camera_data)
    if not camera_id:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"code": "200", "msg": "Camera added successfully", "data": {"cameraId": camera_id}}


@router.get("/getCameras")
def get_cameras_api(
        pageNum: int = Query(...),
        pageSize: int = Query(...),
        cameraName: str = Query(None),
        db: Session = Depends(get_db),
        token: str = Depends(authenticate_admin)
):
    """
    **description**
    获取摄像头列表 API

    **params**
    pageNum: 当前页码
    pageSize: 每页数量
    cameraName: 摄像头名称（可选）
    db: 数据库会话
    token: 管理员 JWT 令牌

    **returns**
    摄像头列表
    """
    result = get_cameras(db, token, pageNum, pageSize, cameraName)
    if result is None:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"code": "200", "msg": "Success", "data": result}


@router.delete("/deleteCamera")
def delete_camera_api(
        camera_data: CameraDelete,
        db: Session = Depends(get_db),
        token: str = Depends(authenticate_admin)
):
    """
    **description**
    删除摄像头 API

    **params**
    camera_data: 需要删除的摄像头 ID
    db: 数据库会话
    token: 管理员 JWT 令牌

    **returns**
    删除成功或失败信息
    """
    success = delete_camera(db, token, camera_data.cameraId)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"code": "200", "msg": "Camera deleted successfully", "data": {}}


@router.post("/updateCamera")
def update_camera_api(
        camera_data: CameraUpdate,
        db: Session = Depends(get_db),
        token: str = Depends(authenticate_admin)
):
    """
    **description**
    更新摄像头信息 API

    **params**
    camera_data: 摄像头更新信息
    db: 数据库会话
    token: 管理员 JWT 令牌

    **returns**
    更新成功或失败信息
    """
    success = update_camera(db, token, camera_data)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"code": "200", "msg": "Camera updated successfully", "data": {}}
