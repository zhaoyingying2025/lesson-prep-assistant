"""文件存储（本地文件系统）"""
from __future__ import annotations

import uuid
from pathlib import Path

from ..config import settings


async def save_upload(file_bytes: bytes, original_filename: str, course_id: int) -> Path:
    """保存上传文件，返回存储路径"""
    ext = Path(original_filename).suffix
    stored_name = f"{course_id}_{uuid.uuid4().hex[:8]}{ext}"
    course_dir = settings.upload_path / f"course_{course_id}"
    course_dir.mkdir(parents=True, exist_ok=True)
    stored_path = course_dir / stored_name
    stored_path.write_bytes(file_bytes)
    return stored_path


async def delete_file(stored_path: str) -> None:
    p = Path(stored_path)
    if p.exists():
        p.unlink()
