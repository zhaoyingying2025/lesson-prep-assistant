"""学科领域定制提示词加载器

借鉴 ai-teaching-ppt 的多槽位注入架构:
  domains/*.md  领域预设(学科/学段, 可热更新)
  operations/*.md 操作预设(润色/扩展/改写/提取)

扩展方式:
  1. 新增学科: 在 domains/ 下添加 .md 文件
  2. 新增操作: 在 operations/ 下添加 .md 文件
  3. 通过 subject 参数动态注入领域规则
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_DOMAINS_DIR = _BASE_DIR / "domains"
_OPERATIONS_DIR = _BASE_DIR / "operations"

# 学科中文名映射（含大学学科）
_SUBJECT_CN_MAP = {
    # 中小学
    "chinese": "语文",
    "math": "数学",
    "english": "英语",
    "physics": "物理",
    "chemistry": "化学",
    "biology": "生物",
    "history": "历史",
    "geography": "地理",
    "politics": "政治",
    "it": "信息技术",
    # 理学
    "applied_math": "应用数学",
    "statistics": "统计学",
    "psychology": "心理学",
    "ecology": "生态学",
    # 工学
    "cs": "计算机科学与技术",
    "software_eng": "软件工程",
    "ai": "人工智能",
    "data_science": "数据科学",
    "electronic_info": "电子信息工程",
    "communication": "通信工程",
    "automation": "自动化",
    "mechanical": "机械工程",
    "civil_eng": "土木工程",
    "architecture": "建筑学",
    "materials_sci": "材料科学与工程",
    "electrical_eng": "电气工程",
    "environmental_eng": "环境工程",
    "biomedical_eng": "生物医学工程",
    "cybersecurity": "网络安全",
    # 医学
    "clinical_med": "临床医学",
    "basic_med": "基础医学",
    "pharmacy": "药学",
    "nursing": "护理学",
    "stomatology": "口腔医学",
    "tcm": "中医学",
    "public_health": "公共卫生",
    # 法学
    "law": "法学",
    "sociology": "社会学",
    "political_sci": "政治学与行政学",
    # 经济学
    "economics": "经济学",
    "finance": "金融学",
    "fiscal": "财政学",
    "intl_trade": "国际经济与贸易",
    "insurance": "保险学",
    # 管理学
    "business_admin": "工商管理",
    "accounting": "会计学",
    "financial_mgmt": "财务管理",
    "marketing": "市场营销",
    "public_admin": "公共管理",
    "info_mgmt": "信息管理与信息系统",
    "ecommerce": "电子商务",
    "logistics": "物流管理",
    # 文学
    "chinese_lit": "中国语言文学",
    "foreign_lit": "外国语言文学",
    "journalism": "新闻传播学",
    "advertising": "广告学",
    "japanese": "日语",
    # 教育学
    "education": "教育学",
    "preschool_edu": "学前教育",
    "edtech": "教育技术学",
    "pe": "体育教育",
    # 艺术学
    "art_design": "艺术设计",
    "music": "音乐学",
    "fine_arts": "美术学",
    "dance": "舞蹈学",
    "digital_media": "数字媒体艺术",
    # 农学
    "agriculture": "农学",
    "forestry": "林学",
    "horticulture": "园艺学",
    "animal_sci": "动物科学",
    # 历史学
    "archaeology": "考古学",
    "museology": "文物与博物馆学",
    # 哲学
    "philosophy": "哲学",
    "logic": "逻辑学",
    # 默认
    "default": "通用",
}


def _load_md(directory: Path, name: str, fallback: str = "") -> str:
    """从目录加载 .md 文件内容, 找不到时返回 fallback"""
    path = directory / f"{name}.md"
    if path.exists():
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.warning(f"读取领域文件失败 {path}: {e}")
    return fallback


def list_domains() -> list[str]:
    """列出所有可用的学科领域预设"""
    if not _DOMAINS_DIR.exists():
        return ["default"]
    return sorted(p.stem for p in _DOMAINS_DIR.glob("*.md"))


def get_domain_context(subject: Optional[str]) -> str:
    """获取学科领域定制规则

    Args:
        subject: 学科标识(如 math/chinese/english/physics 等), None 或未知时使用默认

    Returns:
        学科领域规则文本, 用于注入到系统提示词中
    """
    if not subject:
        return _load_md(_DOMAINS_DIR, "_default", fallback="")

    subject_key = subject.strip().lower()
    # 支持中文输入
    cn_to_key = {v: k for k, v in _SUBJECT_CN_MAP.items()}
    if subject_key in cn_to_key:
        subject_key = cn_to_key[subject_key]

    content = _load_md(_DOMAINS_DIR, subject_key, fallback="")
    if not content:
        # 未知学科, 加载默认
        content = _load_md(_DOMAINS_DIR, "_default", fallback="")
    return content


def get_subject_cn(subject: Optional[str]) -> str:
    """获取学科中文名"""
    if not subject:
        return "通用"
    key = subject.strip().lower()
    cn_to_key = {v: k for k, v in _SUBJECT_CN_MAP.items()}
    if key in cn_to_key:
        key = cn_to_key[key]
    return _SUBJECT_CN_MAP.get(key, subject)


def inject_domain_context(system_prompt: str, subject: Optional[str]) -> str:
    """将学科领域规则注入到系统提示词末尾

    保留原有提示词内容, 在末尾追加学科定制规则(如有)
    """
    ctx = get_domain_context(subject)
    if not ctx:
        return system_prompt
    return f"{system_prompt}\n\n===== 学科领域定制规则 =====\n{ctx}\n===== 学科领域规则结束 ====="
