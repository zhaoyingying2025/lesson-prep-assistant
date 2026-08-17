"""SQLite数据库（SQLAlchemy 2.0 异步）"""
from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import (
    JSON,
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
    created_at = Column(DateTime, default=datetime.utcnow)

    materials = relationship("MaterialORM", back_populates="course", cascade="all,delete-orphan")
    lessons = relationship("LessonORM", back_populates="course", cascade="all,delete-orphan")
    messages = relationship("ChatMessageORM", back_populates="course", cascade="all,delete-orphan")
    chapters = relationship("ChapterORM", back_populates="course", cascade="all,delete-orphan", order_by="ChapterORM.sort_order")
    knowledge_points = relationship("KnowledgePointORM", back_populates="course", cascade="all,delete-orphan", order_by="KnowledgePointORM.sort_order")
    ppt_records = relationship("PptRecordORM", back_populates="course", cascade="all,delete-orphan")


class MaterialORM(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    material_type = Column(String(50), default="other")
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
    is_key_point = Column(Integer, default=0)      # 0/1
    is_difficult = Column(Integer, default=0)       # 0/1
    is_exam_point = Column(Integer, default=0)      # 0/1
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("CourseORM", back_populates="knowledge_points")


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
        await conn.run_sync(_migrate)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
