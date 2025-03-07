import json
import os
import time
import uuid
import socketio

import cv2
from fastapi import APIRouter, UploadFile, WebSocketDisconnect, BackgroundTasks, File, HTTPException, WebSocket, Header
from fastapi.responses import JSONResponse, FileResponse
from starlette.websockets import WebSocketState

from api.socket_manager import sio
from services.user_service import is_admin
from util.detector import Detector

router = APIRouter(prefix="/api")

# **确保使用绝对路径**
UPLOAD_FOLDER = os.path.abspath("../static/uploads/videos/")        #存储原始上传视频
SAVE_FOLDER = os.path.abspath("../static/processed/videos/frames")  #用于存储视频每帧的处理后图片
PROCESSED_FOLDER = os.path.abspath("../static/processed/videos/")   #存储处理后视频
FRAMES_INFO_FOLDER =  os.path.abspath("../static/processed/videos/frames/info")  #用于存储视频每帧的处理后图片的信息

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(FRAMES_INFO_FOLDER, exist_ok=True)

# 服务器地址
URL = "http://localhost:8081"

# 加载 YOLO 模型
detector = Detector("./weights/yolov8n.pt")

#存储websocket客户端连接
active_connections = {}
# active_connections["test-sid"] = None  # 这里可以模拟 WebSocket 连接，测试阶段——发布删除

@sio.event
async def connect(sid, environ):
    print(f"客户端连接: {sid}")
    active_connections[sid] = {"sid": sid}

@sio.event
async def disconnect(sid):
    print(f"客户端断开: {sid}")
    if sid in active_connections:
        del active_connections[sid]

# **视频上传 & 目标检测**
@router.post("/storage/videoUpload")
async def video_detect(
        background_tasks: BackgroundTasks,
        video: UploadFile = File(...),
        token: str = Header(None, alias="X-HAHACAR-TOKEN"),
        sid: str = Header(None, alias="X-HAHACAR-SOCKET")):   #测试时使用
    """
    **description**
    接收视频文件，后台进行目标检测，并通过 WebSocket 实时推送处理进度。

    **params**
    - video (UploadFile): 上传的视频文件。
    - sid (str): WebSocket 客户端 ID。

    **returns**
    - JSON: 任务状态
    """

    # **Token 验证**
    if token is None or not is_admin(token):
        return JSONResponse(content={"code": "401", "data": {}, "msg": "Unauthorized"}, status_code=401)

    if not sid or sid not in active_connections:
        return JSONResponse(content={"code": "400","data":{}, "msg": "Invalid or missing Socket ID"}, status_code=400)

    # **生成唯一 task_id**
    task_id = str(uuid.uuid4())

    # **保存原始视频**
    original_filename = f"video_{task_id}.mp4"
    original_filepath = os.path.join(UPLOAD_FOLDER, original_filename)

    with open(original_filepath, "wb") as buffer:
        buffer.write(await video.read())

    # 传给yolo处理
    background_tasks.add_task(process_video, original_filepath, task_id, sid)

    return JSONResponse(content={"code": "200", "msg": "File processing started", "data":{"taskId": task_id}},
                        status_code=200)


async def process_video(file_path: str, task_id: str, sid: str):
    """
    **description**
    逐帧处理视频，使用yolov8检测，并通过 WebSocket 发送进度更新。

    **params**
    - file_path (str): 原始视频路径
    - task_id (str): 任务 ID
    - sid (str): WebSocket 客户端 ID

    **returns**
    - None
    """
    # 先检查 sid 是否还在线
    if sid not in active_connections:
        print(f"SID {sid} not in active_connections")
        return

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        await sio.emit("errormsg",{"code": "400", "msg": "无法打开视频文件","data":{}}, to=sid)
        return

    # **视频参数**
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0 or fps is None:
        fps = 30.0  # 设置默认帧率，避免错误
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        await sio.emit("errormsg",{"code": "400", "msg": "视频文件无效，没有可处理的帧", "data": {}}, to=sid)
        cap.release()
        return

    # **初始化视频写入器**
    processed_filename = f"processed_{task_id}.mp4"
    processed_filepath = os.path.join(PROCESSED_FOLDER, processed_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # H.264 / MP4
    out = cv2.VideoWriter(processed_filepath, fourcc, fps, (frame_width, frame_height))

    target_classes = {"car", "bus", "van", "truck"}

    # **逐帧运行yolo检测处理**
    frame_index = 0
    while True:
        ret, frame = cap.read()  # 读取视频帧
        if not ret:
            break

        processedImg, detailedResult = detector.detect(frame, addingBoxes=False, addingLabel=False, addingConf=False)
        # **筛选 labels，只保留 car, bus, van,truck**
        filtered_labels = []
        filtered_confidence = []
        filtered_counts = {}

        #后面需要在模型那里改不然效率太低了
        for i, label in enumerate(detailedResult.get("labels", [])):
            if label in target_classes:
                filtered_labels.append(label)
                filtered_confidence.append(detailedResult["confidence"][i])  # 置信度
                filtered_counts[label] = filtered_counts.get(label, 0) + 1  # 计算出现次数

                # 保存处理后的图片
                timestamp = time.time_ns()
                file_name = f"processed_{timestamp}.jpg"
                file_path = os.path.join(SAVE_FOLDER, file_name)
                cv2.imwrite(file_path, cv2.cvtColor(processedImg, cv2.COLOR_RGB2BGR))

                # **构造 JSON 数据**
                result_data = {
                    "filename": file_name,
                    "labels": filtered_labels,
                    "confidence": filtered_confidence,
                    "count": filtered_counts
                }

                # **存储 JSON 结果**
                json_file_path = os.path.join(FRAMES_INFO_FOLDER, f"processed_{timestamp}.json")
                with open(json_file_path, "w") as json_file:
                    json.dump(result_data, json_file, indent=4)

                print(f"Saved: {file_name} and {json_file_path}")
        # **写入处理后的视频帧**
        out.write(cv2.cvtColor(processedImg, cv2.COLOR_RGB2BGR))

        # 模拟处理进度：从 0 到 100，每 10% 更新一次，视频处理结束之前发送progressValue和taskId
        progress = int((frame_index / total_frames) * 100) if total_frames > 0 else 0
        if progress % 10 == 0:  # 每 10% 更新一次
            try:
                await sio.emit("progress",{"progressValue": progress, "taskId": task_id},to=sid)
            except Exception as e:
                print(f"WebSocket send error: {e}")
                return

        frame_index += 1  # 递增帧索引

    cap.release()  # 释放视频资源
    out.release()   #关闭视频写入器

    # 构造返回的 URL
    watchURL = f"{URL}/api/watch/video/{processed_filename}"
    downloadURL = f"{URL}/api/download/video/{processed_filename}"

    # **任务完成**
    # 结束之后发送taskId、watchurl和downloadurl
    done_data = {
        "taskId": task_id,
        "watchURL": watchURL,
        "downloadURL": downloadURL,
        "fileName": processed_filename
    }
    await sio.emit("doneProgress", done_data, to=sid)

# **提供视频的在线查看功能**
@router.get("/watch/video/{filename}")
def watch_video(filename: str):
    """
    **description**
    提供处理后的视频播放功能。

    **params**
    - filename (str): 需要播放的视频文件名。

    **returns**
    - 视频文件流
    """
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        return {"code": "404", "msg": "File not found", "data": ""}
    return FileResponse(file_path, media_type="video/mp4")


# **提供视频的下载功能**
@router.get("/download/video/{filename}")
def download_video(filename: str):
    """
    **description**
    提供处理后的视频下载功能。

    **params**
    - filename (str): 需要下载的视频文件名。

    **returns**
    - 视频文件流
    """
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        return {"code": "404", "msg": "File not found", "data": ""}
    return FileResponse(file_path, filename=filename, media_type="video/mp4")