"""SQLite数据库（SQLAlchemy 2.0 异步）"""
from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from ..config import settings


class Base(DeclarativeBase):
    pass


class CourseORM(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    major = Column(String(100))
    description = Column(Text)
    # 学科标识(用于注入学科领域规则): math/chinese/english/physics/chemistry/biology/history/geography/politics/it/other
    subject = Column(String(50), default="")
    # 内容缓存：教材内容哈希值，用于增量提取判断
    content_hash = Column(String(64), default="", comment="教材内容 SHA256 哈希，用于增量提取缓存")
    last_extracted_at = Column(DateTime, nullable=True, comment="上次知识点提取时间")
    created_at = Column(DateTime, default=datetime.utcnow)

    materials = relationship("MaterialORM", back_populates="course", cascade="all,delete-orphan")
    lessons = relationship("LessonORM", back_populates="course", cascade="all,delete-orphan")
    messages = relationship("ChatMessageORM", back_populates="course", cascade="all,delete-orphan")
    chapters = relationship("ChapterORM", back_populates="course", cascade="all,delete-orphan", order_by="ChapterORM.sort_order")
    knowledge_points = relationship("KnowledgePointORM", back_populates="course", cascade="all,delete-orphan", order_by="KnowledgePointORM.sort_order")
    ppt_records = relationship("PptRecordORM", back_populates="course", cascade="all,delete-orphan")
    lesson_templates = relationship("LessonTemplateORM", back_populates="course", cascade="all,delete-orphan")


class MaterialORM(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    material_type = Column(String(50), default="other")
    # 教材版本标签（如：人教版/高教版/清华版/通用），便于多教材版本管理
    version_label = Column(String(100), default="")
    is_primary = Column(Boolean, default=False, comment="是否主教材(同课程下多本教材时，主教材用于AI生成优先检索)")
    file_size = Column(Integer, default=0)
    content_text = Column(Text, default="")
    content_preview = Column(Text, default="")
    char_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("CourseORM", back_populates="materials")


class LessonORM(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)  # 关联到章节树节点
    chapter = Column(String(200), nullable=False)  # 冗余：章节名称快照
    title = Column(String(200), default="")
    plan_json = Column(JSON, default=dict)
    params_json = Column(JSON, default=dict)
    source_material_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("CourseORM", back_populates="lessons")


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("CourseORM", back_populates="messages")


class ChapterORM(Base):
    """章节树（支持多级嵌套：章/节/知识点等）"""
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True)  # null=顶级
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("CourseORM", back_populates="chapters")
    parent = relationship("ChapterORM", remote_side=[id], back_populates="children")
    children = relationship(
        "ChapterORM",
        back_populates="parent",
        cascade="all,delete-orphan",
        order_by="ChapterORM.sort_order",
    )


class PptRecordORM(Base):
    """PPT生成/上传记录"""
    __tablename__ = "ppt_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    chapter = Column(String(200), default="")
    title = Column(String(200), default="")
    style = Column(String(50), default="cyan_ink")
    content_density = Column(String(20), default="moderate")
    image_style = Column(String(20), default="icons")
    style_custom = Column(Text, default="")
    slide_count = Column(Integer, default=0)
    slide_data = Column(JSON, default=dict)  # 存储LLM生成的幻灯片结构
    source = Column(String(20), default="ai")  # 'ai' 或 'upload'
    stored_path = Column(String(500), default="")  # 上传文件路径
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("CourseORM", back_populates="ppt_records")


class KnowledgePointORM(Base):
    """知识点（持久化，支持手动编辑与跨教案复用）

    layer: basic / core / extension（基础/核心/拓展）
    is_key_point / is_difficult / is_exam_point: 重点/难点/考点 标签
    source_pages: 知识点在教材中的页码，如 "P23-P25" 或 "P23,P25,P27"
    """
    __tablename__ = "knowledge_points"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    chapter = Column(String(200), default="")  # 冗余：章节名称快照
    name = Column(String(200), nullable=False)
    definition = Column(Text, default="")
    source_pages = Column(String(100), default="")  # 教材页码，如 "P23-P25"
    layer = Column(String(20), default="basic")  # basic / core / extension
    importance = Column(Integer, default=3)       # 1-5 重要度
    difficulty = Column(Integer, default=3)       # 1-5 难度
    is_key_point = Column(Integer, default=0)      # 0/1
    is_difficult = Column(Integer, default=0)       # 0/1
    is_exam_point = Column(Integer, default=0)      # 0/1
    prerequisites_json = Column(JSON, default=list)  # 前置知识点名称列表
    relationships_json = Column(JSON, default=list)  # 关联关系: [{target, rel_type}]
    accuracy_json = Column(JSON, default=dict)       # 联网校验结果: {score, reason, flag}
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("CourseORM", back_populates="knowledge_points")


class LessonTemplateORM(Base):
    """教案模板库（全局模板 course_id=null，课程私有模板 course_id=课程ID）"""
    __tablename__ = "lesson_templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    structure_json = Column(JSON, default=dict)  # 模板结构定义（表格类型+字段列表+默认值）
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("CourseORM", back_populates="lesson_templates")


class TextbookChunkORM(Base):
    """教材文本块（按页分割，支持全文检索）

    上传教材时自动解析并按页分割存储，用于后续知识点检索和教案生成时快速定位原文。
    """
    __tablename__ = "textbook_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, default=0, nullable=False)
    chunk_text = Column(Text, default="")
    char_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("MaterialORM", backref="chunks")


# ============ 引擎 ============
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.db_path}",
    echo=settings.debug,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# 启用 SQLite 外键约束（SQLite 默认关闭）
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db() -> None:
    """初始化数据库表（含增量迁移）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 增量迁移
        from sqlalchemy import inspect as sa_inspect
        def _migrate(sync_conn):
            inspector = sa_inspect(sync_conn)
            # 为 knowledge_points 添加 source_pages 列
            cols = [c["name"] for c in inspector.get_columns("knowledge_points")]
            if "source_pages" not in cols:
                sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "ALTER TABLE knowledge_points ADD COLUMN source_pages VARCHAR(100) DEFAULT ''"
                    )
                )
            # 为 ppt_records 添加 source 和 stored_path 列
            ppt_cols = [c["name"] for c in inspector.get_columns("ppt_records")]
            if "source" not in ppt_cols:
                sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "ALTER TABLE ppt_records ADD COLUMN source VARCHAR(20) DEFAULT 'ai'"
                    )
                )
            if "stored_path" not in ppt_cols:
                sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "ALTER TABLE ppt_records ADD COLUMN stored_path VARCHAR(500) DEFAULT ''"
                    )
                )
            # 为 knowledge_points 新增 importance/difficulty/prerequisites_json/accuracy_json
            kp_cols = [c["name"] for c in inspector.get_columns("knowledge_points")]
            if "importance" not in kp_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE knowledge_points ADD COLUMN importance INTEGER DEFAULT 3"
                ))
            if "difficulty" not in kp_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE knowledge_points ADD COLUMN difficulty INTEGER DEFAULT 3"
                ))
            if "prerequisites_json" not in kp_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE knowledge_points ADD COLUMN prerequisites_json TEXT DEFAULT '[]'"
                ))
            if "accuracy_json" not in kp_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE knowledge_points ADD COLUMN accuracy_json TEXT DEFAULT '{}'"
                ))
            if "relationships_json" not in kp_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE knowledge_points ADD COLUMN relationships_json TEXT DEFAULT '[]'"
                ))
            # 为 courses 新增 subject 列(学科标识, 用于注入学科领域规则)
            course_cols = [c["name"] for c in inspector.get_columns("courses")]
            if "subject" not in course_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE courses ADD COLUMN subject VARCHAR(50) DEFAULT ''"
                ))
            if "content_hash" not in course_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE courses ADD COLUMN content_hash VARCHAR(64) DEFAULT ''"
                ))
            if "last_extracted_at" not in course_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE courses ADD COLUMN last_extracted_at DATETIME"
                ))
            # 为 materials 新增 version_label 和 is_primary 列(多教材版本管理)
            mat_cols = [c["name"] for c in inspector.get_columns("materials")]
            if "version_label" not in mat_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE materials ADD COLUMN version_label VARCHAR(100) DEFAULT ''"
                ))
            if "is_primary" not in mat_cols:
                sync_conn.execute(__import__("sqlalchemy").text(
                    "ALTER TABLE materials ADD COLUMN is_primary BOOLEAN DEFAULT 0"
                ))
        await conn.run_sync(_migrate)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
