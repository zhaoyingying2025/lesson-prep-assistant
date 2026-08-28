"""ADDIE 多智能体审议教案流程

借鉴 reference_projects/instructional_agents/src/ADDIE.py 的多阶段审议思想，
将单次 LLM 教案生成升级为 4 阶段轻量化审议流程：

  Analyze  (学情分析)   → 输出学情摘要、认知障碍点、关键教学策略
  Develop  (教案生成)   → 注入学情摘要后调用原 LESSON_SYSTEM 生成完整教案
  Evaluate (自评审议)   → 4 维度审议(结构/目标/重难点/学情) 输出问题清单
  Refine   (精修)       → 若 Evaluate 标记 needs_refine=true，针对性修订

去其糟粕：
  - 不引入 LaTeX 编译路径(项目用 PPTX)
  - 不引入 copilot 交互式输入(Web 端无 stdin)
  - 不引入课程级多周审议(项目为单节课教案)
  - 不引入复杂 Deliberation 多轮对话(每次 LLM 调用都聚焦明确)
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from ..core.llm import LLMError, get_llm
from ..core.prompts import (
    LESSON_ANALYZE_SYSTEM,
    LESSON_ANALYZE_USER_TEMPLATE,
    LESSON_EVALUATE_SYSTEM,
    LESSON_EVALUATE_USER_TEMPLATE,
    LESSON_REFINE_SYSTEM,
    LESSON_REFINE_USER_TEMPLATE,
    LESSON_SYSTEM,
    LESSON_USER_TEMPLATE,
)
from ..core.prompt_loader import inject_domain_context
from ..models.schemas import LessonParams

logger = logging.getLogger(__name__)


async def _analyze_learner(
    course_name: str,
    chapter: str,
    knowledge_points: list[dict],
    textbook_context: str,
    params_dict: dict,
    subject: Optional[str],
) -> dict:
    """阶段1: Analyze 学情分析 Agent

    输出: {prior_knowledge, cognitive_obstacles, key_strategies, learner_summary}
    """
    llm = get_llm()
    user_prompt = LESSON_ANALYZE_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        knowledge_json=json.dumps(knowledge_points, ensure_ascii=False, indent=2),
        textbook_context=textbook_context or "（暂无教材原文参考）",
        params_json=json.dumps(params_dict, ensure_ascii=False, indent=2),
    )
    system_prompt = inject_domain_context(LESSON_ANALYZE_SYSTEM, subject)
    # 学情分析 temperature 略低，倾向稳定客观判断
    return await llm.chat_json(system_prompt, user_prompt, temperature=0.4)


async def _evaluate_lesson(
    course_name: str,
    chapter: str,
    lesson_json_str: str,
    learner_analysis: dict,
    subject: Optional[str],
) -> dict:
    """阶段3: Evaluate 自评审议 Agent

    输出: {overall_score, issues[], needs_refine, refine_focus}
    """
    llm = get_llm()
    user_prompt = LESSON_EVALUATE_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        lesson_json=lesson_json_str,
        learner_analysis_json=json.dumps(learner_analysis, ensure_ascii=False, indent=2),
    )
    system_prompt = inject_domain_context(LESSON_EVALUATE_SYSTEM, subject)
    # 审议阶段 temperature 低，要求严谨判断
    return await llm.chat_json(system_prompt, user_prompt, temperature=0.3)


async def _refine_lesson(
    course_name: str,
    chapter: str,
    lesson_json_str: str,
    evaluation: dict,
    subject: Optional[str],
) -> dict:
    """阶段4: Refine 精修 Agent

    输入: 原教案 + 问题清单 + 重点修订方向
    输出: 修订后的完整教案 JSON (与原结构一致)
    """
    llm = get_llm()
    issues = evaluation.get("issues", [])
    refine_focus = evaluation.get("refine_focus", "")
    user_prompt = LESSON_REFINE_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        lesson_json=lesson_json_str,
        issues_json=json.dumps(issues, ensure_ascii=False, indent=2),
        refine_focus=refine_focus or "针对所有 error 级问题修订",
    )
    system_prompt = inject_domain_context(LESSON_REFINE_SYSTEM, subject)
    # 精修 temperature 适中，既要稳定又要保留一定创造性
    return await llm.chat_json(system_prompt, user_prompt, temperature=0.5)


async def generate_lesson_with_addie(
    course_name: str,
    chapter: str,
    knowledge_points: list[dict],
    params: LessonParams,
    textbook_context: str = "",
    subject: Optional[str] = None,
    progress_callback=None,
) -> tuple[dict, dict]:
    """ADDIE 多智能体审议教案生成流程

    4 阶段:
      1. Analyze: 学情分析 → learner_analysis
      2. Develop: 注入学情生成完整教案 → raw_lesson_dict
      3. Evaluate: 4 维度自评审议 → evaluation
      4. Refine (条件触发): 若 needs_refine=true 则精修

    Args:
        progress_callback: async 回调 (stage_name: str, payload: dict) -> None
            用于向 UI 推送各阶段中间产物，便于教师观察审议过程

    Returns:
        (final_lesson_dict, addie_meta)
        addie_meta 包含各阶段中间产物，供前端展示审议过程
    """
    from .lesson_agent import _validate_and_balance_time  # 复用时间平衡逻辑

    llm = get_llm()

    # 教案参数字典(与原 generate_lesson 保持一致)
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

    # ---------- 阶段1: Analyze 学情分析 ----------
    if progress_callback:
        await progress_callback("analyze_start", {"chapter": chapter})
    learner_analysis = await _analyze_learner(
        course_name, chapter, knowledge_points, textbook_context, params_dict, subject
    )
    if progress_callback:
        await progress_callback("analyze_done", learner_analysis)

    # ---------- 阶段2: Develop 教案生成(注入学情摘要) ----------
    if progress_callback:
        await progress_callback("develop_start", {"chapter": chapter})
    # 在原 user_prompt 顶部追加学情分析摘要，让教案生成 Agent 参考学情
    learner_summary = learner_analysis.get("learner_summary", "")
    cognitive_obstacles = learner_analysis.get("cognitive_obstacles", [])
    key_strategies = learner_analysis.get("key_strategies", [])
    learner_context_block = ""
    if learner_summary or cognitive_obstacles or key_strategies:
        learner_context_block = (
            "\n===== 本节课学情分析（来自 Analyze 阶段，教案生成时请针对性应对） =====\n"
            f"学情摘要: {learner_summary}\n"
            f"认知障碍点: {json.dumps(cognitive_obstacles, ensure_ascii=False)}\n"
            f"关键教学策略: {json.dumps(key_strategies, ensure_ascii=False)}\n"
            "===== 学情分析结束 =====\n\n"
        )

    user_prompt = LESSON_USER_TEMPLATE.format(
        course_name=course_name,
        chapter=chapter,
        knowledge_json=json.dumps(knowledge_points, ensure_ascii=False, indent=2),
        textbook_context=textbook_context or "（暂无教材原文参考，请基于知识点内容生成）",
        params_json=json.dumps(params_dict, ensure_ascii=False, indent=2),
    )
    # 学情块插入到知识点块之前，让模型在生成 stages 时参考
    user_prompt_with_learner = user_prompt.replace(
        "===== 已提取知识点（含教材页码） =====",
        learner_context_block + "===== 已提取知识点（含教材页码） =====",
    ) if learner_context_block else user_prompt

    system_prompt = inject_domain_context(LESSON_SYSTEM, subject)
    raw_lesson_dict = await llm.chat_json(system_prompt, user_prompt_with_learner, temperature=0.7)

    # 时间平衡(与 fast 模式保持一致)
    stages_raw = raw_lesson_dict.get("stages", [])
    if stages_raw:
        raw_lesson_dict["stages"] = _validate_and_balance_time(stages_raw, params.total_minutes)

    if progress_callback:
        await progress_callback("develop_done", {"total_stages": len(raw_lesson_dict.get("stages", []))})

    # ---------- 阶段3: Evaluate 自评审议 ----------
    if progress_callback:
        await progress_callback("evaluate_start", {})
    # 教案 JSON 字符串化用于审议
    lesson_json_str = json.dumps(raw_lesson_dict, ensure_ascii=False, indent=2)
    try:
        evaluation = await _evaluate_lesson(
            course_name, chapter, lesson_json_str, learner_analysis, subject
        )
    except LLMError as e:
        # 审议失败不阻塞流程，记录错误并跳过 Refine
        logger.warning("ADDIE Evaluate 阶段失败: %s", e)
        evaluation = {
            "overall_score": -1,
            "issues": [],
            "needs_refine": False,
            "refine_focus": "",
            "error": str(e),
        }
    if progress_callback:
        await progress_callback("evaluate_done", evaluation)

    # ---------- 阶段4: Refine 精修(条件触发) ----------
    final_lesson_dict = raw_lesson_dict
    refined = False
    refine_error = None
    if evaluation.get("needs_refine") is True:
        if progress_callback:
            await progress_callback("refine_start", {"refine_focus": evaluation.get("refine_focus", "")})
        try:
            refined_dict = await _refine_lesson(
                course_name, chapter, lesson_json_str, evaluation, subject
            )
            # 精修后再次校验时间平衡
            refined_stages = refined_dict.get("stages", [])
            if refined_stages:
                refined_dict["stages"] = _validate_and_balance_time(refined_stages, params.total_minutes)
            final_lesson_dict = refined_dict
            refined = True
        except LLMError as e:
            logger.warning("ADDIE Refine 阶段失败: %s，保留 Develop 阶段产出", e)
            refine_error = str(e)
        if progress_callback:
            await progress_callback("refine_done", {"refined": refined, "error": refine_error})

    addie_meta = {
        "mode": "addie",
        "learner_analysis": learner_analysis,
        "evaluation": evaluation,
        "refined": refined,
        "refine_error": refine_error,
        "stages_run": ["analyze", "develop", "evaluate"] + (["refine"] if refined else []),
    }

    return final_lesson_dict, addie_meta
