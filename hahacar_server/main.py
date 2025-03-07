from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.user import router as user_router
from api.model import router as model_router

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST, PUT, DELETE等）
    allow_headers=["*"],  # 允许所有请求头
)

#注册路由
app.include_router(user_router)
app.include_router(model_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
