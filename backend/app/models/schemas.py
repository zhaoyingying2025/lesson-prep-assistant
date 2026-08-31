"""Pydantic 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    chapter_id: Optional[int] = None


# ============ 通用 ============
class ApiResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Any = None


# ============ 教学日历 ============
class ScheduleCreate(BaseModel):
    """创建教学日历条目"""
    course_id: int
    chapter_id: Optional[int] = None
    lesson_id: Optional[int] = None
    week_number: int = Field(..., ge=1, le=20, description="教学周次 1-20")
    day_of_week: int = Field(..., ge=1, le=5, description="星期 1=周一~5=周五")
    period: str = ""
    content: str = ""
    sort_order: int = 0


class ScheduleUpdate(BaseModel):
    """更新教学日历条目"""
    chapter_id: Optional[int] = None
    lesson_id: Optional[int] = None
    week_number: Optional[int] = Field(None, ge=1, le=20)
    day_of_week: Optional[int] = Field(None, ge=1, le=5)
    period: Optional[str] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None


class ScheduleOut(BaseModel):
    """教学日历条目输出"""
    id: int
    course_id: int
    chapter_id: Optional[int] = None
    lesson_id: Optional[int] = None
    week_number: int
    day_of_week: int
    period: str
    content: str
    sort_order: int
    chapter_name: str = ""
    lesson_title: str = ""
    created_at: datetime
    updated_at: datetime


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


# ============ 多人协作备课 ============
class ShareCodeOut(BaseModel):
    """分享码输出"""
    id: int
    lesson_id: int
    code: str
    created_at: datetime


class ShareCodeCreate(BaseModel):
    """创建分享码请求"""
    pass


class ShareCodeDelete(BaseModel):
    """删除分享码请求"""
    code: str


class CommentCreate(BaseModel):
    """创建评论请求"""
    author: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=1000)


class CommentOut(BaseModel):
    """评论输出"""
    id: int
    lesson_id: int
    author: str
    content: str
    created_at: datetime


class ApprovalStatusOut(BaseModel):
    """审批状态输出"""
    status: str
    submitted_by: str
    submitted_at: Optional[datetime] = None
    reviewed_by: str
    reviewed_at: Optional[datetime] = None
    review_comment: str


class ApprovalSubmit(BaseModel):
    """提交审批请求"""
    submitted_by: str = Field(..., min_length=1, max_length=50)


class ApprovalReview(BaseModel):
    """审批请求"""
    reviewer: str = Field(..., min_length=1, max_length=50)
    comment: str = ""
    approved: bool


# ============ 教学资源市场 ============
class MarketResourceCreate(BaseModel):
    """上传资源到市场"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    category: str = Field(..., pattern="^(template|lesson|courseware)$")
    resource_type: str = ""
    content_json: dict = Field(default_factory=dict)
    author: str = Field(..., min_length=1, max_length=100)
    tags: str = ""
    source_course_id: Optional[int] = None
    source_lesson_id: Optional[int] = None


class MarketResourceOut(BaseModel):
    """资源市场输出"""
    id: int
    title: str
    description: str
    category: str
    resource_type: str
    content_json: dict
    author: str
    rating: float = 0
    rating_count: int = 0
    download_count: int = 0
    tags: str
    created_at: datetime
    updated_at: datetime


class MarketResourceRate(BaseModel):
    """资源评分"""
    rating: int = Field(..., ge=1, le=5)


# ============ AI 智能体工作流编排 ============
class WorkflowStepCreate(BaseModel):
    """工作流步骤创建/更新"""
    agent_type: str = Field(..., pattern="^(extract_knowledge|smart_extract|generate_lesson|generate_lesson_addie|evaluate_lesson|generate_ppt|chat_modify)$")
    label: str = ""
    sort_order: int = 0
    position_x: int = 0
    position_y: int = 0
    config_json: dict = Field(default_factory=dict)
    input_mapping: dict = Field(default_factory=dict)


class WorkflowCreate(BaseModel):
    """创建工作流"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    course_id: Optional[int] = None
    steps: list[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    steps: Optional[list[WorkflowStepCreate]] = None


class WorkflowStepOut(BaseModel):
    """工作流步骤输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    workflow_id: int
    sort_order: int
    agent_type: str
    label: str
    config_json: dict
    position_x: int
    position_y: int
    input_mapping: dict
    created_at: datetime


class WorkflowOut(BaseModel):
    """工作流输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    course_id: Optional[int] = None
    steps: list[WorkflowStepOut] = []
    created_at: datetime
    updated_at: datetime


class WorkflowStepExecutionOut(BaseModel):
    """工作流步骤执行输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    execution_id: int
    step_id: Optional[int] = None
    sort_order: int
    agent_type: str
    label: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_json: dict
    output_json: dict
    error: str


class WorkflowExecutionOut(BaseModel):
    """工作流执行输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    workflow_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: str
    result_json: dict
    created_at: datetime
    step_executions: list[WorkflowStepExecutionOut] = []


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    extra_params: dict = Field(default_factory=dict)
