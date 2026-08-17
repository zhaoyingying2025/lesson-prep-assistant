"""知识点提取 Agent"""
from __future__ import annotations

import json
from typing import Optional

from ..core.llm import get_llm
from ..core.prompts import KNOWLEDGE_SYSTEM, KNOWLEDGE_USER_TEMPLATE
from ..models.schemas import KnowledgeExtractionResult


async def extract_knowledge(
    course_name: str,
    chapter: str,
    text: str,
) -> KnowledgeExtractionResult:
    """从教材文本中提取结构化知识点"""
    llm = get_llm()
    # 控制输入文本长度
    max_input = 12000
    truncated = text[:max_input] if len(text) > max_input else text

    user_prompt = KNOWLEDGE_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        text=truncated,
    )

    data = await llm.chat_json(KNOWLEDGE_SYSTEM, user_prompt, temperature=0.3)

    # 规范化字段
    points = []
    for p in data.get("points", []):
        try:
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
                }
            )
        except Exception:
            continue

    return KnowledgeExtractionResult(
        chapter=data.get("chapter", chapter),
        points=points,  # type: ignore[arg-type]
        summary=data.get("summary", ""),
    )
