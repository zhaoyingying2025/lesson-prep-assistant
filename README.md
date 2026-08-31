# 备课助手 · 智能备课伴侣

> 面向高校/高职教师的 AI 备课助手，基于大语言模型实现教案生成、知识点提取、PPT 制作等全流程备课支持。
> 采用**青绿水墨风格** UI，支持多供应商 LLM 接入。

---

## 快速开始

### 环境要求

- Python 3.10+
- 操作系统：Windows / macOS / Linux

### 安装

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置

在 `backend/.env` 中配置 LLM API Key：

```env
# 通义千问（阿里云DashScope）- 默认
DASHSCOPE_API_KEY=sk-你的API密钥
LLM_MODEL=qwen-plus

# 可选：如使用其他供应商
# LLM_BASE_URL=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-chat
```

> 也支持在应用运行时通过右上角「设置」界面修改 LLM 配置。

### 启动

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问 **http://localhost:8000** 即可使用。

---

## 项目结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理（读取 .env）
│   ├── agents/
│   │   ├── lesson_agent.py        # 教案生成 Agent（六阶段模型）
│   │   ├── lesson_agent_addie.py  # ADDIE 教学设计模型 Agent
│   │   ├── knowledge_agent.py     # 知识点提取 Agent
│   │   ├── chat_agent.py          # 对话修改教案 Agent
│   │   ├── ppt_agent.py           # PPT 生成 Agent
│   │   ├── smart_extract_agent.py # 智能章节提取 Agent
│   │   └── material_evaluator.py  # 教材内容评估 Agent
│   ├── api/
│   │   └── routes.py              # 全部 API 路由（60+ 端点）
│   ├── core/
│   │   ├── llm.py                 # LLM 客户端（多供应商适配）
│   │   ├── parser.py              # 文档解析（PDF/DOCX/TXT/MD）
│   │   ├── prompts.py             # LLM 提示词模板
│   │   ├── prompt_loader.py       # 外部提示词加载器
│   │   ├── content_validator.py   # 教案与 PPT 内容验证器
│   │   ├── textbook_cache.py      # 教材原文缓存与检索
│   │   └── domains/               # 多学科领域知识库（20+ 学科）
│   │       ├── chinese.md         # 语文
│   │       ├── math.md            # 数学
│   │       ├── english.md         # 英语
│   │       ├── physics.md         # 物理
│   │       ├── chemistry.md       # 化学
│   │       ├── biology.md         # 生物
│   │       ├── history.md         # 历史
│   │       ├── geography.md       # 地理
│   │       ├── politics.md        # 政治
│   │       ├── cs.md              # 计算机科学
│   │       ├── ai.md              # 人工智能
│   │       ├── accounting.md      # 会计
│   │       ├── finance.md         # 金融
│   │       ├── economics.md       # 经济
│   │       ├── law.md             # 法律
│   │       ├── education.md       # 教育
│   │       ├── psychology.md      # 心理
│   │       ├── nursing.md         # 护理
│   │       ├── clinical_med.md    # 临床医学
│   │       ├── it.md              # 信息技术
│   │       └── _default.md        # 默认通用知识库
│   ├── models/
│   │   └── schemas.py             # Pydantic 数据模型
│   ├── storage/
│   │   ├── db.py                  # SQLAlchemy 异步 ORM（多数据表）
│   │   └── file_store.py          # 文件存储
│   ├── exporters/
│   │   ├── docx_export.py         # DOCX 教案导出
│   │   ├── template_docx.py       # 模板式 DOCX 导出
│   │   ├── pptx_export.py         # PPTX 幻灯片导出
│   │   └── markdown.py            # Markdown 导出
│   ├── static/
│   │   └── default_template.docx  # 默认教案模板文件
│   └── templates/
│       └── index.html             # 前端主页面（单页应用）
├── data/                          # 运行时数据
│   └── llm_settings.json          # LLM 设置持久化
├── uploads/                       # 上传文件存储（按课程分目录）
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
└── railway.json                   # 部署配置
```

---

## API 文档

启动服务后访问 **http://localhost:8000/docs** 查看交互式 API 文档（Swagger UI）。

### 核心 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/llm-test` | LLM 连通性测试 |
| | **课程管理** | |
| GET | `/api/courses` | 课程列表 |
| POST | `/api/courses` | 创建课程 |
| GET | `/api/courses/{id}` | 课程详情 |
| PUT | `/api/courses/{id}` | 更新课程 |
| DELETE | `/api/courses/{id}` | 删除课程 |
| | **章节管理** | |
| GET | `/api/courses/{id}/chapters` | 章节树（递归嵌套） |
| POST | `/api/courses/{id}/chapters` | 新建章节 |
| PUT | `/api/chapters/{id}` | 更新章节 |
| DELETE | `/api/chapters/{id}` | 删除章节 |
| | **教材管理** | |
| POST | `/api/courses/{id}/materials` | 上传教材文件（自动索引） |
| GET | `/api/courses/{id}/materials` | 教材列表 |
| GET | `/api/materials/types` | 教材类型列表 |
| PUT | `/api/materials/{id}` | 更新教材信息 |
| PUT | `/api/materials/{id}/reupload` | 重新上传教材文件 |
| PUT | `/api/materials/{id}/set-primary` | 设置主教材 |
| DELETE | `/api/materials/{id}` | 删除教材 |
| | **知识点管理** | |
| POST | `/api/courses/{id}/smart-extract` | 一键智能章节提取 |
| POST | `/api/courses/{id}/extract-knowledge` | 知识点提取 |
| POST | `/api/courses/{id}/smart-extract-points` | 智能提取知识点到章节 |
| GET | `/api/courses/{id}/knowledge-points` | 知识点列表 |
| POST | `/api/courses/{id}/knowledge-points` | 新增知识点 |
| PUT | `/api/knowledge-points/{id}` | 更新知识点 |
| DELETE | `/api/knowledge-points/{id}` | 删除知识点 |
| POST | `/api/courses/{id}/knowledge-points/export-xlsx` | 导出知识点为 Excel 模板 |
| GET | `/api/courses/{id}/knowledge-graph` | 知识点图谱 |
| GET | `/api/courses/{id}/extract-progress` | 提取进度查询 |
| | **教案管理** | |
| POST | `/api/courses/{id}/generate-lesson` | 生成教案（含教材原文引用） |
| POST | `/api/courses/{id}/lessons` | 手动创建教案 |
| GET | `/api/courses/{id}/lessons` | 教案列表 |
| GET | `/api/lessons/{id}` | 教案详情 |
| PUT | `/api/lessons/{id}` | 更新教案 |
| DELETE | `/api/lessons/{id}` | 删除教案 |
| POST | `/api/lessons/{id}/evaluate` | 教案内容评估 |
| POST | `/api/lessons/{id}/chat` | 对话修改教案 |
| POST | `/api/lessons/{id}/fallback-template` | 回退模板 |
| | **PPT 与导出** | |
| POST | `/api/lessons/{id}/export-ppt` | 生成 PPT 数据 |
| GET | `/api/lessons/{id}/export/{fmt}` | 导出（markdown/docx/pptx） |
| POST | `/api/courses/{id}/upload-ppt` | 上传 PPT 文件 |
| GET | `/api/ppt/{id}/download` | 下载 PPT 文件 |
| GET | `/api/courses/{id}/ppt-records` | PPT 生成记录列表 |
| GET | `/api/ppt-records/{record_id}` | PPT 记录详情 |
| DELETE | `/api/ppt-records/{record_id}` | 删除 PPT 记录 |
| POST | `/api/ppt-records/{record_id}/download` | 下载 PPT 记录 |
| | **教案模板管理** | |
| GET | `/api/lesson-templates` | 模板列表 |
| POST | `/api/lesson-templates` | 创建模板 |
| PUT | `/api/lesson-templates/{id}` | 更新模板 |
| DELETE | `/api/lesson-templates/{id}` | 删除模板 |
| POST | `/api/lesson-templates/{id}/set-default` | 设为默认模板 |
| POST | `/api/lesson-templates/import` | 导入模板 |
| PUT | `/api/lesson-templates/{id}/upload-docx` | 上传 DOCX 模板文件 |
| GET | `/api/lesson-templates/default/download` | 下载默认模板 |
| GET | `/api/lesson-templates/{id}/download` | 下载指定模板 |
| | **其他** | |
| POST | `/api/courses/{id}/mindmap` | 生成思维导图 |
| GET | `/api/settings/llm` | 获取 LLM 设置 |
| PUT | `/api/settings/llm` | 更新 LLM 设置 |
| POST | `/api/settings/llm/test` | 测试 LLM 连接 |
| GET | `/api/courses/{id}/chat-messages` | 获取对话历史 |

---

## 使用流程

```
1. 创建课程 ──→ 2. 上传教材 ──→ 3. 提取知识点 ──→ 4. 生成教案 ──→ 5. 导出
                     │                                                │
                     ├─ 自动识别教材类型                              ├─ Markdown
                     │  （教材/大纲/培养方案等）                      ├─ DOCX
                     ├─ 自动按页索引                                  └─ PPTX
                     │  └─ 四角页码检测
                     └─ 一键智能提取章节结构
                         └─ 自动创建章节目录
                            └─ 提取知识点到对应章节
                               └─ 标注教材页码
```

### 详细步骤

1. **创建课程**：输入课程名称、所属专业和描述
2. **上传教材**：支持 PDF、DOCX、TXT、MD 格式，系统自动解析全文并识别教材类型。PDF 文件上传时自动按页索引，检测教材实际印刷页码（四角检测算法）
3. **提取知识点**：
   - **一键智能提取**：自动识别章节结构，创建章节目录，提取知识点到对应章节并标注教材页码
   - **智能提取到章节**：将知识点自动归类到已有章节
   - **手动提取**：指定章节名称，提取该章节的知识点
   - **手动管理**：支持新增/编辑/删除知识点，标记重点/难点/考点，填写教材页码出处
   - **Excel 导出**：导出知识点为 Excel 模板，支持批量导入
4. **生成教案**：选择章节和知识点，配置教学参数（时长、风格、互动密度等），AI 自动生成六阶段结构化教案，自动引用教材原文并标注页码。支持 ADDIE 教学设计模型生成
5. **评估教案**：生成后自动评估教案质量，包含内容完整性、教学逻辑、目标可达性等维度
6. **修改教案**：通过自然语言对话对教案进行调整（如"增加一个案例分析"、"将导入环节改为情景导入"）
7. **导出**：支持导出为 Markdown、DOCX 或 PPTX 格式，支持自定义模板

---

## 教案结构

AI 生成的教案采用**六阶段教学设计**：

| 阶段 | 说明 |
|------|------|
| **导入**（新知导入） | 激发兴趣，引入主题 |
| **讲授**（新知讲授） | 系统讲解核心知识 |
| **互动**（互动深化） | 课堂讨论、案例分析等 |
| **练习**（练习巩固） | 随堂练习，检验掌握 |
| **小结**（课堂小结） | 总结回顾，梳理框架 |
| **作业**（课后作业） | 分层作业，巩固拓展 |

每份教案还包含：
- 三维教学目标（知识目标、能力目标、价值目标）
- 教学重难点及突破策略
- 板书设计
- 教学反思（预留）
- 知识点出处表（标注教材页码）

支持 **ADDIE 教学设计模型**（分析、设计、开发、实施、评价），提供更系统的教学设计流程。

---

## 关键技术特性

### 教材页码检测（四角检测算法）

上传 PDF 教材时，系统自动检测教材的实际印刷页码：

1. **四角检测**：扫描页面四个角落的孤立数字文本块，识别印刷页码
2. **顶部边缘检测**：检测页面顶部左右两侧的页码（如 "22\n第1 章" 中的 22）
3. **首行回退**：从首行文本提取数字（如 "24 第1 章" 中的 24）
4. **页码推断**：基于已知页码进行前向/后向填充，处理缺失页码

支持格式：阿拉伯数字、罗马数字（VII、XII 等）、带分隔符页码等。

### 教材原文缓存

上传教材时自动按页分割并缓存到数据库，后续知识点提取和教案生成时：
- 快速检索知识点在教材中的原文位置
- 获取知识点前后页的上下文内容
- 在教案和 PPT 中引用教材原文并标注页码

### 多学科领域知识库

内置 20+ 学科领域知识库，为不同学科提供针对性的教学指导：
- 文科：语文、英语、历史、地理、政治、法律、教育、心理
- 理科：数学、物理、化学、生物、计算机科学、人工智能
- 商科：会计、金融、经济
- 医学：护理、临床医学
- 其他：信息技术

### 教案内容评估与验证

生成教案后自动进行多维度评估：
- 内容完整性检查
- 教学逻辑合理性
- 教学目标可达性
- 教材原文引用准确性
- PPT 内容一致性验证

### 模板式 DOCX 导出

支持自定义 DOCX 模板，灵活控制教案导出格式：
- 定义表格结构（标题表、信息表、目标表、重难点表等）
- 自定义字段映射
- 支持多模板切换
- 在线下载默认模板

### 多供应商 LLM 适配

| 供应商 | 默认模型 | 说明 |
|--------|----------|------|
| 通义千问（阿里云） | qwen-plus | 默认，需 DashScope API Key |
| DeepSeek | deepseek-chat | 需 DeepSeek API Key |
| OpenAI | gpt-4o-mini | 需 OpenAI API Key |
| 月之暗面 (Kimi) | moonshot-v1-8k | 需 Moonshot API Key |
| 智谱 (GLM) | glm-4-plus | 需智谱 API Key |
| 自定义 | - | 任意兼容 OpenAI 接口的服务 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | SQLite（通过 aiosqlite） |
| 前端 | Jinja2 + 原生 HTML/CSS/JavaScript |
| LLM | OpenAI 兼容接口（多供应商适配） |
| 文档解析 | PyMuPDF / pypdf / python-docx |
| 办公导出 | python-docx / python-pptx |
| 风格主题 | 青绿水墨风格（CSS 变量系统） |

---

## 许可

本项目仅供教育和学习用途。