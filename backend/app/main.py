"""备课助手 MVP - FastAPI 入口"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api.routes import router as api_router
from .config import settings
from .storage.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    yield


app = FastAPI(
    title="备课助手智能体 MVP",
    description="面向高校/高职教师的AI备课伴侣",
    version="0.1.0",
    lifespan=lifespan,
)

# 静态资源
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API路由
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面 - 对话驱动型UI"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_title": "备课助手 · 智能备课伴侣",
            "model": settings.llm_model,
        },
    )


@app.get("/favicon.ico")
async def favicon():
    return Response("", media_type="image/x-icon")
