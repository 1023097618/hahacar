from sqlalchemy.orm import Session

from api.socket_manager import sio
from models.alert import Alert
from models.camera import Camera
from dependencies.database import get_db, SessionLocal

# 全局或单例存储摄像头状态
camera_status = {
}
def build_camera_status(db: Session) -> dict:
    """
    从数据库查询所有摄像头信息，以及是否有进行中的预警，返回一个字典:
    {
        cameraId1: {"online": bool, "alert": bool},
        cameraId2: {"online": bool, "alert": bool},
        ...
    }
    """
    camera_status = {}

    # 1) 查询所有摄像头
    cameras = db.query(Camera).distinct().all()

    for cam in cameras:
        camera_id = cam.id
        # 2) 判断是否有进行中的预警(比如 alert_type=1)
        ongoing_alert = db.query(Alert).filter(
            Alert.camera_id == camera_id,
            Alert.alert_type == '1'
        ).first()

        # 只需判断有没有进行中的预警 => bool
        has_alert = True if ongoing_alert else False

        # 3) 填充到 camera_status 字典
        camera_status[camera_id] = {
            "online": False,   # 默认不上线
            "alert": has_alert      # 是否有进行中预警
        }

    return camera_status

@sio.event
async def connect(sid, environ):
    """
    当客户端新连接时，发送所有摄像头的初始状态到此客户端。
    """
    print(f"[socket] Client connected:发送摄像头状态 {sid}")

    # 1) 新建数据库会话
    db = SessionLocal()
    try:
        # 2) 查询最新的 camera_status
        new_status = build_camera_status(db)
    finally:
        db.close()

    # 3) 构造 camera_list
    camera_list = []
    for cid, st in new_status.items():
        camera_list.append({
            "cameraId": cid,
            "online": st["online"],
            "alert": st["alert"]
        })

    await sio.emit("cameraSituation", camera_list, room=sid)

async def update_camera_status(camera_id: str, new_online: bool, new_alert: bool):
    """
    当摄像头状态发生变更时调用：
    - 更新 camera_status
    - 广播给所有已连接的客户端
    """
    camera_status[camera_id] = {
        "online": new_online,
        "alert": new_alert
    }
    # 构造要广播的数据对象
    payload = {
        "cameraId": camera_id,
        "online": new_online,
        "alert": new_alert
    }
    # 给所有已连接的客户端发送状态变更
    await sio.emit("cameraSituation", payload)
    # 或:
    # sio.emit("cameraStatusChanged", payload, broadcast=True)
    # (两者效果相同，都广播给所有房间/客户端)

def refresh_camera_status(db: Session):
    """
    重新从数据库查询所有摄像头的 online / alert 状态，
    与现有 camera_status 做对比，有变更则调用 update_camera_status。
    """
    # 1) 查所有摄像头
    cameras = db.query(Camera).all()

    for cam in cameras:
        camera_id = cam.id
        # 2) 判断是否有进行中的预警(如 alert_type='1')
        ongoing_alert = db.query(Alert).filter(
            Alert.camera_id == camera_id,
            Alert.alert_type == '1'
        ).first()
        has_alert = True if ongoing_alert else False

        # 3) 比对
        old_status = camera_status.get(camera_id, {"online": None, "alert": None})
        new_online = old_status["online"]
        new_alert = has_alert

        # 如果有变化，就更新并推送
        if new_online != old_status["online"] or new_alert != old_status["alert"]:
            # 调用 update_camera_status 来广播
            update_camera_status(camera_id, new_online, new_alert)