"""Pydantic 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============ 课程 ============
class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    major: Optional[str] = Field(None, description="所属专业/院系")
    description: Optional[str] = None


class CourseOut(BaseModel):
    id: int
    name: str
    major: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


# ============ 教材资源 ============
MaterialType = Literal[
    "textbook", "syllabus", "training_plan", "handout", "paper", "other"
]


class MaterialOut(BaseModel):
    id: int
    course_id: int
    filename: str
    material_type: MaterialType
    file_size: int
    content_preview: str
    char_count: int
    created_at: datetime


# ============ 知识点 ============
KnowledgeLayer = Literal["basic", "core", "extension"]


class KnowledgePoint(BaseModel):
    """知识点结构"""
    name: str = Field(..., description="知识点名称")
    layer: KnowledgeLayer = Field("core", description="层级:基础/核心/拓展")
    definition: str = Field("", description="概念定义/简述")
    source_pages: str = Field("", description="教材页码，如 P23-P25")
    importance: int = Field(3, ge=1, le=5, description="重要度1-5")
    difficulty: int = Field(3, ge=1, le=5, description="难度1-5")
    is_key_point: bool = Field(False, description="是否重点")
    is_difficult: bool = Field(False, description="是否难点")
    is_exam_point: bool = Field(False, description="是否考点")
    prerequisites: list[str] = Field(default_factory=list, description="前置知识点")


class KnowledgeExtractionResult(BaseModel):
    """知识点提取结果"""
    chapter: str = Field("", description="章节标题")
    points: list[KnowledgePoint] = Field(default_factory=list)
    summary: str = Field("", description="本章概要")


# ============ 教案 ============
class LessonParams(BaseModel):
    """教案自定义参数"""
    total_minutes: int = Field(90, ge=30, le=180)
    intro_ratio: float = Field(0.10, ge=0.05, le=0.20, description="导入时间占比")
    interact_ratio: float = Field(0.15, ge=0.05, le=0.30, description="互动占比")
    intro_style: Literal["auto", "scenario", "question", "case", "review", "media"] = "auto"
    language_style: Literal["academic", "plain", "humorous", "concise"] = "plain"
    case_density: Literal["high", "medium", "low"] = "medium"
    interact_frequency: Literal["high", "medium", "low"] = "medium"
    difficulty_level: Literal["lower", "match", "higher"] = "match"
    homework_layers: Literal[0, 2, 3] = 3
    include_board_design: bool = True


class LessonStage(BaseModel):
    """教案单个阶段"""
    name: str
    duration_min: int
    teacher_activity: str
    student_activity: str
    design_intent: str
    content: str = Field("", description="本环节具体内容/讲解要点")


class LessonPlan(BaseModel):
    """完整教案"""
    course_name: str
    chapter: str
    total_minutes: int

    # 教学基本信息
    teaching_object: Optional[str] = None
    teacher_name: Optional[str] = None

    # 三维目标
    knowledge_goal: str
    ability_goal: str
    value_goal: str

    # 重难点
    key_points: list[str]
    difficult_points: list[str]
    difficult_strategy: str

    # 六阶段
    stages: list[LessonStage]

    # 板书设计
    board_design: Optional[str] = None

    # 作业
    homework: list[str] = Field(default_factory=list)

    # 反思预留
    reflection: str = "（课后填写）"

    # 元信息
    source_material_ids: list[int] = Field(default_factory=list)


class LessonOut(BaseModel):
    id: int
    course_id: int
    chapter: str
    title: str
    plan_json: dict
    params_json: dict
    created_at: datetime
    updated_at: datetime


# ============ 对话 ============
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    course_id: int
    message: str
    context: Optional[dict] = None


# ============ 通用 ============
class ApiResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[dict | list] = None


# ============ LLM 设置 ============
class LLMSettingsUpdate(BaseModel):
    """LLM设置更新请求"""
    provider: str = Field("qwen", description="供应商：qwen/deepseek/openai/moonshot/zhipu/custom")
    api_key: Optional[str] = Field(None, description="API Key（掩码格式则保留原值）")
    base_url: Optional[str] = Field(None, description="API Base URL")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=256, le=32768)
