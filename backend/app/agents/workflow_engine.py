"""AI 智能体工作流编排引擎"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..agents.chat_agent import modify_lesson
from ..agents.knowledge_agent import chunked_extract_knowledge, extract_knowledge, organize_knowledge_into_chapters
from ..agents.lesson_agent import generate_lesson
from ..agents.lesson_agent_addie import generate_lesson_with_addie
from ..agents.material_evaluator import evaluate_lesson_independent
from ..agents.ppt_agent import generate_ppt_content
from ..agents.smart_extract_agent import smart_extract
from ..models.schemas import LessonParams
from ..storage.db import (
    LessonORM,
    WorkflowExecutionORM,
    WorkflowORM,
    WorkflowStepExecutionORM,
    WorkflowStepORM,
    get_session,
)

logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    "extract_knowledge": {
        "func": extract_knowledge,
        "label": "提取知识点",
        "color": "#3b82f6",
        "inputs": {"course_name": "str", "chapter": "str", "text": "str", "subject": "Optional[str]"},
        "outputs": ["knowledge_points", "summary"],
    },
    "smart_extract": {
        "func": smart_extract,
        "label": "智能提取",
        "color": "#8b5cf6",
        "inputs": {"course_name": "str", "filenames": "str", "text": "str", "subject": "Optional[str]"},
        "outputs": ["chapters"],
    },
    "generate_lesson": {
        "func": generate_lesson,
        "label": "生成教案",
        "color": "#10b981",
        "inputs": {"course_name": "str", "chapter": "str", "knowledge_points": "list", "params": "LessonParams", "textbook_context": "str", "subject": "Optional[str]"},
        "outputs": ["lesson_plan"],
    },
    "generate_lesson_addie": {
        "func": generate_lesson_with_addie,
        "label": "ADDIE生成教案",
        "color": "#059669",
        "inputs": {"course_name": "str", "chapter": "str", "knowledge_points": "list", "params": "LessonParams", "textbook_context": "str", "subject": "Optional[str]"},
        "outputs": ["lesson_plan", "addie_meta"],
    },
    "evaluate_lesson": {
        "func": evaluate_lesson_independent,
        "label": "评估教案",
        "color": "#f59e0b",
        "inputs": {"course_name": "str", "chapter": "str", "lesson_dict": "dict", "knowledge_points": "list", "subject": "Optional[str]"},
        "outputs": ["scores", "overall_score", "top_issues", "chair_validation", "student_validation"],
    },
    "generate_ppt": {
        "func": generate_ppt_content,
        "label": "生成PPT",
        "color": "#ef4444",
        "inputs": {"plan": "LessonPlan", "knowledge_points": "list", "style": "str", "content_density": "str", "image_style": "str", "style_custom": "str", "textbook_context": "str", "subject": "Optional[str]"},
        "outputs": ["slides", "total_slides", "style_used"],
    },
    "chat_modify": {
        "func": modify_lesson,
        "label": "对话修改",
        "color": "#ec4899",
        "inputs": {"course_name": "str", "chapter": "str", "current_plan": "LessonPlan", "user_message": "str"},
        "outputs": ["plan", "type"],
    },
}


def _resolve_input_mapping(input_mapping: dict, step_outputs: dict[str, dict], extra_params: dict) -> dict:
    """解析输入映射，将 {{step_id.output_key}} 替换为实际值"""
    resolved = {}
    for key, value_template in input_mapping.items():
        if isinstance(value_template, str):
            match = re.match(r"\{\{(\w+)\.(\w+)\}\}", value_template)
            if match:
                source_step_id = match.group(1)
                output_key = match.group(2)
                if source_step_id == "params":
                    resolved[key] = extra_params.get(output_key)
                elif source_step_id in step_outputs:
                    resolved[key] = step_outputs[source_step_id].get(output_key)
                else:
                    resolved[key] = value_template
            else:
                resolved[key] = value_template
        else:
            resolved[key] = value_template
    return resolved


async def _execute_agent_step(
    agent_type: str,
    resolved_inputs: dict,
    db: AsyncSession,
) -> dict:
    """执行单个 Agent 步骤"""
    agent_info = AGENT_REGISTRY.get(agent_type)
    if not agent_info:
        raise ValueError(f"未知的 Agent 类型: {agent_type}")

    func = agent_info["func"]
    kwargs = {}

    for param_name, param_type in agent_info["inputs"].items():
        if param_name in resolved_inputs:
            value = resolved_inputs[param_name]
            if param_type == "LessonParams" and isinstance(value, dict):
                value = LessonParams(**value)
            kwargs[param_name] = value

    if agent_type == "generate_lesson_addie":
        result = await func(**kwargs, progress_callback=None)
        if isinstance(result, tuple):
            lesson_dict, addie_meta = result
            return {"lesson_plan": lesson_dict, "addie_meta": addie_meta}
    elif agent_type == "generate_lesson":
        result = await func(**kwargs)
        return {"lesson_plan": result.model_dump() if hasattr(result, "model_dump") else result}
    elif agent_type == "evaluate_lesson":
        result = await func(**kwargs)
        return result
    elif agent_type == "generate_ppt":
        result = await func(**kwargs)
        return result
    elif agent_type == "chat_modify":
        result = await func(**kwargs)
        return result
    elif agent_type == "extract_knowledge":
        result = await func(**kwargs)
        return {"knowledge_points": [p.model_dump() if hasattr(p, "model_dump") else p for p in result.points], "summary": result.summary}
    elif agent_type == "smart_extract":
        result = await func(**kwargs)
        return {"chapters": result}
    else:
        result = await func(**kwargs)
        return {"result": result}


async def execute_workflow(
    workflow_id: int,
    course_id: Optional[int] = None,
    lesson_id: Optional[int] = None,
    extra_params: dict = None,
) -> WorkflowExecutionORM:
    """执行完整工作流"""
    if extra_params is None:
        extra_params = {}

    async for db in get_session():
        result = await db.execute(
            select(WorkflowORM).options(selectinload(WorkflowORM.steps)).where(WorkflowORM.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")

        if course_id:
            extra_params["course_id"] = course_id
        if lesson_id:
            extra_params["lesson_id"] = lesson_id
            lesson_result = await db.execute(select(LessonORM).where(LessonORM.id == lesson_id))
            lesson = lesson_result.scalar_one_or_none()
            if lesson:
                extra_params["course_name"] = lesson.course_name or ""
                extra_params["chapter"] = lesson.chapter or ""

        execution = WorkflowExecutionORM(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        step_outputs: dict[str, dict] = {}
        all_success = True
        accumulated_error = ""

        for step in workflow.steps:
            step_exec = WorkflowStepExecutionORM(
                execution_id=execution.id,
                step_id=step.id,
                sort_order=step.sort_order,
                agent_type=step.agent_type,
                label=step.label or AGENT_REGISTRY.get(step.agent_type, {}).get("label", step.agent_type),
                status="running",
                started_at=datetime.utcnow(),
            )
            db.add(step_exec)
            await db.commit()
            await db.refresh(step_exec)

            resolved_inputs = {}
            try:
                input_mapping = step.input_mapping or {}
                resolved_inputs = _resolve_input_mapping(input_mapping, step_outputs, extra_params)

                step_config = step.config_json or {}
                resolved_inputs.update({k: v for k, v in step_config.items() if k not in resolved_inputs and v != ""})

                output = await _execute_agent_step(step.agent_type, resolved_inputs, db)

                step_exec.status = "completed"
                step_exec.completed_at = datetime.utcnow()
                step_exec.input_json = resolved_inputs
                step_exec.output_json = output
                step_outputs[str(step.id)] = output

            except Exception as e:
                logger.error(f"工作流步骤 {step.id} ({step.agent_type}) 执行失败: {e}")
                step_exec.status = "failed"
                step_exec.completed_at = datetime.utcnow()
                step_exec.error = str(e)
                step_exec.input_json = resolved_inputs
                all_success = False
                accumulated_error = f"步骤 {step.sort_order + 1} ({step.agent_type}) 失败: {e}"
                break

            await db.commit()

        execution.status = "completed" if all_success else "failed"
        execution.completed_at = datetime.utcnow()
        if accumulated_error:
            execution.error = accumulated_error
        execution.result_json = step_outputs
        await db.commit()
        await db.refresh(execution)

        return execution