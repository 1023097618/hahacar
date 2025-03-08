# socket_manager.py
import socketio

# 创建 Socket.IO 实例
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True
)