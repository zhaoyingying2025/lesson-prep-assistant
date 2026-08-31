"""备课助手 MVP - FastAPI 入口"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from .api.routes import router as api_router
from .config import settings
from .exporters.template_docx import generate_template_docx
from .storage.db import LessonTemplateORM, init_db, get_session


DEFAULT_TEMPLATE_STRUCTURE = {
    "tables": [
        {"type": "title-table", "fields": ["course_name", "chapter", "total_minutes"], "label": "教案标题"},
        {"type": "info-table", "fields": ["teaching_object", "teacher_name", "class_hours"], "label": "基本信息"},
        {"type": "goal-table", "fields": ["knowledge_goal", "ability_goal", "value_goal"], "label": "教学目标"},
        {"type": "keypoint-table", "fields": ["key_points", "difficult_points", "difficult_strategy"], "label": "教学重难点"},
        {"type": "source-table", "fields": ["knowledge_sources"], "label": "知识点出处"},
        {"type": "stage-table", "fields": ["stages"], "label": "教学过程（六阶段）"},
        {"type": "board-table", "fields": ["board_design"], "label": "板书设计"},
        {"type": "homework-table", "fields": ["homework"], "label": "课后作业"},
        {"type": "reflection-table", "fields": ["reflection"], "label": "教学反思"},
    ],
    "defaults": {
        "course_name": "",
        "chapter": "",
        "total_minutes": 90,
        "teaching_object": "",
        "teacher_name": "",
        "class_hours": "2课时",
        "knowledge_goal": "",
        "ability_goal": "",
        "value_goal": "",
        "key_points": [],
        "difficult_points": [],
        "difficult_strategy": "",
        "knowledge_sources": [],
        "stages": [
            {"name": "课程导入", "duration_min": 9, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
            {"name": "新知讲授", "duration_min": 27, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
            {"name": "互动研讨", "duration_min": 14, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
            {"name": "典型例题", "duration_min": 18, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
            {"name": "归纳小结", "duration_min": 9, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
            {"name": "作业布置", "duration_min": 13, "teacher_activity": "", "student_activity": "", "design_intent": "", "content": ""},
        ],
        "board_design": "",
        "homework": [],
        "reflection": "（课后填写）",
        "source_material_ids": [],
    },
}


async def seed_default_templates() -> None:
    """启动时 seed 默认教案模板（如果不存在），同时生成默认 .docx 文件到静态目录"""
    async for session in get_session():
        # 先清理：确保只有全局模板 (course_id=None) 可标记为 is_default=True
        # 课程私有模板不可占用默认标记
        non_global_defaults = await session.execute(
            select(LessonTemplateORM).where(
                LessonTemplateORM.is_default == True,
                LessonTemplateORM.course_id.isnot(None),
            )
        )
        for tpl in non_global_defaults.scalars().all():
            tpl.is_default = False

        # 查找全局默认模板
        result = await session.execute(
            select(LessonTemplateORM).where(
                LessonTemplateORM.is_default == True,
                LessonTemplateORM.course_id.is_(None),
            )
        )
        existing_default = result.scalars().first()
        if existing_default:
            if existing_default.structure_json != DEFAULT_TEMPLATE_STRUCTURE:
                existing_default.structure_json = DEFAULT_TEMPLATE_STRUCTURE
                await session.commit()
        else:
            # 查找全局模板修复标记或创建新模板
            result2 = await session.execute(
                select(LessonTemplateORM).where(LessonTemplateORM.course_id.is_(None))
            )
            global_tpl = result2.scalars().first()
            if global_tpl:
                global_tpl.is_default = True
                global_tpl.structure_json = DEFAULT_TEMPLATE_STRUCTURE
                await session.commit()
            else:
                default = LessonTemplateORM(
                    course_id=None,
                    name="默认全表格教案模板",
                    description="内置青绿风全表格模板，对应《LessonPlan》标准结构含8大模块+知识点出处",
                    structure_json=DEFAULT_TEMPLATE_STRUCTURE,
                    is_default=True,
                )
                session.add(default)
                await session.commit()

    # 每次启动都生成/更新默认 .docx 文件到静态目录，方便用户直接下载
    try:
        docx_bytes = generate_template_docx(DEFAULT_TEMPLATE_STRUCTURE, "默认教案模板")
        static_dir = Path(__file__).resolve().parent / "static"
        static_dir.mkdir(exist_ok=True)
        default_docx_path = static_dir / "default_template.docx"
        default_docx_path.write_bytes(docx_bytes)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库 + seed 默认模板"""
    await init_db()
    try:
        await seed_default_templates()
    except Exception:
        pass  # seed失败不影响主流程
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
        request,
        "index.html",
        {
            "app_title": "备课助手 · 智能备课伴侣",
            "model": settings.llm_model,
        },
    )


@app.get("/mobile", response_class=HTMLResponse)
async def mobile_page(request: Request):
    """移动端独立 H5 页面"""
    return templates.TemplateResponse(
        request,
        "mobile.html",
        {
            "app_title": "备课助手",
            "model": settings.llm_model,
        },
    )


@app.get("/sw.js")
async def service_worker():
    """Serve service worker from root scope"""
    sw_path = STATIC_DIR / "sw.js"
    return Response(sw_path.read_text(encoding="utf-8"), media_type="application/javascript")


@app.get("/favicon.ico")
async def favicon():
    return Response("", media_type="image/x-icon")
