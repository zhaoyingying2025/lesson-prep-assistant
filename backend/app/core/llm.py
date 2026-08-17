"""LLM客户端（支持多供应商：Qwen / DeepSeek / OpenAI / 自定义）

所有供应商均通过OpenAI兼容接口对接，运行时配置存储于 data/llm_settings.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from openai import AsyncOpenAI

from ..config import settings


class LLMError(Exception):
    """LLM调用异常"""


# ============================================================
# 预设供应商
# ============================================================
PRESET_PROVIDERS: dict[str, dict[str, Any]] = {
    "qwen": {
        "label": "通义千问（阿里云DashScope）",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long", "qwen2.5-7b-instruct", "qwen2.5-14b-instruct"],
        "api_key_hint": "sk-...",
        "docs_url": "https://help.aliyun.com/zh/model-studio/",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
        "api_key_hint": "sk-...",
        "docs_url": "https://platform.deepseek.com/",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_hint": "sk-...",
        "docs_url": "https://platform.openai.com/",
    },
    "moonshot": {
        "label": "月之暗面 Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "api_key_hint": "sk-...",
        "docs_url": "https://platform.moonshot.cn/",
    },
    "zhipu": {
        "label": "智谱AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "models": ["glm-4-flash", "glm-4", "glm-4-air", "glm-4-airx"],
        "api_key_hint": "xxx.xxx",
        "docs_url": "https://open.bigmodel.cn/",
    },
    "custom": {
        "label": "自定义（OpenAI兼容接口）",
        "base_url": "",
        "default_model": "",
        "models": [],
        "api_key_hint": "根据服务商提供",
        "docs_url": "",
    },
}


# ============================================================
# 配置存储
# ============================================================
class LLMConfig:
    """LLM运行时配置（持久化到JSON文件）"""

    _instance: Optional["LLMConfig"] = None
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = self._load()
        # 若运行时配置缺失，尝试从 .env 初始化
        if not self._data:
            self._init_from_env()

    # ---- 文件路径 ----
    @property
    def config_path(self) -> Path:
        return settings.data_path / "llm_settings.json"

    # ---- 加载/保存 ----
    def _load(self) -> dict[str, Any]:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.config_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _init_from_env(self) -> None:
        """从 .env 初始化（兼容旧版部署）"""
        api_key = settings.dashscope_api_key
        if api_key and "****" not in api_key:
            self._data = {
                "provider": "qwen",
                "api_key": api_key,
                "base_url": settings.llm_base_url,
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
            }
            self._save()

    # ---- 访问器 ----
    def get_all(self) -> dict[str, Any]:
        return {
            "provider": self._data.get("provider", "qwen"),
            "api_key": self._data.get("api_key", ""),
            "base_url": self._data.get("base_url", ""),
            "model": self._data.get("model", ""),
            "temperature": self._data.get("temperature", 0.7),
            "max_tokens": self._data.get("max_tokens", 4096),
        }

    def get_masked(self) -> dict[str, Any]:
        """返回掩码后的配置（用于前端展示）"""
        cfg = self.get_all()
        cfg["api_key"] = mask_api_key(cfg["api_key"])
        cfg["has_api_key"] = bool(cfg["api_key"])
        return cfg

    def update(self, payload: dict[str, Any]) -> None:
        """更新配置。若 api_key 是掩码格式则保留原值"""
        # 处理 api_key 掩码情况
        if "api_key" in payload:
            new_key = payload["api_key"] or ""
            if new_key and ("****" in new_key or new_key == "********"):
                # 掩码占位，不修改
                payload.pop("api_key")
        # 处理 provider 切换：自动填充 base_url 和默认 model
        provider = payload.get("provider")
        if provider and provider in PRESET_PROVIDERS:
            preset = PRESET_PROVIDERS[provider]
            # 若切换了 provider 或 base_url 为空，使用预设
            current_provider = self._data.get("provider")
            if provider != current_provider or not payload.get("base_url"):
                payload["base_url"] = preset["base_url"]
            if provider != current_provider or not payload.get("model"):
                payload["model"] = preset["default_model"]
        # 合并更新
        self._data.update(payload)
        self._save()
        # 重置客户端单例
        global _llm_client
        _llm_client = None

    def is_configured(self) -> bool:
        cfg = self.get_all()
        return bool(cfg["api_key"] and cfg["base_url"] and cfg["model"])


# ============================================================
# 工具函数
# ============================================================
def mask_api_key(key: str) -> str:
    """API Key 掩码：保留前4后4，中间用 **** 替代"""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


# ============================================================
# LLM 客户端
# ============================================================
class LLMClient:
    """通用LLM异步客户端（兼容OpenAI协议）"""

    def __init__(self, cfg: dict[str, Any]) -> None:
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "")
        model = cfg.get("model", "")

        if not api_key:
            raise LLMError("未配置 API Key，请在设置中填写")
        if not base_url:
            raise LLMError("未配置 Base URL，请在设置中填写")
        if not model:
            raise LLMError("未配置模型名称，请在设置中填写")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = float(cfg.get("temperature", 0.7))
        self.max_tokens = int(cfg.get("max_tokens", 4096))
        self.provider = cfg.get("provider", "custom")

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """同步对话调用，返回完整文本"""
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"LLM调用失败: {e}") from e

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> dict | list:
        """对话调用并解析JSON结果"""
        text = await self.chat(system_prompt, user_prompt, temperature=temperature)
        return parse_json_loose(text)

    async def stream_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """流式对话，逐块返回文本增量"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise LLMError(f"LLM流式调用失败: {e}") from e


def parse_json_loose(text: str) -> dict | list:
    """宽松JSON解析：剥离代码块、修复常见格式问题"""
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    raw = m.group(1).strip() if m else text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        for start_char, end_char in (("{", "}"), ("[", "]")):
            start = raw.find(start_char)
            end = raw.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise LLMError(f"无法解析为JSON: {raw[:200]}...")


# ============================================================
# 全局单例
# ============================================================
_llm_client: Optional[LLMClient] = None
_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """获取 LLM 配置单例"""
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config


def get_llm() -> LLMClient:
    """获取 LLM 客户端单例（配置变更后自动重建）"""
    global _llm_client
    if _llm_client is None:
        cfg = get_llm_config().get_all()
        _llm_client = LLMClient(cfg)
    return _llm_client


def reset_llm() -> None:
    """重置 LLM 客户端单例（配置变更后调用）"""
    global _llm_client
    _llm_client = None
