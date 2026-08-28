# -*- coding: utf-8 -*-
"""Smart extract agent: identify chapter structure and extract knowledge points from textbook content."""

from __future__ import annotations

from typing import Any, Optional

from ..core.llm import get_llm
from ..core.prompts import SMART_EXTRACT_SYSTEM, SMART_EXTRACT_USER_TEMPLATE
from ..core.prompt_loader import inject_domain_context


async def smart_extract(
    course_name: str,
    filenames: str,
    text: str,
    subject: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Extract chapter structure and knowledge points from textbook content.

    Args:
        subject: 学科标识(如 math/chinese/english/physics 等), 用于注入学科领域规则
    """
    llm = get_llm()
    max_input = 25000
    truncated = text[:max_input] if len(text) > max_input else text

    user_prompt = SMART_EXTRACT_USER_TEMPLATE.format(
        course_name=course_name,
        filenames=filenames,
        text=truncated,
    )

    # 注入学科领域规则 (借鉴 ai-teaching-ppt 的多槽位注入)
    system_prompt = inject_domain_context(SMART_EXTRACT_SYSTEM, subject)

    data = await llm.chat_json(system_prompt, user_prompt, temperature=0.3)

    chapters = data.get("chapters", [])
    if not isinstance(chapters, list):
        chapters = []

    def _normalize_node(node: dict) -> dict:
        return {
            "name": str(node.get("name", "")).strip(),
            "children": [_normalize_node(c) for c in (node.get("children") or [])],
            "knowledge_points": [
                {
                    "name": str(p.get("name", "")).strip(),
                    "definition": str(p.get("definition", "")).strip(),
                    "source_pages": str(p.get("source_pages", "")).strip(),
                    "layer": (
                        p.get("layer", "core")
                        if p.get("layer") in ("basic", "core", "extension")
                        else "core"
                    ),
                    "is_key_point": bool(p.get("is_key_point", False)),
                    "is_difficult": bool(p.get("is_difficult", False)),
                    "is_exam_point": bool(p.get("is_exam_point", False)),
                }
                for p in (node.get("knowledge_points") or [])
                if str(p.get("name", "")).strip()
            ],
        }

    return [_normalize_node(c) for c in chapters]
