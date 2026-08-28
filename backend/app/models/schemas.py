"""Pydantic 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============ 课程 ============
# 支持的学科列表(对应 backend/app/core/domains/*.md)
SUPPORTED_SUBJECTS = [
    "math", "chinese", "english", "physics", "chemistry",
    "biology", "history", "geography", "politics", "it", "other",
]


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    major: Optional[str] = Field(None, description="所属专业/院系")
    description: Optional[str] = None
    subject: Optional[str] = Field(None, description="学科标识: math/chinese/english/physics 等")


class CourseUpdate(BaseModel):
    """更新课程(全部字段可选)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    major: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = Field(None, description="学科标识")


class CourseOut(BaseModel):
    id: int
    name: str
    major: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    created_at: datetime


# ============ 教材资源 ============
# 六类枚举：syllabus(课程标准/大纲)、textbook(教科书)、reference(教参教辅)、
# exercise_book(练习题册)、paper(学术论文)、other(其他)
MaterialType = Literal[
    "syllabus", "textbook", "reference", "exercise_book", "paper", "other"
]
# 向后兼容：旧枚举值 -> 新枚举值
LEGACY_MATERIAL_TYPE_MAP = {
    "training_plan": "syllabus",
    "handout": "reference",
}


class MaterialOut(BaseModel):
    id: int
    course_id: int
    filename: str
    material_type: MaterialType
    version_label: str = ""
    is_primary: bool = False
    file_size: int
    content_preview: str
    char_count: int
    created_at: datetime


# ============ 知识点 ============
KnowledgeLayer = Literal["basic", "core", "extension"]


class AccuracyMeta(BaseModel):
    """联网准确性校验结果"""
    accuracy_score: int = Field(3, ge=0, le=5, description="准确性评分0-5")
    accuracy_reason: str = Field("", description="校验说明")
    accuracy_flag: Literal["pass", "warn", "fail"] = Field("warn", description="通过/警告/不通过")


class KnowledgeRelation(BaseModel):
    """知识点间关系"""
    target: str = Field(..., description="关联知识点名称")
    rel_type: str = Field("依赖", description="关系类型: 依赖/支撑/组成/对比/应用")


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
    relationships: list[KnowledgeRelation] = Field(default_factory=list, description="关联关系（含类型）")
    accuracy: Optional[AccuracyMeta] = Field(None, description="联网准确性校验结果")


class KnowledgeExtractionResult(BaseModel):
    """知识点提取结果"""
    chapter: str = Field("", description="章节标题")
    points: list[KnowledgePoint] = Field(default_factory=list)
    summary: str = Field("", description="本章概要")


# ============ 教案 ============
class LessonParams(BaseModel):
    """教案自定义参数"""
    total_minutes: int = Field(90, ge=15, le=180)
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


# ============ 教案模板库 ============
class LessonTemplateCreate(BaseModel):
    """新建教案模板"""
    course_id: Optional[int] = Field(None, description="所属课程ID，None为全局模板")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    structure_json: dict = Field(default_factory=dict)
    is_default: bool = False


class LessonTemplateUpdate(BaseModel):
    """更新教案模板"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    structure_json: Optional[dict] = None
    is_default: Optional[bool] = None


class LessonTemplateOut(BaseModel):
    """教案模板输出"""
    id: int
    course_id: Optional[int]
    name: str
    description: str
    structure_json: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime


# ============ LLM 设置 ============
class LLMSettingsUpdate(BaseModel):
    """LLM设置更新请求"""
    provider: str = Field("qwen", description="供应商：qwen/deepseek/openai/moonshot/zhipu/custom")
    api_key: Optional[str] = Field(None, description="API Key（掩码格式则保留原值）")
    base_url: Optional[str] = Field(None, description="API Base URL")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=256, le=32768)
