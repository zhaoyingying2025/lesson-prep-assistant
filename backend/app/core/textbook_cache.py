"""教材内容缓存与检索模块

功能：
1. 上传教材时自动按页索引，存入 textbook_chunks 表
2. 知识点提取时快速检索原文页码
3. 教案/PPT生成时检索教材原文作为上下文
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..storage.db import TextbookChunkORM
from .parser import parse_file_with_pages


async def index_material(
    session: AsyncSession,
    material_id: int,
    course_id: int,
    file_path: Path,
    max_chars: int = 50000,
) -> int:
    """解析教材并按页存入缓存

    Args:
        session: 数据库会话
        material_id: 教材记录ID
        course_id: 课程ID
        file_path: 教材文件路径
        max_chars: 最大解析字符数

    Returns:
        索引的页数
    """
    # 先清除旧索引
    await session.execute(
        delete(TextbookChunkORM).where(
            TextbookChunkORM.material_id == material_id,
            TextbookChunkORM.course_id == course_id,
        )
    )

    # 按页解析
    pages = parse_file_with_pages(file_path, max_chars)
    if not pages:
        return 0

    # 批量入库
    for page in pages:
        text = page["text"].strip()
        if not text:
            continue
        chunk = TextbookChunkORM(
            material_id=material_id,
            course_id=course_id,
            page_number=page["page_number"],
            chunk_text=text,
            char_count=len(text),
        )
        session.add(chunk)

    await session.flush()
    return len(pages)


async def search_textbook(
    session: AsyncSession,
    course_id: int,
    query: str,
    limit: int = 5,
    max_chars_per_chunk: int = 2000,
) -> list[dict]:
    """在教材缓存中搜索与查询词相关的文本块

    使用关键词匹配 + 相关性排序，返回最匹配的页级文本块

    Args:
        session: 数据库会话
        course_id: 课程ID
        query: 搜索关键词
        limit: 最多返回的文本块数
        max_chars_per_chunk: 每个文本块最大字符数（截断）

    Returns:
        [{"material_id": int, "page_number": int, "text": str, "score": float}, ...]
    """
    # 提取关键词（按空格/标点分词，去重，过滤过短的词）
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    # 查询所有该课程的文本块
    result = await session.execute(
        select(TextbookChunkORM)
        .where(TextbookChunkORM.course_id == course_id)
        .order_by(TextbookChunkORM.page_number)
    )
    all_chunks: list[TextbookChunkORM] = result.scalars().all()

    # 评分排序
    scored: list[tuple[float, TextbookChunkORM]] = []
    for chunk in all_chunks:
        score = _score_chunk(chunk.chunk_text, keywords)
        if score > 0:
            scored.append((score, chunk))

    # 按分数降序取 top
    scored.sort(key=lambda x: -x[0])
    results = []
    for score, chunk in scored[:limit]:
        text = chunk.chunk_text[:max_chars_per_chunk]
        if len(chunk.chunk_text) > max_chars_per_chunk:
            text += "..."
        results.append({
            "material_id": chunk.material_id,
            "page_number": chunk.page_number,
            "text": text,
            "score": round(score, 2),
        })

    return results


async def get_knowledge_point_context(
    session: AsyncSession,
    course_id: int,
    kp_name: str,
    surrounding_pages: int = 1,
) -> Optional[dict]:
    """获取知识点在教材中的原文上下文

    先搜索最匹配的页，然后返回该页及前后页的内容

    Args:
        session: 数据库会话
        course_id: 课程ID
        kp_name: 知识点名称
        surrounding_pages: 前后各取几页

    Returns:
        {"page_number": int, "context": str} 或 None（未找到）
    """
    results = await search_textbook(session, course_id, kp_name, limit=1)
    if not results:
        return None

    best = results[0]
    target_page = best["page_number"]

    # 获取该页及前后页的内容
    result = await session.execute(
        select(TextbookChunkORM)
        .where(TextbookChunkORM.course_id == course_id)
        .where(
            TextbookChunkORM.page_number.between(
                max(1, target_page - surrounding_pages),
                target_page + surrounding_pages,
            )
        )
        .order_by(TextbookChunkORM.page_number)
    )
    chunks: list[TextbookChunkORM] = result.scalars().all()

    context_parts = []
    for c in chunks:
        context_parts.append(f"[第{c.page_number}页]\n{c.chunk_text}")

    return {
        "page_number": target_page,
        "context": "\n\n".join(context_parts),
    }


def _extract_keywords(text: str) -> list[str]:
    """从文本中提取有意义的搜索关键词"""
    # 去除非中文、非英文、非数字的字符（保留空格）
    text = re.sub(r"[^\w\u4e00-\u9fff\s]", " ", text)
    # 分词
    words = text.split()
    # 过滤：保留长度 >= 2 的词
    keywords = [w.strip() for w in words if len(w.strip()) >= 2]
    # 去重，保留原顺序
    seen = set()
    unique = []
    for w in keywords:
        if w.lower() not in seen:
            seen.add(w.lower())
            unique.append(w)
    return unique


def _score_chunk(text: str, keywords: list[str]) -> float:
    """计算文本块与关键词的相关性评分"""
    text_lower = text.lower()
    score = 0.0
    for kw in keywords:
        kw_lower = kw.lower()
        count = text_lower.count(kw_lower)
        if count > 0:
            # 基础分 + 频率加分
            score += 1.0 + count * 0.5
            # 完整短语匹配加分
            if kw_lower in text_lower:
                score += 2.0
    return score