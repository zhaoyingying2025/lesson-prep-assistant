"""课程材料评估系统

借鉴 reference_projects/instructional_agents/src/evaluate.py 的多指标打分 + 双视角评审机制，
针对教案 JSON 做独立质量评估，输出：
  - 6 维度指标打分（每项 1-5 分，含 CoT 思考过程）
  - 双视角评审报告（教务专家 + 学生代表）
  - 总评分 + 改进建议清单

与 lesson_agent_addie 的 Evaluate 阶段区别：
  - ADDIE Evaluate 仅做"是否需要 Refine"的判断（4 大维度+问题清单），用于驱动精修
  - 本系统面向用户最终成品，做更细粒度多指标打分 + 多视角评审，输出可读性强的报告
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from ..core.llm import LLMError, get_llm
from ..core.prompt_loader import inject_domain_context

logger = logging.getLogger(__name__)


# 教案评估的 6 个细粒度指标(借鉴 instructional_agents 的 metrics 字典思想)
LESSON_METRICS = {
    "structure_completeness": "教案六阶段是否齐备、时间总和是否等于课时、各阶段时间分配是否合理",
    "goal_alignment": "三维目标是否覆盖全部知识点、目标是否可观测可衡量",
    "key_difficulty_handling": "重点是否在 stages 中有对应教学活动、难点是否有具体突破策略",
    "learner_match": "教学策略是否符合学情、案例/互动设计是否符合学生认知水平",
    "pedagogy_appropriateness": "教学法选择是否得当（启发式vs讲授式比例）、互动设计是否充分",
    "executability": "教师行为/学生行为描述是否具体可执行、content 是否能直接用于课堂讲授",
}


SCORE_EVALUATOR_SYSTEM = """你是高校教学设计量化评估专家，负责对教案 JSON 进行细粒度多指标打分。

评估流程（Chain-of-Thought）：
1. 先针对每个指标在 THOUGHT 字段简要写出你的判断依据（不超过 80 字）
2. 然后在 SCORE 字段给出 1.0-5.0 的评分（可用小数）
3. 评分参考：5.0 完美 / 4.0 优秀 / 3.0 良好 / 2.0 一般 / 1.0 较差
4. 不要总是给高分，思考如果由你来打磨这份教案需要多少时间，需要大改则降分

严格输出 JSON，不要额外解释。"""

SCORE_EVALUATOR_USER_TEMPLATE = """课程名称：{course_name}
章节：{chapter}

===== 待评估教案 JSON =====
{lesson_json}
===== 教案结束 =====

===== 知识点列表（用于交叉校验目标达成度） =====
{knowledge_json}
===== 知识点结束 =====

请对教案按以下 6 个指标逐一打分：

{metrics_desc}

输出 JSON 格式：
{{
  "scores": [
    {{
      "metric": "structure_completeness",
      "thought": "判断依据(80字内)",
      "score": 1.0-5.0
    }},
    {{
      "metric": "goal_alignment",
      "thought": "...",
      "score": 1.0-5.0
    }},
    ... 共6项 ...
  ],
  "overall_score": 加权平均分(1.0-5.0，保留1位小数),
  "top_issues": ["最突出的3个改进点(简短一句话)"]
}}

要求：
- 6 个指标全部评估，不可遗漏
- overall_score 取 6 项平均
- top_issues 至多 3 条
- 严格输出 JSON，不要额外解释。"""

VALIDATION_CHAIR_SYSTEM = """你是高校系主任/教学督导，负责从教学质量保障视角评审教案。

评审关注点：
- 学术严谨性与课程标准一致性
- 教育设计质量（教学目标-活动-评估的对齐度）
- 评估有效性与可靠性
- 整体连贯性与结构合理性

请提供详细的评审意见和建设性反馈，使用中文 Markdown 格式。"""

VALIDATION_STUDENT_SYSTEM = """你是高校在校大学生代表，从学生视角评审教案的可学性。

评审关注点：
- 内容清晰度与可理解性
- 学习动力激发与课堂参与度
- 学习支持与引导（学生能否跟上节奏）
- 实用性与可应用性
- 易用性（教案节奏对学生是否友好）

请提供详细反馈，使用中文 Markdown 格式。"""

VALIDATION_USER_TEMPLATE = """课程名称：{course_name}
章节：{chapter}

===== 待评审教案 =====
{lesson_json}
===== 教案结束 =====

请从你的角色视角评审该教案，提供：
1. 总体评价（80-150字）
2. 优点（3-5 条）
3. 待改进之处（3-5 条）
4. 具体建议（3-5 条可执行建议）
5. 1-5 星级评定（1=很差，5=完美）

输出 JSON 格式：
{{
  "overall_assessment": "总体评价",
  "strengths": ["优点1", "优点2", "..."],
  "improvements": ["改进点1", "改进点2", "..."],
  "recommendations": ["建议1", "建议2", "..."],
  "rating": 1-5,
  "summary": "一句话总结(30字内)"
}}

要求：严格输出 JSON，不要额外解释。"""


async def evaluate_lesson_independent(
    course_name: str,
    chapter: str,
    lesson_dict: dict,
    knowledge_points: list[dict],
    subject: Optional[str] = None,
) -> dict:
    """对教案 JSON 做独立质量评估

    Args:
        lesson_dict: 教案 dict (含 stages / 三维目标 / 重难点 等)
        knowledge_points: 本节知识点列表（用于交叉校验目标达成度）

    Returns:
        {
          "scores": [{metric, thought, score}, ...],   # 6 指标打分
          "overall_score": float,
          "top_issues": [str, ...],
          "chair_validation": {总体评价/优点/改进/建议/星级/总结},
          "student_validation": {...},
          "error": Optional[str]  # 任一 Agent 失败时填错误信息
        }
    """
    llm = get_llm()
    lesson_json_str = json.dumps(lesson_dict, ensure_ascii=False, indent=2)
    knowledge_json_str = json.dumps(knowledge_points, ensure_ascii=False, indent=2)
    metrics_desc = "\n".join(
        f"- {k}: {v}" for k, v in LESSON_METRICS.items()
    )

    # ---------- 1. 多指标打分 Agent ----------
    score_user = SCORE_EVALUATOR_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        lesson_json=lesson_json_str,
        knowledge_json=knowledge_json_str,
        metrics_desc=metrics_desc,
    )
    score_system = inject_domain_context(SCORE_EVALUATOR_SYSTEM, subject)
    try:
        score_result = await llm.chat_json(score_system, score_user, temperature=0.3)
    except LLMError as e:
        logger.warning("多指标打分 Agent 失败: %s", e)
        return {
            "scores": [],
            "overall_score": 0.0,
            "top_issues": [],
            "error": f"打分 Agent 失败: {e}",
        }

    # ---------- 2. 教务专家视角评审 ----------
    valid_user = VALIDATION_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        lesson_json=lesson_json_str,
    )
    chair_system = inject_domain_context(VALIDATION_CHAIR_SYSTEM, subject)
    try:
        chair_validation = await llm.chat_json(chair_system, valid_user, temperature=0.5)
    except LLMError as e:
        logger.warning("教务专家评审 Agent 失败: %s", e)
        chair_validation = {"error": str(e), "summary": "评审失败"}

    # ---------- 3. 学生代表视角评审 ----------
    student_system = inject_domain_context(VALIDATION_STUDENT_SYSTEM, subject)
    try:
        student_validation = await llm.chat_json(student_system, valid_user, temperature=0.6)
    except LLMError as e:
        logger.warning("学生代表评审 Agent 失败: %s", e)
        student_validation = {"error": str(e), "summary": "评审失败"}

    return {
        "scores": score_result.get("scores", []),
        "overall_score": float(score_result.get("overall_score", 0.0)),
        "top_issues": score_result.get("top_issues", []),
        "chair_validation": chair_validation,
        "student_validation": student_validation,
    }
