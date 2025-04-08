import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.camera_process import background_camera_task
from dependencies.database import get_db_session, SessionLocal
from services.camera_service import get_all_camera_ids
from services.camera_status_service import refresh_camera_status

tasks: dict[str, asyncio.Task] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行的逻辑
    db, close_db = get_db_session()
    try:
        camera_ids = get_all_camera_ids(db)  # 获取所有摄像头ID列表
        # 为每个摄像头创建独立的后台任务
        for camera_id in camera_ids:
            task = asyncio.create_task(background_camera_task(camera_id))
            tasks[camera_id] = task
    finally:
        close_db()

    # 2) 定义一个定时协程，用来周期性刷新 camera_status
    stop_refresh = False

    async def periodic_refresh():
        while not stop_refresh:
            # 每 60 秒执行一次
            await asyncio.sleep(60)

            # 在刷新前打开/关闭一个会话
            with SessionLocal() as dbsession:
                # 调用 refresh_camera_status：对比数据库最新状态与当前 camera_status
                refresh_camera_status(dbsession)

    # 启动周期任务
    task = asyncio.create_task(periodic_refresh())
    # 启动逻辑完成后，yield 让应用进入运行状态
    yield

    # 可在此添加关闭时的清理工作（如果需要）
    # 例如：关闭数据库连接、停止后台任务等
    # 应用关闭时
    stop_refresh = True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

#在摄像头
def cancel_task(camera_id:str):
    if tasks.get(camera_id) is not None:
        task = tasks.pop(camera_id, None)
        task.cancel()


#应当在摄像头url发生改变或者新加一个摄像头之后进行调用
def add_task(camera_id:str):
    cancel_task(camera_id)
    task = asyncio.create_task(background_camera_task(camera_id))
    tasks[camera_id] = task
