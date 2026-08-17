"""教案设计 Agent（六阶段结构）"""
from __future__ import annotations

import json
from typing import Optional

from ..core.llm import get_llm
from ..core.prompts import LESSON_SYSTEM, LESSON_USER_TEMPLATE
from ..models.schemas import LessonParams, LessonPlan, LessonStage


def _validate_and_balance_time(stages: list[dict], total_minutes: int) -> list[dict]:
    """校验时间分配总和，必要时按比例缩放"""
    durations = [int(s.get("duration_min", 0)) for s in stages]
    actual_total = sum(durations)
    if actual_total == 0:
        # 兜底：平均分配
        avg = total_minutes // len(stages) if stages else 0
        for s in stages:
            s["duration_min"] = avg
        return stages
    if actual_total != total_minutes:
        # 按比例缩放
        scale = total_minutes / actual_total
        new_durations = [max(1, round(d * scale)) for d in durations]
        # 修正取整误差
        diff = total_minutes - sum(new_durations)
        if diff != 0 and new_durations:
            new_durations[-1] += diff
        for s, d in zip(stages, new_durations):
            s["duration_min"] = d
    return stages


async def generate_lesson(
    course_name: str,
    chapter: str,
    knowledge_points: list[dict],
    params: LessonParams,
    textbook_context: str = "",
) -> LessonPlan:
    """基于知识点生成六阶段教案

    Args:
        textbook_context: 教材原文参考，用于知识点解释时引用教材原文
    """
    llm = get_llm()

    # 参数字典
    params_dict = {
        "total_minutes": params.total_minutes,
        "intro_ratio": params.intro_ratio,
        "interact_ratio": params.interact_ratio,
        "intro_style": params.intro_style,
        "language_style": params.language_style,
        "case_density": params.case_density,
        "interact_frequency": params.interact_frequency,
        "difficulty_level": params.difficulty_level,
        "homework_layers": params.homework_layers,
        "include_board_design": params.include_board_design,
    }

    user_prompt = LESSON_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        knowledge_json=json.dumps(knowledge_points, ensure_ascii=False, indent=2),
        textbook_context=textbook_context or "（暂无教材原文参考，请基于知识点内容生成）",
        params_json=json.dumps(params_dict, ensure_ascii=False, indent=2),
    )

    data = await llm.chat_json(LESSON_SYSTEM, user_prompt, temperature=0.7)

    # 后处理：校验时间总和
    stages_raw = data.get("stages", [])
    if stages_raw:
        stages_raw = _validate_and_balance_time(stages_raw, params.total_minutes)

    stages: list[LessonStage] = []
    for s in stages_raw:
        stages.append(
            LessonStage(
                name=str(s.get("name", "")).strip(),
                duration_min=int(s.get("duration_min", 0)),
                teacher_activity=str(s.get("teacher_activity", "")).strip(),
                student_activity=str(s.get("student_activity", "")).strip(),
                design_intent=str(s.get("design_intent", "")).strip(),
                content=str(s.get("content", "")).strip(),
            )
        )

    # 作业分层处理
    homework = list(data.get("homework", []))
    if params.homework_layers == 0:
        homework = homework[:1] if homework else []
    elif params.homework_layers == 2:
        homework = homework[:2] if homework else []
    # 3层保留全部

    return LessonPlan(
        course_name=data.get("course_name", course_name),
        chapter=data.get("chapter", chapter),
        total_minutes=int(data.get("total_minutes", params.total_minutes)),
        teaching_object=data.get("teaching_object", ""),
        teacher_name=data.get("teacher_name", ""),
        knowledge_goal=str(data.get("knowledge_goal", "")).strip(),
        ability_goal=str(data.get("ability_goal", "")).strip(),
        value_goal=str(data.get("value_goal", "")).strip(),
        key_points=list(data.get("key_points", [])),
        difficult_points=list(data.get("difficult_points", [])),
        difficult_strategy=str(data.get("difficult_strategy", "")).strip(),
        stages=stages,
        board_design=data.get("board_design") if params.include_board_design else None,
        homework=homework,
        reflection=str(data.get("reflection", "（课后填写）")),
    )
