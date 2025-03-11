import time
import os
import io
import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image
from util.detector import Detector

router = APIRouter(prefix="/api")

# **确保使用绝对路径**
UPLOAD_FOLDER = os.path.abspath("./static/uploads/frames/")
SAVE_DIR = os.path.abspath("./static/processed/frames/")

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

# 服务器地址
URL = "http://localhost:8081"

# 加载 YOLO 模型
detector = Detector("./weights/yolov8n.pt")

#图片处理
@router.post("/storage/pictureUpload")
async def frames_detect(file: UploadFile = File(...)):
    """
    **description**
    接收图片并返回YOLOv8检测结果，包含 labels、confidence 和 count（仅限 car, bus, van）。

    **params**
    - image (UploadFile): 上传的图片文件。

    **returns**
    - JSON: 包含 labels、confidence 和 count 信息。
    """
    try:
        # 读取上传的图片
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = np.array(img)

        # 运行YOLOv8检测
        processedImg, detailedResult = detector.detect(img, 
                                                       addingBoxes=True, 
                                                       addingLabel=True, 
                                                       addingConf=False,
                                                       verbosity=2);

        # 保存处理后的图片
        timestamp = time.time_ns()
        file_name = f"processed_{timestamp}.jpg"
        file_path = os.path.join(SAVE_DIR, file_name)
        cv2.imwrite(file_path, cv2.cvtColor(processedImg, cv2.COLOR_RGB2BGR))

        # 构造返回的 URL
        watchURL = f"{URL}/api/watch/{file_name}"
        downloadURL = f"{URL}/api/download/{file_name}"

        # 提取所需的关键信息（已过滤）
        results_json = {
            "code": "200",
            "msg": "image process success",
            "data": {
                "watchURL": watchURL,
                "downloadURL": downloadURL,
                "labels": detailedResult["labels"],
                "confidence": detailedResult["confidence"],
                "count": detailedResult["count"]
            }
        }
        return JSONResponse(content=results_json, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"code": "500", "msg": f"image process failed: {str(e)}", "data": {}},
            status_code=500
        )

# **提供图片的在线查看功能**
@router.get("/watch/{filename}")
def watch_image(filename: str):
    file_path = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/jpeg")

# **提供图片的下载功能**
@router.get("/download/{filename}")
def download_image(filename: str):
    file_path = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename, media_type="image/jpeg")