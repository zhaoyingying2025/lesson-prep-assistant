"""Markdown 导出"""
from __future__ import annotations

from ..models.schemas import LessonPlan


def export_markdown(plan: LessonPlan) -> str:
    """将教案导出为 Markdown"""
    lines: list[str] = []

    # 标题
    lines.append(f"# {plan.course_name} · {plan.chapter} 教案")
    lines.append("")
    lines.append(f"> 总课时：{plan.total_minutes} 分钟")
    lines.append("")

    # 基本信息
    lines.append("## 一、教学基本信息")
    lines.append("")
    lines.append(f"- **课程名称**：{plan.course_name}")
    lines.append(f"- **授课章节**：{plan.chapter}")
    if plan.teaching_object:
        lines.append(f"- **授课对象**：{plan.teaching_object}")
    if plan.teacher_name:
        lines.append(f"- **授课教师**：{plan.teacher_name}")
    lines.append(f"- **课时安排**：{plan.total_minutes} 分钟")
    lines.append("")

    # 三维目标
    lines.append("## 二、教学目标")
    lines.append("")
    lines.append(f"### 1. 知识目标")
    lines.append(plan.knowledge_goal)
    lines.append("")
    lines.append(f"### 2. 能力目标")
    lines.append(plan.ability_goal)
    lines.append("")
    lines.append(f"### 3. 素质/思政目标")
    lines.append(plan.value_goal)
    lines.append("")

    # 重难点
    lines.append("## 三、教学重难点")
    lines.append("")
    if plan.key_points:
        lines.append("### 教学重点")
        for i, kp in enumerate(plan.key_points, 1):
            lines.append(f"{i}. {kp}")
        lines.append("")
    if plan.difficult_points:
        lines.append("### 教学难点")
        for i, dp in enumerate(plan.difficult_points, 1):
            lines.append(f"{i}. {dp}")
        lines.append("")
    if plan.difficult_strategy:
        lines.append("### 难点突破策略")
        lines.append(plan.difficult_strategy)
        lines.append("")

    # 教学过程（表格形式）
    lines.append("## 四、教学过程设计")
    lines.append("")
    if plan.stages:
        lines.append("| 阶段 | 时长(分钟) | 教师行为 | 学生行为 | 设计意图 | 教学内容 |")
        lines.append("|------|-----------|---------|---------|---------|---------|")
        for i, stage in enumerate(plan.stages, 1):
            def cell(s):
                """转义表格中的特殊字符，换行用 <br> 替代"""
                if not s:
                    return "-"
                return str(s).replace("|", "\\|").replace("\n", "<br>").strip()
            lines.append(
                f"| {i}. {cell(stage.name)} | {stage.duration_min} | "
                f"{cell(stage.teacher_activity)} | {cell(stage.student_activity)} | "
                f"{cell(stage.design_intent)} | {cell(stage.content)} |"
            )
        lines.append("")

    # 板书设计
    if plan.board_design:
        lines.append("## 五、板书设计")
        lines.append("")
        lines.append("```")
        lines.append(plan.board_design)
        lines.append("```")
        lines.append("")

    # 作业
    if plan.homework:
        lines.append("## 六、课后作业")
        lines.append("")
        for i, hw in enumerate(plan.homework, 1):
            lines.append(f"{i}. {hw}")
        lines.append("")

    # 教学反思
    lines.append("## 七、教学反思")
    lines.append("")
    lines.append(plan.reflection or "（课后填写）")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本教案由备课助手智能体辅助生成，仅供教学参考。*")

    return "\n".join(lines)
