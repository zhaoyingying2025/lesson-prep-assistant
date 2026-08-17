"""教学PPT生成 Agent：将教案转化为课堂使用的教学幻灯片"""
from __future__ import annotations

import json
from typing import Any

from ..core.llm import get_llm
from ..core.prompts import PPT_SYSTEM, PPT_USER_TEMPLATE
from ..models.schemas import LessonPlan


# 风格配置
PPT_STYLES = {
    "academic": {
        "label": "学术简约",
        "desc": "干净清晰，蓝白配色，适合理工科",
    },
    "cyan_ink": {
        "label": "青绿水墨",
        "desc": "传统水墨风格，淡雅配色，适合文科/艺术",
    },
    "cute_cartoon": {
        "label": "清新卡通",
        "desc": "温暖活泼，圆角设计，适合低年级",
    },
    "formal": {
        "label": "商务正式",
        "desc": "深色稳重，适合MBA/管理类课程",
    },
    "minimal": {
        "label": "极简黑白",
        "desc": "纯黑白灰，极度简洁，适合任何场合",
    },
}

DENSITY_DESC = {
    "detailed": "内容详细丰富，每页3-5个要点，适合自学或复习课",
    "moderate": "内容适中，每页2-3个要点，适合常规课堂教学",
    "concise": "内容精炼简洁，每页1-2个要点，适合快速讲授或复习",
}

IMAGE_DESC = {
    "none": "无图，纯文字排版，用表格、对比、流程图等文字化视觉元素",
    "icons": "使用图标装饰，用文字符号（如★●▶◆）辅助视觉层级",
    "rich": "使用丰富的视觉表达，如分栏、表格、对比框、引用块等布局变化",
}


async def generate_ppt_content(
    plan: LessonPlan,
    knowledge_points: list[dict],
    style: str = "academic",
    content_density: str = "moderate",
    image_style: str = "icons",
    style_custom: str = "",
    textbook_context: str = "",
) -> dict[str, Any]:
    """调用LLM生成教学PPT的幻灯片结构

    Args:
        plan: 完整教案
        knowledge_points: 知识点列表
        style: PPT视觉风格
        content_density: 内容密度
        image_style: 视觉元素风格
        style_custom: 用户自定义风格描述
        textbook_context: 教材原文参考，用于知识点解释时引用教材原文

    Returns:
        {"style_used": str, "total_slides": int, "slides": [...]}
    """
    llm = get_llm()

    params = {
        "style": PPT_STYLES.get(style, PPT_STYLES["academic"])["label"],
        "density": content_density,
        "content_density_desc": DENSITY_DESC.get(content_density, DENSITY_DESC["moderate"]),
        "image_style_desc": IMAGE_DESC.get(image_style, IMAGE_DESC["icons"]),
        "style_custom": style_custom,
    }

    # 课程序列化
    plan_dict = plan.model_dump()
    # 将 stages 等对象转为 dict
    plan_dict["stages"] = [s.model_dump() for s in plan.stages]

    user_prompt = PPT_USER_TEMPLATE.format(
        course_name=plan.course_name,
        chapter=plan.chapter,
        total_minutes=plan.total_minutes,
        lesson_json=json.dumps(plan_dict, ensure_ascii=False, indent=2),
        knowledge_json=json.dumps(knowledge_points, ensure_ascii=False, indent=2),
        textbook_context=textbook_context or "（暂无教材原文参考，请基于知识点内容生成）",
        params_json=json.dumps(params, ensure_ascii=False, indent=2),
        style=style,
        density=content_density,
        content_density_desc=params["content_density_desc"],
        image_style_desc=params["image_style_desc"],
    )

    data = await llm.chat_json(PPT_SYSTEM, user_prompt, temperature=0.8)

    # 验证结构
    if "slides" not in data or not isinstance(data["slides"], list):
        raise ValueError("PPT生成失败：LLM返回结构异常")

    return data