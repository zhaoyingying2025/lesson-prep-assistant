"""知识点提取 Agent"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Optional

from ..core.llm import get_llm
from ..core.prompts import (
    KNOWLEDGE_SYSTEM,
    KNOWLEDGE_TO_CHAPTER_SYSTEM,
    KNOWLEDGE_TO_CHAPTER_USER_TEMPLATE,
    KNOWLEDGE_USER_TEMPLATE,
)
from ..core.prompt_loader import inject_domain_context
from ..models.schemas import KnowledgeExtractionResult


async def extract_knowledge(
    course_name: str,
    chapter: str,
    text: str,
    subject: Optional[str] = None,
) -> KnowledgeExtractionResult:
    """从教材文本中提取结构化知识点

    Args:
        subject: 学科标识(如 math/chinese/english/physics 等), 用于注入学科领域规则
    """
    llm = get_llm()
    max_input = 12000
    truncated = text[:max_input] if len(text) > max_input else text

    user_prompt = KNOWLEDGE_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        text=truncated,
    )

    system_prompt = inject_domain_context(KNOWLEDGE_SYSTEM, subject)

    data = await llm.chat_json(system_prompt, user_prompt, temperature=0.3)

    points = []
    for p in data.get("points", []):
        try:
            relationships_raw = p.get("relationships") or []
            relationships = []
            for r in relationships_raw:
                target = str(r.get("target", "")).strip()
                rel_type = str(r.get("rel_type", "依赖")).strip()
                if target:
                    relationships.append({"target": target, "rel_type": rel_type})

            points.append(
                {
                    "name": str(p.get("name", "")).strip(),
                    "layer": p.get("layer", "core") if p.get("layer") in ("basic", "core", "extension") else "core",
                    "definition": str(p.get("definition", "")).strip(),
                    "source_pages": str(p.get("source_pages", "")).strip(),
                    "importance": int(p.get("importance", 3)),
                    "difficulty": int(p.get("difficulty", 3)),
                    "is_key_point": bool(p.get("is_key_point", False)),
                    "is_difficult": bool(p.get("is_difficult", False)),
                    "is_exam_point": bool(p.get("is_exam_point", False)),
                    "prerequisites": list(p.get("prerequisites", [])),
                    "relationships": relationships,
                }
            )
        except Exception:
            continue

    return KnowledgeExtractionResult(
        chapter=data.get("chapter", chapter),
        points=points,
        summary=data.get("summary", ""),
    )


async def chunked_extract_knowledge(
    course_name: str,
    chapter: str,
    text: str,
    chunk_size: int = 8000,
    overlap: int = 500,
    progress_callback=None,
    subject: Optional[str] = None,
    max_concurrency: int = 3,
) -> KnowledgeExtractionResult:
    """分段并行提取知识点：将长文本智能分割后并发提取，合并去重

    优化点：
    1. 智能分块：按段落/句子边界切割，避免切断语义单元
    2. 并行处理：多 chunk 并发调用 LLM，大幅提速
    3. 关系图谱：合并各 chunk 的知识点关系

    Args:
        subject: 学科标识
        max_concurrency: 最大并行数（默认3，避免 LLM 限流）
    """
    if len(text) <= chunk_size:
        result = await extract_knowledge(course_name, chapter, text, subject=subject)
        if progress_callback:
            pts = [p.model_dump() if hasattr(p, 'model_dump') else p for p in (result.points or [])]
            await progress_callback(1, 1, pts)
        return result

    chunks = _smart_split_text(text, chunk_size, overlap)
    chapter_title = chapter

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _process_chunk(idx: int, chunk: str) -> tuple[int, KnowledgeExtractionResult]:
        async with semaphore:
            chunk_label = f"{chapter} (第{idx+1}段/共{len(chunks)}段)"
            return idx, await extract_knowledge(course_name, chunk_label, chunk, subject=subject)

    tasks = [_process_chunk(i, c) for i, c in enumerate(chunks)]
    all_points: list[dict] = []
    summary_parts: list[str] = []
    completed = 0

    for coro in asyncio.as_completed(tasks):
        idx, result = await coro
        if result.points:
            pts = [p.model_dump() if hasattr(p, 'model_dump') else p for p in result.points]
            all_points.extend(pts)
        if result.summary:
            summary_parts.append(result.summary)
        if result.chapter and result.chapter != f"{chapter} (第{idx+1}段/共{len(chunks)}段)":
            chapter_title = result.chapter
        completed += 1
        if progress_callback:
            await progress_callback(completed, len(chunks), list(all_points))

    merged = _merge_points(all_points)

    merged_count = len(merged)
    filtered = _filter_quality_points(merged)
    if len(filtered) < len(merged) and filtered:
        merged = filtered

    combined_summary = "；".join(s for s in summary_parts if s)
    if not combined_summary:
        merged_desc = f"共提取 {len(merged)} 个知识点"
        if len(merged) < merged_count:
            merged_desc += f"（自动过滤 {merged_count - len(merged)} 个低质量条目）"
        else:
            merged_desc += "（分段并行提取合并）"
        combined_summary = merged_desc

    return KnowledgeExtractionResult(
        chapter=chapter_title,
        points=merged,
        summary=combined_summary,
    )


def _smart_split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """智能分割文本：在段落或句子边界处切割，避免切断语义单元

    优先在段落边界（双换行）处分割，
    次优在句子边界（句号/问号/感叹号）处分割，
    最后才在换行处分割。
    chunk 之间保留 overlap 字符的重叠以确保上下文连贯。
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        if start + chunk_size >= len(text):
            chunks.append(text[start:])
            break

        end = _find_break_point(text, start, start + chunk_size)
        chunks.append(text[start:end])
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start

    return chunks


def _find_break_point(text: str, start: int, end: int) -> int:
    """在 [start, end] 范围内寻找最佳切割点，优先级：段落边界 > 句子边界 > 换行 > 硬切"""
    segment = text[start:end]

    para_break = segment.rfind('\n\n')
    if para_break != -1 and para_break > len(segment) * 0.5:
        return start + para_break + 2

    for delim in ['。\n', '！\n', '？\n', '.\n', '!\n', '?\n']:
        pos = segment.rfind(delim)
        if pos != -1 and pos > len(segment) * 0.4:
            return start + pos + len(delim)

    for delim in ['。', '！', '？', '.', '!', '?']:
        pos = segment.rfind(delim)
        if pos != -1 and pos > len(segment) * 0.4:
            return start + pos + 1

    line_break = segment.rfind('\n')
    if line_break != -1 and line_break > len(segment) * 0.3:
        return start + line_break + 1

    return end


def _filter_quality_points(points: list[dict]) -> list[dict]:
    """过滤低质量/不完整的知识点，保留高质量条目

    过滤规则：
    1. 名称过短（< 2 字符）或为空
    2. 定义过短（< 15 字符）或为占位符
    3. 定义中包含明显的占位符文本
    4. 重要度或难度不在 1-5 范围内
    5. 定义与已有知识点高度相似（去重冗余定义）
    """
    PLACEHOLDER_PATTERNS = [
        "待补充", "暂无", "待完善", "待填", "待定",
        "暂无定义", "暂无内容", "待补充内容",
        "请补充", "请完善",
    ]
    filtered = []
    seen_definitions: list[str] = []
    for p in points:
        nm = (p.get("name") or "").strip()
        definition = (p.get("definition") or "").strip()
        if len(nm) < 2:
            continue
        if len(definition) < 15:
            continue
        def_lower = definition.lower()
        is_placeholder = any(pat in def_lower for pat in PLACEHOLDER_PATTERNS)
        if is_placeholder:
            continue
        importance = int(p.get("importance") or 3)
        difficulty = int(p.get("difficulty") or 3)
        if not (1 <= importance <= 5) or not (1 <= difficulty <= 5):
            continue
        is_dup_def = False
        for existing_def in seen_definitions:
            if SequenceMatcher(None, definition, existing_def).ratio() > 0.9:
                is_dup_def = True
                break
        if is_dup_def:
            continue
        seen_definitions.append(definition)
        filtered.append(p)
    return filtered


def _fuzzy_match_key(name: str, seen_keys: set[str]) -> str | None:
    """模糊匹配已存在的知识点名称，返回匹配到的 key 或 None

    匹配策略：
    1. 精确匹配（忽略大小写）
    2. 包含关系（一个名称是另一个的子串）
    3. 相似度阈值（SequenceMatcher > 0.85）
    """
    lowered = name.lower().strip()
    if lowered in seen_keys:
        return lowered
    for k in seen_keys:
        if lowered in k or k in lowered:
            return k
    for k in seen_keys:
        if SequenceMatcher(None, lowered, k).ratio() > 0.85:
            return k
    return None


def _merge_points(points: list[dict]) -> list[dict]:
    """合并多个chunk提取的知识点，按名称去重，合并关系

    增强的去重策略：
    1. 精确匹配（忽略大小写）
    2. 包含关系匹配（如 "机器学习" 与 "监督机器学习"）
    3. 模糊相似度匹配（SequenceMatcher > 0.85）
    """
    seen: dict[str, dict] = {}
    seen_keys: set[str] = set()
    for p in points:
        nm = (p.get("name") or "").strip()
        if not nm:
            continue
        key = nm.lower()
        existing_key = _fuzzy_match_key(nm, seen_keys) if key not in seen else key
        if existing_key and existing_key in seen:
            old = seen[existing_key]
            old_def = old.get("definition", "")
            new_def = p.get("definition", "")
            if len(new_def) > len(old_def):
                old["definition"] = new_def
            old_pages = old.get("source_pages", "")
            new_pages = p.get("source_pages", "")
            if new_pages and new_pages not in old_pages:
                old["source_pages"] = (old_pages + "; " + new_pages).strip("; ")
            for flag in ("is_key_point", "is_difficult", "is_exam_point"):
                if p.get(flag):
                    old[flag] = True
            old_imp = old.get("importance", 3)
            new_imp = p.get("importance", 3)
            old["importance"] = max(old_imp, new_imp)
            old_dif = old.get("difficulty", 3)
            new_dif = p.get("difficulty", 3)
            old["difficulty"] = max(old_dif, new_dif)
            old_prereq = set(old.get("prerequisites") or [])
            new_prereq = set(p.get("prerequisites") or [])
            old["prerequisites"] = list(old_prereq | new_prereq)

            old_rels = old.get("relationships") or []
            new_rels = p.get("relationships") or []
            existing_targets = {(r["target"], r["rel_type"]) for r in old_rels}
            for r in new_rels:
                key_r = (r["target"], r["rel_type"])
                if key_r not in existing_targets:
                    old_rels.append(r)
                    existing_targets.add(key_r)
            old["relationships"] = old_rels
        else:
            seen[key] = {
                "name": nm,
                "definition": (p.get("definition") or "").strip(),
                "source_pages": (p.get("source_pages") or "").strip(),
                "layer": p.get("layer") if p.get("layer") in ("basic", "core", "extension") else "core",
                "importance": int(p.get("importance") or 3),
                "difficulty": int(p.get("difficulty") or 3),
                "is_key_point": bool(p.get("is_key_point", False)),
                "is_difficult": bool(p.get("is_difficult", False)),
                "is_exam_point": bool(p.get("is_exam_point", False)),
                "prerequisites": list(p.get("prerequisites") or []),
                "relationships": list(p.get("relationships") or []),
            }
            seen_keys.add(key)
    return list(seen.values())


async def organize_knowledge_into_chapters(
    course_name: str,
    knowledge_points: list[dict],
) -> list[dict]:
    """将提取的知识点组织成章节目录结构（章→节二级），返回章节列表"""
    if not knowledge_points:
        return []
    kp_json = json.dumps(
        [{"name": kp["name"]} for kp in knowledge_points if kp.get("name")],
        ensure_ascii=False,
        indent=2,
    )
    llm = get_llm()
    user_prompt = KNOWLEDGE_TO_CHAPTER_USER_TEMPLATE.format(
        course_name=course_name,
        knowledge_json=kp_json,
    )
    data = await llm.chat_json(
        KNOWLEDGE_TO_CHAPTER_SYSTEM, user_prompt, temperature=0.3
    )
    return data.get("chapters", [])