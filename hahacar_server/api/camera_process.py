import asyncio
import json
import os

import cv2
import time
from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.camera import authenticate_admin
from core.security import verify_jwt_token
from dependencies.database import get_db
from services.camera_service import get_camera_url
from services.user_service import is_admin
from util.detector import Detector
from fastapi.responses import JSONResponse, FileResponse
from api.socket_manager import sio

router = APIRouter(prefix="/api")

# 服务器地址
URL = "http://localhost:8081"

# 加载 YOLO 模型
detector = Detector("./weights/yolov8n.pt")

# RTSP 摄像头地址
# RTSP_URL = "rtsp://admin:zhishidiannaoka1@192.168.1.101:10554/udp/av0_0"

# **确保使用绝对路径**
UPLOAD_FOLDER = os.path.abspath("./static/camera/uploads/")
SAVE_DIR = os.path.abspath("./static/camera/frames/")
INFO_DIR = os.path.abspath("./static/camera/info/")

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)

#保存处理后的帧/信息函数
def save_processed_frame(frame, processedImg, detailedResult):

    # 保存原始帧和处理后的图片
    timestamp = time.time_ns()
    origin_name = f"original_{timestamp}.jpg"
    file_name = f"processed_{timestamp}.jpg"
    file_path = os.path.join(SAVE_DIR, file_name)
    origin_path = os.path.join(UPLOAD_FOLDER, origin_name)
    cv2.imwrite(origin_path, frame)
    cv2.imwrite(file_path, processedImg)

    # **构造 JSON 数据**
    result_data = {
        "filename": file_name,
        "labels": detailedResult["labels"],
        "confidence": detailedResult["confidence"],
        "count": detailedResult["count"]
    }

    # **存储 JSON 结果**
    json_file_path = os.path.join(INFO_DIR, f"processed_{timestamp}.json")
    with open(json_file_path, "w") as json_file:
        json.dump(result_data, json_file, indent=4)

    print(f"Saved: {file_name} and {json_file_path}")


# **帧处理函数**
def process_frame(frame):
    """
    **description**
    示例：将图像转换为灰度图，你可以替换为你的机器学习模型处理逻辑。

    **params**
    - frame (np.ndarray): 读取的原始帧

    **returns**
    - np.ndarray: 处理后的帧
    """
    # 运行YOLOv8检测
    processedImg, detailedResult = detector.detect(frame, addingBoxes=True, addingLabel=True, addingConf=True)
    return processedImg,detailedResult

# **视频流生成器**
async def generate_frames(RTSP_URL:str):
    """
        :param rtsp_url: 摄像头地址
    """
    #设置超时时间
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

    # 如果还是没打开，直接 return，结束生成器
    if not cap.isOpened():
        print("摄像头无法连接，已放弃重试")
        return

    print("摄像头打开成功，开始读帧...")

    while True:
        success, frame = cap.read()
        if not success:
            print("无法接收帧，等待重试...")
        else:
            print("接收到帧")

        processed ,detailedResult = process_frame(frame)

        #保存原始帧、处理后的帧和信息
        save_processed_frame(frame, processed, detailedResult)

        # **Socket.IO 发送 JSON 结果**
        sio.emit("detection", detailedResult)

        ret, buffer = cv2.imencode('.jpg', processed)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

# **FastAPI 端点：返回 RTSP 直播流**
@router.get("/storage/getCameraLiveStream")
async def proxy_video_feed(
        cameraId: str = Query(..., description="摄像头 ID"),
        liveStreamType: str = Query(..., description="直播流类型"),
        # X_HAHACAR_TOKEN: str = Header(..., description="管理员访问权限 Token"),
        token: str = Query(..., description="管理员访问权限 Token"),
        db: Session = Depends(get_db)
        ):
    """
    **description**
    代理 RTSP 视频流，并返回处理后的 MJPEG 流

    **params**
    - cameraId (str): 摄像头 ID（必须）
    - liveStreamType (str): 直播流类型（可选，'preview' 或 'full'，默认 'preview'）
    - token (str): 访问权限 Token

    **returns**
    - StreamingResponse: 返回 MJPEG 视频流
    """
    # **验证管理员权限**
    token_payload = verify_jwt_token(token)
    if not token_payload or not token_payload.get("is_admin"):
        return {"code": "403", "msg": "Unorthrize", "data": {}}

    #获取摄像头URL
    cameraURL = get_camera_url(db, cameraId)
    if not cameraURL:
        return JSONResponse(content={"code": "404", "data": {}, "msg": "Camera not found"}, status_code=404)

    #根据liveStreamType选择不同的流
    if liveStreamType == 'full':
        rtsp_url = f"{cameraURL}?stream=full"
    else:
        rtsp_url = f"{cameraURL}?stream=preview"

    print(f"正在拉取 RTSP 直播流: {rtsp_url}")
    # 先尝试打开摄像头
    # 设置超时时间
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;5000"
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        return JSONResponse({"code": "400", "msg": "无法连接摄像头", "data": {}}, status_code=400)

    return StreamingResponse(generate_frames(rtsp_url), media_type="multipart/x-mixed-replace; boundary=frame")


# **Socket.IO 端点：发送 YOLOv8 检测结果**
@sio.event
async def video_feed(sid):
    """
    **description**
    Socket.IO 连接，实时推送 YOLOv8 目标检测结果（不包含视频流）。

    **params**
    - sid: Socket.IO 连接 ID

    **returns**
    - 实时 JSON 数据
    """
    print(f"Socket.IO Client connected: {sid}")

    try:
        # **调用 generate_frames() 处理帧**
        async for frame in generate_frames():  #`async for` 以异步方式处理数据
            # 发送处理结果
            await sio.emit("detection", frame, room=sid)

    except Exception as e:
        print(f"Socket.IO 连接断开: {e}")

