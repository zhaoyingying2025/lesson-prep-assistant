"""API 路由汇总（MVP简化版，所有路由聚合便于维护）"""
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.chat_agent import modify_lesson
from ..agents.knowledge_agent import extract_knowledge
from ..agents.lesson_agent import generate_lesson
from ..agents.ppt_agent import generate_ppt_content
from ..agents.smart_extract_agent import smart_extract
from ..core.llm import (
    LLMError,
    PRESET_PROVIDERS,
    get_llm,
    get_llm_config,
    reset_llm,
)
from ..core.parser import ParseError, detect_material_type, make_preview, parse_file
from ..core.textbook_cache import index_material, search_textbook, get_knowledge_point_context
from ..exporters.docx_export import export_docx
from ..exporters.markdown import export_markdown
from ..exporters.pptx_export import export_teaching_pptx
from ..models.schemas import (
    ApiResponse,
    ChatRequest,
    CourseCreate,
    LessonParams,
    LessonPlan,
    LLMSettingsUpdate,
)
from ..storage.db import (
    ChatMessageORM,
    ChapterORM,
    CourseORM,
    KnowledgePointORM,
    LessonORM,
    MaterialORM,
    PptRecordORM,
    get_session,
)
from ..storage.file_store import save_upload

router = APIRouter(prefix="/api")


# ============================================================
# 课程管理
# ============================================================
@router.get("/courses")
async def list_courses():
    async for session in get_session():
        result = await session.execute(select(CourseORM).order_by(CourseORM.created_at.desc()))
        courses = result.scalars().all()
        return ApiResponse(
            data=[
                {
                    "id": c.id,
                    "name": c.name,
                    "major": c.major,
                    "description": c.description,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in courses
            ]
        )


@router.post("/courses")
async def create_course(payload: CourseCreate):
    async for session in get_session():
        course = CourseORM(
            name=payload.name,
            major=payload.major,
            description=payload.description,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return ApiResponse(
            message="课程创建成功",
            data={
                "id": course.id,
                "name": course.name,
                "major": course.major,
                "description": course.description,
                "created_at": course.created_at.isoformat() if course.created_at else None,
            },
        )


@router.get("/courses/{course_id}")
async def get_course(course_id: int):
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")
        return ApiResponse(
            data={
                "id": course.id,
                "name": course.name,
                "major": course.major,
                "description": course.description,
                "created_at": course.created_at.isoformat() if course.created_at else None,
            }
        )


@router.delete("/courses/{course_id}")
async def delete_course(course_id: int):
    async for session in get_session():
        course = await session.get(
            CourseORM,
            course_id,
            options=[
                selectinload(CourseORM.materials),
                selectinload(CourseORM.ppt_records),
            ],
        )
        if not course:
            raise HTTPException(404, "课程不存在")

        # 1. 先删除上传的文件（教材、PPT存储文件）
        from ..config import settings
        base_dir = Path(settings.upload_dir) if settings.upload_dir else Path(__file__).resolve().parent.parent.parent / "uploads"

        for mat in course.materials or []:
            if mat.stored_path:
                p = Path(mat.stored_path)
                # 仅删除 uploads 目录下的文件，避免误删
                try:
                    if p.exists() and base_dir in p.resolve().parents:
                        p.unlink()
                except Exception:
                    pass

        for ppt in course.ppt_records or []:
            if ppt.stored_path:
                p = Path(ppt.stored_path)
                try:
                    if p.exists() and base_dir in p.resolve().parents:
                        p.unlink()
                except Exception:
                    pass

        # 2. 使用 SQLAlchemy 级联删除
        await session.delete(course)
        await session.commit()
        return ApiResponse(message="课程已删除")


@router.put("/courses/{course_id}")
async def update_course(course_id: int, payload: dict):
    """更新课程信息（名称/专业/描述）"""
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")
        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                raise HTTPException(400, "课程名称不能为空")
            course.name = name
        if "major" in payload:
            course.major = (payload.get("major") or "").strip() or None
        if "description" in payload:
            course.description = (payload.get("description") or "").strip() or None
        await session.commit()
        await session.refresh(course)
        return ApiResponse(
            message="课程已更新",
            data={
                "id": course.id,
                "name": course.name,
                "major": course.major,
                "description": course.description,
                "created_at": course.created_at.isoformat() if course.created_at else None,
            },
        )


# ============================================================
# 章节树（章/节/子节，多级嵌套）
# ============================================================
def _chapter_to_dict(ch: ChapterORM, include_children: bool = True) -> dict:
    """递归序列化章节树"""
    d = {
        "id": ch.id,
        "course_id": ch.course_id,
        "parent_id": ch.parent_id,
        "name": ch.name,
        "sort_order": ch.sort_order,
    }
    if include_children:
        d["children"] = [_chapter_to_dict(c) for c in (ch.children or [])]
    return d


@router.get("/courses/{course_id}/chapters")
async def list_chapters(course_id: int):
    """获取课程的章节树（递归嵌套）"""
    async for session in get_session():
        # 一次查出该课程的所有章节，在 Python 中构建树（避免异步 lazy load 问题）
        result = await session.execute(
            select(ChapterORM)
            .where(ChapterORM.course_id == course_id)
            .order_by(ChapterORM.sort_order)
        )
        all_chapters = result.scalars().all()

        # 构建 id -> node 字典
        node_map = {}
        for ch in all_chapters:
            node_map[ch.id] = {
                "id": ch.id,
                "course_id": ch.course_id,
                "parent_id": ch.parent_id,
                "name": ch.name,
                "sort_order": ch.sort_order,
                "children": [],
            }

        # 构建树（收集根节点）
        roots = []
        for ch in all_chapters:
            node = node_map[ch.id]
            if ch.parent_id is None:
                roots.append(node)
            else:
                parent = node_map.get(ch.parent_id)
                if parent:
                    parent["children"].append(node)
                else:
                    # 父节点不存在，作为根节点
                    roots.append(node)

        return ApiResponse(data=roots)


@router.post("/courses/{course_id}/chapters")
async def create_chapter(course_id: int, payload: dict):
    """新建章节（parent_id 为 null 表示顶级章，否则为子节）"""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "章节名称不能为空")
    parent_id = payload.get("parent_id")

    async for session in get_session():
        # 校验课程存在
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")
        # 校验父节点
        if parent_id is not None:
            parent = await session.get(ChapterORM, parent_id)
            if not parent or parent.course_id != course_id:
                raise HTTPException(400, "父节点不存在或不属于本课程")

        # 计算 sort_order：同级末尾
        if parent_id is not None:
            result = await session.execute(
                select(func.max(ChapterORM.sort_order))
                .where(ChapterORM.parent_id == parent_id)
            )
        else:
            result = await session.execute(
                select(func.max(ChapterORM.sort_order))
                .where(ChapterORM.course_id == course_id, ChapterORM.parent_id.is_(None))
            )
        max_order = result.scalar() or 0

        chapter = ChapterORM(
            course_id=course_id,
            parent_id=parent_id,
            name=name,
            sort_order=max_order + 1,
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)
        # 直接构造 dict，避免访问 relationship 触发异步 lazy load
        return ApiResponse(data={
            "id": chapter.id,
            "course_id": chapter.course_id,
            "parent_id": chapter.parent_id,
            "name": chapter.name,
            "sort_order": chapter.sort_order,
            "children": [],
        }, message="章节已创建")


@router.put("/chapters/{chapter_id}")
async def rename_chapter(chapter_id: int, payload: dict):
    """重命名章节"""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "章节名称不能为空")

    async for session in get_session():
        chapter = await session.get(ChapterORM, chapter_id)
        if not chapter:
            raise HTTPException(404, "章节不存在")
        chapter.name = name
        await session.commit()
        await session.refresh(chapter)
        return ApiResponse(data={
            "id": chapter.id,
            "course_id": chapter.course_id,
            "parent_id": chapter.parent_id,
            "name": chapter.name,
            "sort_order": chapter.sort_order,
            "children": [],
        }, message="已重命名")


@router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: int):
    """删除章节（级联删除子节点；关联教案 chapter_id 置空，保留教案）"""
    async for session in get_session():
        chapter = await session.get(ChapterORM, chapter_id)
        if not chapter:
            raise HTTPException(404, "章节不存在")
        await session.delete(chapter)
        await session.commit()
        return ApiResponse(message="章节已删除")


# ============================================================
# 教材资源
# ============================================================
@router.post("/courses/{course_id}/materials")
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    material_type: Optional[str] = Form(None),
):
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 读取文件
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(400, "文件为空")

        # 保存文件
        stored_path = await save_upload(file_bytes, file.filename or "unnamed", course_id)

        # 解析文件
        try:
            content_text = parse_file(Path(stored_path))
        except ParseError as e:
            # 解析失败也要保存记录，但内容为空
            content_text = ""
            parse_error = str(e)
        else:
            parse_error = None

        # 类型检测
        detected_type = material_type or detect_material_type(file.filename or "", content_text)

        # 入库
        material = MaterialORM(
            course_id=course_id,
            filename=file.filename or "unnamed",
            stored_path=str(stored_path),
            material_type=detected_type,
            file_size=len(file_bytes),
            content_text=content_text,
            content_preview=make_preview(content_text),
            char_count=len(content_text),
        )
        session.add(material)
        await session.commit()
        await session.refresh(material)

        # 自动索引到教材缓存（按页分割，便于后续检索）
        if content_text:
            try:
                indexed_pages = await index_material(
                    session, material.id, course_id, Path(stored_path)
                )
            except Exception:
                indexed_pages = 0
        else:
            indexed_pages = 0

        return ApiResponse(
            message="文件上传成功" + ("（部分内容解析失败）" if parse_error else ""),
            data={
                "id": material.id,
                "course_id": material.course_id,
                "filename": material.filename,
                "material_type": material.material_type,
                "file_size": material.file_size,
                "char_count": material.char_count,
                "content_preview": material.content_preview,
                "indexed_pages": indexed_pages,
                "parse_error": parse_error,
                "created_at": material.created_at.isoformat() if material.created_at else None,
            },
        )


@router.get("/courses/{course_id}/materials")
async def list_materials(course_id: int):
    async for session in get_session():
        result = await session.execute(
            select(MaterialORM)
            .where(MaterialORM.course_id == course_id)
            .order_by(MaterialORM.created_at.desc())
        )
        materials = result.scalars().all()
        return ApiResponse(
            data=[
                {
                    "id": m.id,
                    "course_id": m.course_id,
                    "filename": m.filename,
                    "material_type": m.material_type,
                    "file_size": m.file_size,
                    "char_count": m.char_count,
                    "content_preview": m.content_preview,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in materials
            ]
        )


@router.get("/materials/{material_id}")
async def get_material(material_id: int):
    async for session in get_session():
        m = await session.get(MaterialORM, material_id)
        if not m:
            raise HTTPException(404, "材料不存在")
        return ApiResponse(
            data={
                "id": m.id,
                "course_id": m.course_id,
                "filename": m.filename,
                "material_type": m.material_type,
                "file_size": m.file_size,
                "char_count": m.char_count,
                "content_text": m.content_text,
                "content_preview": m.content_preview,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
        )


@router.delete("/materials/{material_id}")
async def delete_material(material_id: int):
    async for session in get_session():
        m = await session.get(MaterialORM, material_id)
        if not m:
            raise HTTPException(404, "材料不存在")
        # 删除文件
        try:
            Path(m.stored_path).unlink(missing_ok=True)
        except Exception:
            pass
        await session.delete(m)
        await session.commit()
        return ApiResponse(message="材料已删除")


# ============================================================
# 知识点提取
# ============================================================
@router.post("/courses/{course_id}/extract-knowledge")
async def extract_knowledge_api(
    course_id: int,
    chapter: str = Form(...),
    material_ids: Optional[str] = Form(None),  # 逗号分隔的ID
):
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 获取材料
        if material_ids:
            ids = [int(x) for x in material_ids.split(",") if x.strip()]
        else:
            result = await session.execute(
                select(MaterialORM).where(MaterialORM.course_id == course_id)
            )
            ids = [m.id for m in result.scalars().all()]

        if not ids:
            raise HTTPException(400, "请先上传教材资源")

        # 拼接材料文本
        texts: list[str] = []
        for mid in ids:
            m = await session.get(MaterialORM, mid)
            if m and m.content_text:
                texts.append(f"### 来源：{m.filename}\n{m.content_text}")

        combined = "\n\n".join(texts)
        if not combined.strip():
            raise HTTPException(400, "教材内容为空，请上传可解析的文件")

        try:
            result = await extract_knowledge(course.name, chapter, combined)
        except LLMError as e:
            raise HTTPException(502, str(e))

        # 持久化知识点（先删除该章节旧知识点，再写入新的）
        # 通过 chapter 名匹配（兼容无 chapter_id 的场景）
        old_kps = (await session.execute(
            select(KnowledgePointORM).where(
                KnowledgePointORM.course_id == course_id,
                KnowledgePointORM.chapter == chapter,
            )
        )).scalars().all()
        for old_kp in old_kps:
            await session.delete(old_kp)

        # 写入新知识点
        saved_points = []
        for idx, p in enumerate(result.points, 1):
            kp = KnowledgePointORM(
                course_id=course_id,
                chapter=chapter,
                name=p.name,
                definition=p.definition or "",
                source_pages=p.source_pages or "",
                layer=p.layer if p.layer in ("basic", "core", "extension") else "basic",
                is_key_point=1 if p.is_key_point else 0,
                is_difficult=1 if p.is_difficult else 0,
                is_exam_point=1 if p.is_exam_point else 0,
                sort_order=idx,
            )
            session.add(kp)
            saved_points.append(kp)
        await session.commit()
        for kp in saved_points:
            await session.refresh(kp)

        # 构造返回数据（带 id）
        points_with_id = [
            {
                "id": kp.id,
                "name": kp.name,
                "definition": kp.definition,
                "source_pages": kp.source_pages or "",
                "layer": kp.layer,
                "is_key_point": bool(kp.is_key_point),
                "is_difficult": bool(kp.is_difficult),
                "is_exam_point": bool(kp.is_exam_point),
                "sort_order": kp.sort_order,
            }
            for kp in saved_points
        ]

        return ApiResponse(
            message=f"已提取 {len(points_with_id)} 个知识点",
            data={"points": points_with_id, "summary": result.summary},
        )


# ============================================================
# 智能章节提取（一键知识点提取）
# ============================================================
@router.post("/courses/{course_id}/smart-extract")
async def smart_extract_api(course_id: int):
    """从教材全文自动识别章节结构并提取知识点"""
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 获取所有教材
        result = await session.execute(
            select(MaterialORM).where(MaterialORM.course_id == course_id)
        )
        materials = result.scalars().all()
        if not materials:
            raise HTTPException(400, "请先上传教材资源")

        # 拼接材料文本
        texts: list[str] = []
        filenames: list[str] = []
        for m in materials:
            if m.content_text:
                texts.append(f"### 来源：{m.filename}\n{m.content_text}")
                filenames.append(m.filename)

        combined = "\n\n".join(texts)
        if not combined.strip():
            raise HTTPException(400, "教材内容为空")

        try:
            chapter_tree = await smart_extract(
                course.name,
                ", ".join(filenames),
                combined,
            )
        except LLMError as e:
            raise HTTPException(502, str(e))

        if not chapter_tree:
            raise HTTPException(500, "未能识别出章节结构，请检查教材内容")

        # 递归创建章节和知识点
        created_chapters = []

        async def _create_node(
            parent_id: int | None,
            sort_order: int,
            node: dict,
        ) -> dict:
            ch = ChapterORM(
                course_id=course_id,
                parent_id=parent_id,
                name=node["name"],
                sort_order=sort_order,
            )
            session.add(ch)
            await session.flush()
            await session.refresh(ch)

            node_kps = node.get("knowledge_points") or []
            saved_kps = []
            for kp_idx, kp in enumerate(node_kps, 1):
                kp_obj = KnowledgePointORM(
                    course_id=course_id,
                    chapter=node["name"],
                    chapter_id=ch.id,
                    name=kp["name"],
                    definition=kp.get("definition", ""),
                    source_pages=kp.get("source_pages", ""),
                    layer=kp.get("layer", "core"),
                    is_key_point=1 if kp.get("is_key_point") else 0,
                    is_difficult=1 if kp.get("is_difficult") else 0,
                    is_exam_point=1 if kp.get("is_exam_point") else 0,
                    sort_order=kp_idx,
                )
                session.add(kp_obj)
                saved_kps.append(kp_obj)

            children = []
            for child_idx, child in enumerate(node.get("children") or []):
                child_result = await _create_node(ch.id, child_idx + 1, child)
                children.append(child_result)

            await session.flush()
            for kp in saved_kps:
                await session.refresh(kp)

            return {
                "id": ch.id,
                "name": ch.name,
                "children": children,
                "knowledge_points": [
                    {
                        "id": kp.id,
                        "name": kp.name,
                        "definition": kp.definition,
                        "source_pages": kp.source_pages or "",
                        "layer": kp.layer,
                        "is_key_point": bool(kp.is_key_point),
                        "is_difficult": bool(kp.is_difficult),
                        "is_exam_point": bool(kp.is_exam_point),
                    }
                    for kp in saved_kps
                ],
            }

        for idx, ch_node in enumerate(chapter_tree):
            created = await _create_node(None, idx + 1, ch_node)
            created_chapters.append(created)

        await session.commit()

        # 统计知识点总数
        all_kp_count = 0
        def _count_kp(nodes):
            nonlocal all_kp_count
            for n in nodes:
                all_kp_count += len(n.get("knowledge_points", []))
                _count_kp(n.get("children", []))
        _count_kp(created_chapters)

        return ApiResponse(
            message=f"智能提取完成，已创建 {len(created_chapters)} 个章节，提取 {all_kp_count} 个知识点",
            data={
                "chapters": created_chapters,
                "total_kp": all_kp_count,
            },
        )


# ============================================================
# 知识点 CRUD（手动编辑/增删/标签切换）
# ============================================================
def _kp_to_dict(kp: KnowledgePointORM) -> dict:
    return {
        "id": kp.id,
        "course_id": kp.course_id,
        "chapter_id": kp.chapter_id,
        "chapter": kp.chapter,
        "name": kp.name,
        "definition": kp.definition,
        "source_pages": kp.source_pages or "",
        "layer": kp.layer,
        "is_key_point": bool(kp.is_key_point),
        "is_difficult": bool(kp.is_difficult),
        "is_exam_point": bool(kp.is_exam_point),
        "sort_order": kp.sort_order,
    }


async def _build_textbook_context(
    session: AsyncSession,
    course_id: int,
    knowledge_points: list[dict],
) -> str:
    """检索多个知识点在教材中的原文上下文"""
    parts = []
    for kp in knowledge_points:
        kp_name = kp.get("name", "").strip()
        if not kp_name:
            continue
        try:
            ctx = await get_knowledge_point_context(session, course_id, kp_name)
        except Exception:
            continue
        if not ctx:
            continue
        context_text = ctx["context"]
        if len(context_text) > 1500:
            context_text = context_text[:1500] + "..."
        parts.append(f"知识点「{kp_name}」（教材第{ctx['page_number']}页附近）：\n{context_text}")
    return "\n\n---\n\n".join(parts)


@router.get("/courses/{course_id}/knowledge-points")
async def list_knowledge_points(course_id: int, chapter: Optional[str] = None, chapter_id: Optional[int] = None):
    """列出课程（或某章节）的知识点，支持按 chapter 名称或 chapter_id 筛选"""
    async for session in get_session():
        stmt = select(KnowledgePointORM).where(KnowledgePointORM.course_id == course_id)
        if chapter:
            stmt = stmt.where(KnowledgePointORM.chapter == chapter)
        if chapter_id is not None:
            stmt = stmt.where(KnowledgePointORM.chapter_id == chapter_id)
        stmt = stmt.order_by(KnowledgePointORM.sort_order)
        result = await session.execute(stmt)
        kps = result.scalars().all()
        return ApiResponse(data=[_kp_to_dict(k) for k in kps])


@router.post("/courses/{course_id}/knowledge-points")
async def create_knowledge_point(course_id: int, payload: dict):
    """手动新增知识点"""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "知识点名称不能为空")
    chapter = (payload.get("chapter") or "").strip()

    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")
        # 计算 sort_order
        max_order = (await session.execute(
            select(func.max(KnowledgePointORM.sort_order))
            .where(KnowledgePointORM.course_id == course_id, KnowledgePointORM.chapter == chapter)
        )).scalar() or 0
        kp = KnowledgePointORM(
            course_id=course_id,
            chapter=chapter,
            chapter_id=payload.get("chapter_id"),
            name=name,
            definition=(payload.get("definition") or "").strip(),
            source_pages=(payload.get("source_pages") or "").strip(),
            layer=payload.get("layer") if payload.get("layer") in ("basic", "core", "extension") else "basic",
            is_key_point=1 if payload.get("is_key_point") else 0,
            is_difficult=1 if payload.get("is_difficult") else 0,
            is_exam_point=1 if payload.get("is_exam_point") else 0,
            sort_order=max_order + 1,
        )
        session.add(kp)
        await session.commit()
        await session.refresh(kp)
        return ApiResponse(data=_kp_to_dict(kp), message="知识点已新增")


@router.put("/knowledge-points/{kp_id}")
async def update_knowledge_point(kp_id: int, payload: dict):
    """更新知识点（名称/定义/层级/标签）"""
    async for session in get_session():
        kp = await session.get(KnowledgePointORM, kp_id)
        if not kp:
            raise HTTPException(404, "知识点不存在")
        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                raise HTTPException(400, "知识点名称不能为空")
            kp.name = name
        if "definition" in payload:
            kp.definition = (payload.get("definition") or "").strip()
        if "source_pages" in payload:
            kp.source_pages = (payload.get("source_pages") or "").strip()
        if "layer" in payload:
            kp.layer = payload.get("layer") if payload.get("layer") in ("basic", "core", "extension") else "basic"
        if "is_key_point" in payload:
            kp.is_key_point = 1 if payload.get("is_key_point") else 0
        if "is_difficult" in payload:
            kp.is_difficult = 1 if payload.get("is_difficult") else 0
        if "is_exam_point" in payload:
            kp.is_exam_point = 1 if payload.get("is_exam_point") else 0
        await session.commit()
        await session.refresh(kp)
        return ApiResponse(data=_kp_to_dict(kp), message="知识点已更新")


@router.delete("/knowledge-points/{kp_id}")
async def delete_knowledge_point(kp_id: int):
    """删除知识点"""
    async for session in get_session():
        kp = await session.get(KnowledgePointORM, kp_id)
        if not kp:
            raise HTTPException(404, "知识点不存在")
        await session.delete(kp)
        await session.commit()
        return ApiResponse(message="知识点已删除")


# ============================================================
# 思维导图生成
# ============================================================
@router.post("/courses/{course_id}/mindmap")
async def generate_mindmap(course_id: int, payload: dict):
    """根据知识点生成思维导图数据（markmap 格式）"""
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 获取知识点：优先使用请求传入的，否则从数据库取
        points_input = payload.get("knowledge_points")
        if points_input and isinstance(points_input, list):
            kps = points_input
        else:
            chapter = payload.get("chapter", "")
            stmt = select(KnowledgePointORM).where(KnowledgePointORM.course_id == course_id)
            if chapter:
                stmt = stmt.where(KnowledgePointORM.chapter == chapter)
            stmt = stmt.order_by(KnowledgePointORM.sort_order)
            result = await session.execute(stmt)
            kps = result.scalars().all()
            kps = [
                {
                    "name": k.name,
                    "definition": k.definition,
                    "layer": k.layer,
                    "is_key_point": bool(k.is_key_point),
                    "is_difficult": bool(k.is_difficult),
                    "is_exam_point": bool(k.is_exam_point),
                }
                for k in kps
            ]

        if not kps:
            raise HTTPException(400, "暂无知识点，请先提取知识点")

        # 按层级分组
        layers = {"basic": [], "core": [], "extension": []}
        for p in kps:
            layer = p.get("layer", "basic")
            if layer not in layers:
                layer = "basic"
            layers[layer].append(p)

        layer_labels = {"basic": "基础层", "core": "核心层", "extension": "拓展层"}
        layer_icons = {"basic": "📘", "core": "📗", "extension": "📕"}

        # 生成 markmap 兼容的 markdown
        lines = [f"# {course.name}"]
        chapter_name = payload.get("chapter", kps[0].get("chapter", "")) if kps else ""
        if chapter_name:
            lines[0] = f"# {course.name} — {chapter_name}"

        for layer_key in ("basic", "core", "extension"):
            items = layers[layer_key]
            if not items:
                continue
            lines.append(f"## {layer_icons[layer_key]} {layer_labels[layer_key]} ({len(items)}个)")
            for p in items:
                name = p.get("name", "")
                definition = p.get("definition", "")
                tags = []
                if p.get("is_key_point"):
                    tags.append("重点")
                if p.get("is_difficult"):
                    tags.append("难点")
                if p.get("is_exam_point"):
                    tags.append("考点")
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                desc = f"：{definition[:80]}" if definition else ""
                lines.append(f"### {name}{tag_str}{desc}")

        markdown = "\n".join(lines)

        return ApiResponse(
            message="思维导图生成成功",
            data={
                "markdown": markdown,
                "count": len(kps),
            },
        )


# ============================================================
# 教案生成
# ============================================================
@router.post("/courses/{course_id}/generate-lesson")
async def generate_lesson_api(
    course_id: int,
    chapter: str = Form(...),
    knowledge_points: str = Form(...),  # JSON字符串
    params: Optional[str] = Form(None),  # JSON字符串，可选
    chapter_id: Optional[int] = Form(None),  # 关联章节树节点
):
    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 解析知识点
        try:
            kp_list = json.loads(knowledge_points)
            if not isinstance(kp_list, list):
                raise ValueError
        except Exception:
            raise HTTPException(400, "knowledge_points 必须是JSON数组")

        # 解析参数
        try:
            params_dict = json.loads(params) if params else {}
            lesson_params = LessonParams(**params_dict)
        except Exception as e:
            raise HTTPException(400, f"参数解析失败: {e}")

        # 检索教材原文作为上下文
        textbook_context_parts = []
        for kp in kp_list:
            kp_name = kp.get("name", "").strip()
            if kp_name:
                ctx = await get_knowledge_point_context(session, course_id, kp_name)
                if ctx:
                    # 只保留关键段落，避免超出 token 限制
                    context_text = ctx["context"]
                    if len(context_text) > 1500:
                        context_text = context_text[:1500] + "..."
                    textbook_context_parts.append(
                        f"知识点「{kp_name}」（教材第{ctx['page_number']}页附近）：\n{context_text}"
                    )
        textbook_context = "\n\n---\n\n".join(textbook_context_parts)

        # 生成教案
        try:
            plan = await generate_lesson(
                course.name, chapter, kp_list, lesson_params,
                textbook_context=textbook_context,
            )
        except LLMError as e:
            raise HTTPException(502, str(e))

        # 入库
        lesson = LessonORM(
            course_id=course_id,
            chapter_id=chapter_id,
            chapter=chapter,
            title=f"{course.name} - {chapter}",
            plan_json=plan.model_dump(),
            params_json=lesson_params.model_dump(),
        )
        session.add(lesson)
        await session.commit()
        await session.refresh(lesson)

        return ApiResponse(
            message="教案生成成功",
            data={
                "id": lesson.id,
                "course_id": lesson.course_id,
                "chapter": lesson.chapter,
                "title": lesson.title,
                "plan": plan.model_dump(),
                "params": lesson_params.model_dump(),
                "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
                "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
            },
        )


# ============================================================
# 教案管理
# ============================================================
@router.get("/courses/{course_id}/lessons")
async def list_lessons(course_id: int):
    async for session in get_session():
        result = await session.execute(
            select(LessonORM)
            .where(LessonORM.course_id == course_id)
            .order_by(LessonORM.updated_at.desc())
        )
        lessons = result.scalars().all()
        return ApiResponse(
            data=[
                {
                    "id": l.id,
                    "course_id": l.course_id,
                    "chapter": l.chapter,
                    "title": l.title,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                    "updated_at": l.updated_at.isoformat() if l.updated_at else None,
                }
                for l in lessons
            ]
        )


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: int):
    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")
        return ApiResponse(
            data={
                "id": lesson.id,
                "course_id": lesson.course_id,
                "chapter": lesson.chapter,
                "title": lesson.title,
                "plan": lesson.plan_json,
                "params": lesson.params_json,
                "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
                "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
            }
        )


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, plan: dict):
    """直接更新教案（用于编辑器修改后保存）"""
    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")
        lesson.plan_json = plan
        lesson.updated_at = datetime.utcnow()
        await session.commit()
        return ApiResponse(message="教案已保存")


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int):
    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")
        await session.delete(lesson)
        await session.commit()
        return ApiResponse(message="教案已删除")


# ============================================================
# 本地上传教案 / PPT
# ============================================================
@router.post("/courses/{course_id}/upload-lesson")
async def upload_lesson_file(course_id: int, file: UploadFile = File(...)):
    """上传本地教案文件（DOCX/MD/TXT），自动解析并创建教案记录"""
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in (".docx", ".md", ".txt"):
        raise HTTPException(400, "仅支持 .docx/.md/.txt 格式教案文件")

    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        # 读取文件内容
        content_bytes = await file.read()
        content_text = content_bytes.decode("utf-8", errors="ignore")

        # 保存文件
        stored_path = await save_upload(content_bytes, file.filename or "lesson_upload.txt", course_id)

        # 构建基础教案结构
        chapter_name = Path(file.filename).stem[:30]
        plan = {
            "course_name": course.name,
            "chapter": chapter_name,
            "total_minutes": 90,
            "knowledge_goal": "",
            "ability_goal": "",
            "value_goal": "",
            "key_points": [],
            "difficult_points": [],
            "difficult_strategy": "",
            "stages": [],
            "homework": [],
            "board_design": "",
            "reflection": "（课后填写）",
            "source_text": content_text[:50000],
        }

        lesson = LessonORM(
            course_id=course_id,
            chapter=chapter_name,
            title=chapter_name,
            plan_json=plan,
            params_json={},
        )
        session.add(lesson)
        await session.flush()
        lesson_id = lesson.id
        await session.commit()

        return ApiResponse(
            data={
                "id": lesson_id,
                "course_id": course_id,
                "chapter": chapter_name,
                "title": chapter_name,
                "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
                "uploaded": True,
            }
        )


@router.post("/courses/{course_id}/upload-ppt")
async def upload_ppt_file(course_id: int, file: UploadFile = File(...)):
    """上传本地PPT文件（PPTX），存储到课程"""
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext != ".pptx":
        raise HTTPException(400, "仅支持 .pptx 格式PPT文件")

    async for session in get_session():
        course = await session.get(CourseORM, course_id)
        if not course:
            raise HTTPException(404, "课程不存在")

        content_bytes = await file.read()
        stored_path = await save_upload(content_bytes, file.filename or "upload.pptx", course_id)

        title = Path(file.filename).stem[:30]
        ppt = PptRecordORM(
            course_id=course_id,
            chapter=title,
            title=title,
            slide_count=0,
            slide_data={},
            source="upload",
            stored_path=str(stored_path),
        )
        session.add(ppt)
        await session.flush()
        ppt_id = ppt.id
        await session.commit()

        return ApiResponse(
            data={
                "id": ppt_id,
                "course_id": course_id,
                "title": title,
                "source": "upload",
                "created_at": ppt.created_at.isoformat() if ppt.created_at else None,
            }
        )


@router.get("/ppt/{ppt_id}/download")
async def download_ppt_file(ppt_id: int):
    """下载上传的PPT文件"""
    async for session in get_session():
        ppt = await session.get(PptRecordORM, ppt_id)
        if not ppt:
            raise HTTPException(404, "PPT记录不存在")
        if not ppt.stored_path:
            raise HTTPException(404, "该PPT没有关联文件")

        file_path = Path(ppt.stored_path)
        if not file_path.exists():
            raise HTTPException(404, "文件已被删除")

        content = file_path.read_bytes()
        filename_encoded = urllib.parse.quote(f"{ppt.title}.pptx")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ppt.title}.pptx\"; filename*=UTF-8''{filename_encoded}"
            },
        )


# ============================================================
# 对话修改
# ============================================================
@router.post("/lessons/{lesson_id}/chat")
async def chat_modify_lesson(lesson_id: int, payload: ChatRequest):
    """通过自然语言修改教案"""
    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")

        # 记录用户消息
        session.add(
            ChatMessageORM(
                course_id=lesson.course_id,
                role="user",
                content=payload.message,
            )
        )

        try:
            plan = LessonPlan(**lesson.plan_json)
        except Exception as e:
            raise HTTPException(500, f"教案数据损坏: {e}")

        try:
            result = await modify_lesson(
                course_name=plan.course_name,
                chapter=plan.chapter,
                current_plan=plan,
                user_message=payload.message,
            )
        except LLMError as e:
            raise HTTPException(502, str(e))

        response_text = ""
        new_plan_dict = None

        if result["type"] == "modified":
            new_plan: LessonPlan = result["plan"]
            lesson.plan_json = new_plan.model_dump()
            lesson.updated_at = datetime.utcnow()
            new_plan_dict = new_plan.model_dump()
            response_text = "已根据您的指令修改教案。"
        elif result["type"] == "clarify":
            response_text = result["question"]
        else:  # answer
            response_text = result["answer"]

        # 记录助手消息
        session.add(
            ChatMessageORM(
                course_id=lesson.course_id,
                role="assistant",
                content=response_text,
                metadata_json={"type": result["type"]},
            )
        )
        await session.commit()

        return ApiResponse(
            data={
                "type": result["type"],
                "response": response_text,
                "plan": new_plan_dict,
            }
        )


@router.get("/courses/{course_id}/messages")
async def list_messages(course_id: int, limit: int = 50):
    async for session in get_session():
        result = await session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.course_id == course_id)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
        )
        msgs = list(reversed(result.scalars().all()))
        return ApiResponse(
            data=[
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.metadata_json,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in msgs
            ]
        )


# ============================================================
# 导出
# ============================================================
@router.get("/lessons/{lesson_id}/export/{fmt}")
async def export_lesson(lesson_id: int, fmt: str):
    """导出教案：fmt=markdown|docx|pptx"""
    if fmt not in ("markdown", "docx", "pptx"):
        raise HTTPException(400, "格式仅支持 markdown、docx 或 pptx")

    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")
        try:
            plan = LessonPlan(**lesson.plan_json)
        except Exception as e:
            raise HTTPException(500, f"教案数据损坏: {e}")

        # 安全的文件名：课程名+章节，去除特殊字符
        safe_title = f"{plan.course_name}_{plan.chapter}".replace(" ", "_")
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in "_-")
        if not safe_title:
            safe_title = f"lesson_{lesson_id}"

        # ASCII fallback 文件名（header 不支持非 ASCII）
        ascii_fallback = f"lesson_{lesson_id}"

        if fmt == "markdown":
            content = export_markdown(plan)
            filename_encoded = urllib.parse.quote(f"{safe_title}.md")
            return Response(
                content=content.encode("utf-8"),
                media_type="text/markdown; charset=utf-8",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{ascii_fallback}.md\"; filename*=UTF-8''{filename_encoded}"
                },
            )
        elif fmt == "docx":
            try:
                content = export_docx(plan)
            except Exception as e:
                raise HTTPException(500, f"DOCX生成失败: {e}")
            filename_encoded = urllib.parse.quote(f"{safe_title}.docx")
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{ascii_fallback}.docx\"; filename*=UTF-8''{filename_encoded}"
                },
            )
        else:  # pptx — 使用默认参数生成教学PPT
            # 获取知识点
            stmt = (
                select(KnowledgePointORM)
                .where(KnowledgePointORM.course_id == lesson.course_id)
                .order_by(KnowledgePointORM.sort_order)
            )
            result = await session.execute(stmt)
            kps = result.scalars().all()
            knowledge_points = [
                {
                    "name": k.name,
                    "definition": k.definition,
                    "source_pages": k.source_pages or "",
                    "layer": k.layer,
                    "is_key_point": bool(k.is_key_point),
                    "is_difficult": bool(k.is_difficult),
                    "is_exam_point": bool(k.is_exam_point),
                }
                for k in kps
            ]

            # 检索教材原文上下文
            textbook_context = await _build_textbook_context(session, lesson.course_id, knowledge_points)

            try:
                slide_data = await generate_ppt_content(
                    plan=plan,
                    knowledge_points=knowledge_points,
                    style="cyan_ink",
                    content_density="moderate",
                    image_style="icons",
                    textbook_context=textbook_context,
                )
                content = export_teaching_pptx(slide_data, style="cyan_ink")
            except Exception as e:
                raise HTTPException(500, f"PPT生成失败: {e}")
            filename_encoded = urllib.parse.quote(f"{safe_title}.pptx")
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{ascii_fallback}.pptx\"; filename*=UTF-8''{filename_encoded}"
                },
            )


@router.post("/lessons/{lesson_id}/export-ppt")
async def export_lesson_ppt(lesson_id: int, payload: dict):
    """生成教学PPT（带参数配置）

    请求体：
    {
        "style": "academic|cyan_ink|cute_cartoon|formal|minimal",
        "content_density": "detailed|moderate|concise",
        "image_style": "none|icons|rich",
        "style_custom": "用户自定义风格描述（可选）"
    }
    """
    style = payload.get("style", "cyan_ink")
    content_density = payload.get("content_density", "moderate")
    image_style = payload.get("image_style", "icons")
    style_custom = payload.get("style_custom", "")

    async for session in get_session():
        lesson = await session.get(LessonORM, lesson_id)
        if not lesson:
            raise HTTPException(404, "教案不存在")
        try:
            plan = LessonPlan(**lesson.plan_json)
        except Exception as e:
            raise HTTPException(500, f"教案数据损坏: {e}")

        # 获取知识点
        stmt = (
            select(KnowledgePointORM)
            .where(KnowledgePointORM.course_id == lesson.course_id)
            .order_by(KnowledgePointORM.sort_order)
        )
        result = await session.execute(stmt)
        kps = result.scalars().all()
        knowledge_points = [
            {
                "name": k.name,
                "definition": k.definition,
                "source_pages": k.source_pages or "",
                "layer": k.layer,
                "is_key_point": bool(k.is_key_point),
                "is_difficult": bool(k.is_difficult),
                "is_exam_point": bool(k.is_exam_point),
            }
            for k in kps
        ]

        # 检索教材原文上下文
        textbook_context = await _build_textbook_context(session, lesson.course_id, knowledge_points)

        try:
            slide_data = await generate_ppt_content(
                plan=plan,
                knowledge_points=knowledge_points,
                style=style,
                content_density=content_density,
                image_style=image_style,
                style_custom=style_custom,
                textbook_context=textbook_context,
            )
            content = export_teaching_pptx(slide_data, style=style)
        except Exception as e:
            raise HTTPException(500, f"PPT生成失败: {e}")

        # 保存PPT记录
        slide_count = 0
        if slide_data and isinstance(slide_data, dict):
            slides = slide_data.get("slides", [])
            if isinstance(slides, list):
                slide_count = len(slides)

        ppt_record = PptRecordORM(
            course_id=lesson.course_id,
            lesson_id=lesson_id,
            chapter=plan.chapter,
            title=f"{plan.course_name} - {plan.chapter}",
            style=style,
            content_density=content_density,
            image_style=image_style,
            style_custom=style_custom,
            slide_count=slide_count,
            slide_data=slide_data,
        )
        session.add(ppt_record)
        await session.commit()
        await session.refresh(ppt_record)

        # 安全的文件名
        safe_title = f"{plan.course_name}_{plan.chapter}".replace(" ", "_")
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in "_-")
        if not safe_title:
            safe_title = f"lesson_{lesson_id}"
        ascii_fallback = f"lesson_{lesson_id}"
        filename_encoded = urllib.parse.quote(f"{safe_title}.pptx")

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ascii_fallback}.pptx\"; filename*=UTF-8''{filename_encoded}",
                "X-Ppt-Record-Id": str(ppt_record.id),
            },
        )


# ============================================================
# PPT记录管理
# ============================================================
@router.get("/courses/{course_id}/ppt-records")
async def list_ppt_records(course_id: int):
    """列出课程的PPT生成记录"""
    async for session in get_session():
        result = await session.execute(
            select(PptRecordORM)
            .where(PptRecordORM.course_id == course_id)
            .order_by(PptRecordORM.created_at.desc())
        )
        records = result.scalars().all()
        return ApiResponse(
            data=[
                {
                    "id": r.id,
                    "course_id": r.course_id,
                    "lesson_id": r.lesson_id,
                    "chapter": r.chapter,
                    "title": r.title,
                    "style": r.style,
                    "content_density": r.content_density,
                    "image_style": r.image_style,
                    "slide_count": r.slide_count,
                    "source": r.source,
                    "has_file": bool(r.stored_path),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        )


@router.get("/ppt-records/{record_id}")
async def get_ppt_record(record_id: int):
    """获取PPT记录详情"""
    async for session in get_session():
        r = await session.get(PptRecordORM, record_id)
        if not r:
            raise HTTPException(404, "PPT记录不存在")
        return ApiResponse(
            data={
                "id": r.id,
                "course_id": r.course_id,
                "lesson_id": r.lesson_id,
                "chapter": r.chapter,
                "title": r.title,
                "style": r.style,
                "content_density": r.content_density,
                "image_style": r.image_style,
                "style_custom": r.style_custom or "",
                "slide_count": r.slide_count,
                "slide_data": r.slide_data,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )


@router.delete("/ppt-records/{record_id}")
async def delete_ppt_record(record_id: int):
    """删除PPT记录"""
    async for session in get_session():
        r = await session.get(PptRecordORM, record_id)
        if not r:
            raise HTTPException(404, "PPT记录不存在")
        await session.delete(r)
        await session.commit()
        return ApiResponse(message="PPT记录已删除")


@router.post("/ppt-records/{record_id}/download")
async def download_ppt(record_id: int):
    """重新下载PPT（根据已有记录生成）"""
    async for session in get_session():
        r = await session.get(PptRecordORM, record_id)
        if not r:
            raise HTTPException(404, "PPT记录不存在")

        slide_data = r.slide_data
        if not slide_data:
            raise HTTPException(400, "PPT数据为空，请重新生成")

        try:
            content = export_teaching_pptx(slide_data, style=r.style)
        except Exception as e:
            raise HTTPException(500, f"PPT生成失败: {e}")

        safe_title = r.title or f"ppt_{record_id}"
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in "_-")
        if not safe_title:
            safe_title = f"ppt_{record_id}"
        ascii_fallback = f"ppt_{record_id}"
        filename_encoded = urllib.parse.quote(f"{safe_title}.pptx")

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ascii_fallback}.pptx\"; filename*=UTF-8''{filename_encoded}"
            },
        )


# ============================================================
# 健康检查 / API连通性
# ============================================================
@router.get("/health")
async def health():
    return ApiResponse(message="ok", data={"status": "healthy"})


@router.get("/llm-test")
async def llm_test():
    """测试当前LLM连通性"""
    cfg = get_llm_config()
    if not cfg.is_configured():
        raise HTTPException(
            502,
            "LLM未配置，请点击右上角「设置」按钮配置 API Key、Base URL 和模型",
        )
    try:
        llm = get_llm()
        text = await llm.chat(
            system_prompt="你是测试助手。",
            user_prompt="请回复：连通正常",
            temperature=0.0,
            max_tokens=30,
        )
        current = cfg.get_masked()
        return ApiResponse(
            message="LLM连通正常",
            data={
                "response": text,
                "provider": current["provider"],
                "model": current["model"],
                "base_url": current["base_url"],
            },
        )
    except LLMError as e:
        raise HTTPException(502, f"LLM不可用: {e}")


# ============================================================
# LLM 设置管理
# ============================================================
@router.get("/settings/llm")
async def get_llm_settings():
    """获取当前 LLM 设置（API Key 掩码）"""
    cfg = get_llm_config()
    return ApiResponse(
        data={
            "current": cfg.get_masked(),
            "providers": PRESET_PROVIDERS,
            "is_configured": cfg.is_configured(),
        }
    )


@router.put("/settings/llm")
async def update_llm_settings(payload: LLMSettingsUpdate):
    """保存 LLM 设置"""
    cfg = get_llm_config()
    # 过滤 None 值
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        return ApiResponse(message="无更新内容", data=cfg.get_masked())

    try:
        cfg.update(update_data)
        reset_llm()
    except Exception as e:
        raise HTTPException(500, f"保存失败: {e}")

    return ApiResponse(
        message="设置已保存",
        data=cfg.get_masked(),
    )


@router.post("/settings/llm/test")
async def test_llm_settings(payload: LLMSettingsUpdate):
    """测试给定的 LLM 配置（不持久化，直接测试）"""
    cfg = get_llm_config()
    current = cfg.get_all()
    # 合并：用户提交的覆盖当前（处理掩码）
    test_cfg = {
        "provider": payload.provider or current["provider"],
        "api_key": current["api_key"],
        "base_url": payload.base_url or current["base_url"],
        "model": payload.model or current["model"],
        "temperature": payload.temperature if payload.temperature is not None else current["temperature"],
        "max_tokens": payload.max_tokens if payload.max_tokens is not None else current["max_tokens"],
    }
    # 若用户提交了非掩码 api_key，使用新值
    if payload.api_key and "****" not in payload.api_key:
        test_cfg["api_key"] = payload.api_key

    if not test_cfg["api_key"]:
        raise HTTPException(400, "请填写 API Key")
    if not test_cfg["base_url"]:
        raise HTTPException(400, "请填写 Base URL")
    if not test_cfg["model"]:
        raise HTTPException(400, "请填写模型名称")

    try:
        from ..core.llm import LLMClient

        client = LLMClient(test_cfg)
        text = await client.chat(
            system_prompt="你是测试助手。",
            user_prompt="请回复：连通正常",
            temperature=0.0,
            max_tokens=30,
        )
        return ApiResponse(
            message="连接测试成功",
            data={
                "response": text,
                "provider": test_cfg["provider"],
                "model": test_cfg["model"],
                "base_url": test_cfg["base_url"],
            },
        )
    except LLMError as e:
        raise HTTPException(502, f"连接测试失败: {e}")
    except Exception as e:
        raise HTTPException(502, f"连接测试失败: {type(e).__name__}: {e}")


# 引入settings用于llm-test
from ..config import settings  # noqa: E402
