"""内容校验器（借鉴 AgentCourseAssistant/shared/validators.py）

对生成的教案/PPT 内容做后置校验，包括：
- 公式格式校验（LaTeX 闭合性/转义）
- 超纲关键词检测（可配置，默认空集，避免误报）
- 结构完整性校验（必需字段缺失）
- 全角/半角括号检查（warning）

校验结果分两类：
- errors：阻塞级问题（如必需字段缺失、超纲关键词）
- warnings：提示级问题（如全角括号、公式未闭合）

设计原则（"取其精华,去其糟粕"）：
- 不强制中断生成流程：校验失败时返回结构化结果，由调用方决定是否重试
- 默认超纲关键词库为空，避免对高校教学场景误报（原项目针对K12）
- 保留可扩展接口：支持自定义 forbidden_keywords 与公式库
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass
class ValidationIssue:
    """单个校验问题"""
    rule: str          # 规则名: format_check / structure_check / forbidden_check / formula_check
    severity: str      # error / warning
    message: str       # 问题描述


@dataclass
class ValidationResult:
    """校验结果"""
    is_valid: bool = True                       # 是否通过（无 error）
    issues: list[ValidationIssue] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)  # 统计信息

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": [i.message for i in self.issues if i.severity == "error"],
            "warnings": [i.message for i in self.issues if i.severity == "warning"],
            "stats": self.stats,
        }


# 必需教案字段（缺失视为 error）
REQUIRED_LESSON_FIELDS = (
    "course_name", "chapter", "total_minutes",
    "knowledge_goal", "ability_goal", "value_goal",
    "key_points", "difficult_points", "stages",
)

# 必需 PPT 字段
REQUIRED_PPT_FIELDS = ("style_used", "total_slides", "slides")

# 教案阶段必需子字段
REQUIRED_STAGE_FIELDS = ("name", "duration_min", "teacher_activity", "student_activity")


class ContentValidator:
    """内容校验器

    Args:
        forbidden_keywords: 自定义超纲关键词（默认为空集，避免高校场景误报）
        formulas: 自定义公式库（暂未使用，保留扩展接口）
    """

    def __init__(
        self,
        forbidden_keywords: Iterable[str] | None = None,
        formulas: dict[str, str] | None = None,
    ):
        self._forbidden_keywords = set(forbidden_keywords or [])
        self._formulas = dict(formulas or {})

    def validate_lesson(self, plan_dict: dict) -> ValidationResult:
        """校验教案"""
        result = ValidationResult()
        # 1. 结构完整性
        self._check_structure(plan_dict, REQUIRED_LESSON_FIELDS, result, kind="lesson")
        # 2. stages 子结构
        stages = plan_dict.get("stages") or []
        if isinstance(stages, list):
            for idx, st in enumerate(stages):
                if not isinstance(st, dict):
                    result.issues.append(ValidationIssue(
                        "structure_check", "error",
                        f"阶段 #{idx+1} 不是字典结构"
                    ))
                    continue
                for f in REQUIRED_STAGE_FIELDS:
                    if not str(st.get(f, "")).strip():
                        result.issues.append(ValidationIssue(
                            "structure_check", "warning",
                            f"阶段「{st.get('name', f'#{idx+1}')}」缺少字段: {f}"
                        ))
        # 3. 全角括号 + LaTeX（针对字符串化后的内容）
        content_str = json.dumps(plan_dict, ensure_ascii=False)
        self._check_format(content_str, result)
        self._check_forbidden(content_str, result)
        self._check_formulas(content_str, result)
        self._finalize(result)
        return result

    def validate_ppt(self, ppt_dict: dict) -> ValidationResult:
        """校验 PPT 内容"""
        result = ValidationResult()
        self._check_structure(ppt_dict, REQUIRED_PPT_FIELDS, result, kind="ppt")
        slides = ppt_dict.get("slides") or []
        if isinstance(slides, list):
            if len(slides) == 0:
                result.issues.append(ValidationIssue(
                    "structure_check", "error", "PPT 没有 slide"
                ))
            for idx, sl in enumerate(slides):
                if not isinstance(sl, dict):
                    result.issues.append(ValidationIssue(
                        "structure_check", "error",
                        f"Slide #{idx+1} 不是字典结构"
                    ))
                    continue
                # slide 至少要有 title 或 content
                title = str(sl.get("title", "")).strip()
                content = str(sl.get("content", "")).strip()
                if not title and not content:
                    result.issues.append(ValidationIssue(
                        "structure_check", "warning",
                        f"Slide #{idx+1} 标题和内容均为空"
                    ))
        content_str = json.dumps(ppt_dict, ensure_ascii=False)
        self._check_format(content_str, result)
        self._check_forbidden(content_str, result)
        self._check_formulas(content_str, result)
        self._finalize(result)
        return result

    # ============ 内部规则 ============

    def _check_structure(
        self,
        data: dict,
        required_fields: tuple[str, ...],
        result: ValidationResult,
        kind: str = "lesson",
    ) -> None:
        for f in required_fields:
            v = data.get(f)
            if v is None:
                result.issues.append(ValidationIssue(
                    "structure_check", "error",
                    f"{kind} 缺少必需字段: {f}"
                ))
            elif isinstance(v, (list, str)) and len(v) == 0:
                result.issues.append(ValidationIssue(
                    "structure_check", "warning",
                    f"{kind} 字段「{f}」为空"
                ))

    def _check_format(self, content_str: str, result: ValidationResult) -> None:
        # 全角括号
        if "（" in content_str or "）" in content_str:
            cnt = content_str.count("（") + content_str.count("）")
            result.issues.append(ValidationIssue(
                "format_check", "warning",
                f"发现 {cnt} 处全角括号，建议使用半角括号 ()"
            ))

    def _check_forbidden(self, content_str: str, result: ValidationResult) -> None:
        if not self._forbidden_keywords:
            return
        found = [kw for kw in self._forbidden_keywords if kw in content_str]
        if found:
            result.issues.append(ValidationIssue(
                "forbidden_check", "error",
                f"发现超纲/违规关键词: {', '.join(found)}"
            ))

    def _check_formulas(self, content_str: str, result: ValidationResult) -> None:
        # 提取 LaTeX 公式 ($$...$$, $...$, \begin{equation*}...)
        latex_patterns = [
            (r'\$\$([^$]+)\$\$', "block"),
            (r'(?<!\\)\$([^$\n]+)\$', "inline"),
        ]
        for pattern, kind in latex_patterns:
            for m in re.finditer(pattern, content_str):
                formula = m.group(1).strip()
                if not formula:
                    continue
                if formula.count("{") != formula.count("}"):
                    result.issues.append(ValidationIssue(
                        "formula_check", "warning",
                        f"{kind}公式可能未闭合: {formula[:60]}..."
                    ))
                if re.search(r'(?<!\\)[%#&]', formula):
                    result.issues.append(ValidationIssue(
                        "formula_check", "warning",
                        f"{kind}公式可能包含未转义字符: {formula[:60]}..."
                    ))

    def _finalize(self, result: ValidationResult) -> None:
        result.is_valid = not any(i.severity == "error" for i in result.issues)
        result.stats = {
            "errors": sum(1 for i in result.issues if i.severity == "error"),
            "warnings": sum(1 for i in result.issues if i.severity == "warning"),
        }


# 模块级单例（默认空关键词集，避免高校场景误报）
_default_validator = ContentValidator()


def validate_lesson(plan_dict: dict) -> ValidationResult:
    """便捷函数：校验教案"""
    return _default_validator.validate_lesson(plan_dict)


def validate_ppt(ppt_dict: dict) -> ValidationResult:
    """便捷函数：校验 PPT"""
    return _default_validator.validate_ppt(ppt_dict)
