"""对话修改 Agent：自然语言指令修改教案"""
from __future__ import annotations

import json
from typing import Optional

from ..core.llm import get_llm
from ..core.prompts import CHAT_SYSTEM, CHAT_USER_TEMPLATE
from ..models.schemas import LessonPlan


async def modify_lesson(
    course_name: str,
    chapter: str,
    current_plan: LessonPlan,
    user_message: str,
) -> dict:
    """根据自然语言指令修改教案

    返回字典：
    - {"type": "modified", "plan": LessonPlan}  修改成功
    - {"type": "clarify", "question": str}       需要澄清
    - {"type": "answer", "answer": str}          询问性回答
    """
    llm = get_llm()

    plan_dict = current_plan.model_dump()
    user_prompt = CHAT_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        lesson_json=json.dumps(plan_dict, ensure_ascii=False, indent=2),
        user_message=user_message,
    )

    data = await llm.chat_json(CHAT_SYSTEM, user_prompt, temperature=0.6)

    if data.get("need_clarify"):
        return {"type": "clarify", "question": data.get("question", "请补充您的修改意图")}
    if data.get("answer"):
        return {"type": "answer", "answer": data["answer"]}

    # 修改后的教案
    try:
        new_plan = LessonPlan(
            course_name=data.get("course_name", current_plan.course_name),
            chapter=data.get("chapter", current_plan.chapter),
            total_minutes=int(data.get("total_minutes", current_plan.total_minutes)),
            teaching_object=data.get("teaching_object", current_plan.teaching_object),
            teacher_name=data.get("teacher_name", current_plan.teacher_name),
            knowledge_goal=data.get("knowledge_goal", current_plan.knowledge_goal),
            ability_goal=data.get("ability_goal", current_plan.ability_goal),
            value_goal=data.get("value_goal", current_plan.value_goal),
            key_points=list(data.get("key_points", current_plan.key_points)),
            difficult_points=list(data.get("difficult_points", current_plan.difficult_points)),
            difficult_strategy=data.get("difficult_strategy", current_plan.difficult_strategy),
            stages=[
                {
                    "name": s.get("name", ""),
                    "duration_min": int(s.get("duration_min", 0)),
                    "teacher_activity": s.get("teacher_activity", ""),
                    "student_activity": s.get("student_activity", ""),
                    "design_intent": s.get("design_intent", ""),
                    "content": s.get("content", ""),
                }
                for s in data.get("stages", current_plan.stages)
            ],
            board_design=data.get("board_design", current_plan.board_design),
            homework=list(data.get("homework", current_plan.homework)),
            reflection=data.get("reflection", current_plan.reflection),
        )
        return {"type": "modified", "plan": new_plan}
    except Exception as e:
        return {
            "type": "answer",
            "answer": f"抱歉，修改过程中出现错误：{e}。请尝试更明确的修改指令。",
        }
