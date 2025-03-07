import asyncio
import json
import os

import cv2
import time
from fastapi import APIRouter, Depends, Query, HTTPException,WebSocket
from fastapi.responses import StreamingResponse

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
RTSP_URL = "rtsp://admin:zhishidiannaoka1@192.168.1.100:10554/udp/av0_0"

# **确保使用绝对路径**
UPLOAD_FOLDER = os.path.abspath("./static/camera/frames/")
SAVE_DIR = os.path.abspath("./static/camera/frames/")
INFO_DIR = os.path.abspath("./static/camera/info/")

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(INFO_DIR, exist_ok=True)

#检查摄像头是否连接成功
cap = cv2.VideoCapture(RTSP_URL)
if not cap.isOpened():
    print("无法打开摄像头")
else:
    print("摄像头连接成功")

cap.release()

#保存处理后的帧/信息函数
def save_processed_frame(frame, processedImg, detailedResult):
    # **筛选 labels，只保留 car, bus, van，truck**
    # target_classes = {"car", "bus", "van", "truck"}
    # filtered_labels = []
    # filtered_confidence = []
    # filtered_counts = {}
    #
    # for i, label in enumerate(detailedResult.get("labels", [])):
    #     if label in target_classes:
    #         filtered_labels.append(label)
    #         filtered_confidence.append(detailedResult["confidence"][i])  # 置信度
    #         filtered_counts[label] = filtered_counts.get(label, 0) + 1  # 计算出现次数

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
    processedImg, detailedResult = detector.detect(frame, addingBoxes=False, addingLabel=False, addingConf=False)
    return processedImg,detailedResult

# **视频流生成器**
async def generate_frames():
    cap = cv2.VideoCapture(RTSP_URL)

    while True:
        success, frame = cap.read()
        if not success:
            print("无法接收帧，等待重试...")
            time.sleep(1)
            continue

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
@router.get("/proxy_video_feed")
async def proxy_video_feed(token: str = Query(..., description="访问权限 Token")):
    """
    **description**
    代理 RTSP 视频流，并返回处理后的 MJPEG 流

    **params**
    - token (str): 访问权限 Token，防止未经授权的访问

    **returns**
    - StreamingResponse: 返回 MJPEG 视频流
    """
    # **Token 验证**
    if token is None or is_admin(token):
        print(f"isadmin:{is_admin(token)}")
        return JSONResponse(content={"code": "401", "data": {}, "msg": "Unauthorized"}, status_code=401)

    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


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

