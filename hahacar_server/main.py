import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from api.socket_manager import sio
from api.user import router as user_router
from api.photo_process import router as photo_router
from api.video_process import router as video_router
from api.camera_process import router as camera_process_router, generate_frames, background_camera_task
from api.camera import router as camera_router
from api.camera_rule import router as camera_rule_router
from api.camera_detect_info import router as camera_detect_info
from api.alert import router as alert
from api.camera_line import router as camera_line
from api.label import router as label

from dependencies.database import get_db
from services.camera_service import get_all_camera_ids

# 定义 lifespan 上下文管理器，用于应用启动和关闭的逻辑
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行的逻辑
    db = next(get_db())
    camera_ids = get_all_camera_ids(db)  # 获取所有摄像头ID列表
    # 为每个摄像头创建独立的后台任务
    for camera_id in camera_ids:
        asyncio.create_task(background_camera_task(camera_id))
    
    # 启动逻辑完成后，yield 让应用进入运行状态
    yield
    
    # 可在此添加关闭时的清理工作（如果需要）
    # 例如：关闭数据库连接、停止后台任务等

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
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=False)
