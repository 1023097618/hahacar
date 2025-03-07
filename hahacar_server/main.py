from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.routing import Mount

from api.socket_manager import sio
from api.user import router as user_router
from api.photo_process import router as photo_router
from api.video_process import router as video_router
from api.camera_process import router as camera_router
import socketio

# 创建 ASGI 应用
socket_app = socketio.ASGIApp(sio)

app = FastAPI()


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST, PUT, DELETE等）
    allow_headers=["*"],  # 允许所有请求头
)


# 挂载 socket.io 到 /socket 或 /socket.io
app.mount("/socket.io", socket_app)

#注册路由
app.include_router(user_router)
app.include_router(photo_router)
app.include_router(video_router)
app.include_router(camera_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}