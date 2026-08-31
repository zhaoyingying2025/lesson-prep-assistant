"""备课助手配置"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend/）——使所有路径不依赖工作目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 千问API
    dashscope_api_key: str = ""
    llm_model: str = "qwen-plus"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # 路径（相对路径基于 PROJECT_ROOT，不依赖工作目录）
    upload_dir: str = "./uploads"
    data_dir: str = "./data"
    sqlite_db: str = "./data/lesson_prep.db"

    @property
    def upload_path(self) -> Path:
        p = (PROJECT_ROOT / self.upload_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_path(self) -> Path:
        p = (PROJECT_ROOT / self.data_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        return self.data_path / "lesson_prep.db"


settings = Settings()
