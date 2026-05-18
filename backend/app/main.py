import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.database import engine, Base
from app.models import models  # noqa: F401 - 必须在create_all之前导入所有模型

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI测试平台",
    description="自然语言 → LLM生成Playwright代码 → 执行 → 返回结果",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.routers import suites, test_cases, executions, documents, model_configs, generation, generate_cases, functions

app.include_router(suites.router)
app.include_router(test_cases.router)
app.include_router(executions.router)
app.include_router(documents.router)
app.include_router(model_configs.router)
app.include_router(generation.router)
app.include_router(generate_cases.router)
app.include_router(functions.router)

# 挂载截图和上传文件目录
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "screenshots")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.on_event("startup")
def cleanup_zombie_executions():
    """启动时清理卡在 running 状态的僵尸任务（如上次服务崩溃残留）"""
    from app.models.database import SessionLocal
    from app.models.models import TestExecution
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        zombies = db.query(TestExecution).filter(TestExecution.status == "running").all()
        for z in zombies:
            z.status = "error"
            z.error_message = "服务重启，自动标记为超时终止"
            z.end_time = datetime.now(timezone.utc)
        if zombies:
            db.commit()
            print(f"[启动清理] 标记 {len(zombies)} 个僵尸任务为 error")
    finally:
        db.close()
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
