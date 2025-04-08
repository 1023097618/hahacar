import os
import os

import socketio
import uvicorn;
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.alert import router as alert
from api.camera import router as camera_router
from api.camera_detect_info import router as camera_detect_info
from api.camera_line import router as camera_line
from api.camera_process import router as camera_process_router
from api.camera_rule import router as camera_rule_router
from api.label import router as label
from api.photo_process import router as photo_router
from api.socket_manager import sio
from api.user import router as user_router
from api.video_process import router as video_router
from lifespan_manager import lifespan

# logging.getLogger("sqlalchemy").setLevel(logging.ERROR);

# 定义 lifespan 上下文管理器，用于应用启动和关闭的逻辑


# 挂载 socket.io 到 ASGI 应用
socket_app = socketio.ASGIApp(sio)

# 使用 lifespan 参数初始化 FastAPI 应用
app = FastAPI(lifespan=lifespan)
# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

# 获取当前工作目录，并构造保存路径，当前目录/alerts/on
base_dir = os.getcwd()
save_dir = os.path.join(base_dir, "alerts", "on")
# os.makedirs(save_dir, exist_ok=True)  # 确保目录存在

# 将本地的 save_dir 映射为 URL 路径 /static/alerts/on
app.mount("/api/fetchImage", StaticFiles(directory=save_dir), name="alerts_on")

# 挂载 socket.io 路由
app.mount("/socket.io", socket_app)

# 注册各个路由
app.include_router(user_router)
app.include_router(photo_router)
app.include_router(video_router)
app.include_router(camera_router)
app.include_router(camera_process_router)
app.include_router(camera_rule_router)
app.include_router(camera_detect_info)
app.include_router(camera_line)
app.include_router(alert)
app.include_router(label)

# 根路由
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=False);
