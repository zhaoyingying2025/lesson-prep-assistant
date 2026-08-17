# 备课助手 · 智能备课伴侣

> 面向高校/高职教师的 AI 备课助手，基于大语言模型实现教案生成、知识点提取、PPT 制作等全流程备课支持。
> 采用**青绿水墨风格** UI，支持多供应商 LLM 接入。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **课程管理** | 创建/编辑/删除课程，支持设置专业和描述 |
| **教材资源管理** | 上传 PDF、Word、TXT、MD 等教材文件，自动解析全文并识别教材类型 |
| **智能章节提取** | 一键从教材中自动识别章节结构，创建章节目录，提取知识点到对应章节 |
| **知识点管理** | 手动新增/编辑/删除知识点，标记重点/难点/考点，标注教材页码出处 |
| **AI 教案生成** | 基于课程、章节和知识点，自动生成六阶段结构化教案（含三维目标、重难点、教学过程等） |
| **对话修改教案** | 通过自然语言对话对已生成的教案进行修改和调整 |
| **思维导图** | 根据知识点生成思维导图，直观展示课程知识结构 |
| **PPT 生成** | 支持多种风格（学术/青绿/卡通/正式/简约）的教学 PPT 生成，可自定义内容和密度 |
| **多格式导出** | 教案支持导出为 Markdown、DOCX、PPTX 格式 |
| **多供应商 LLM** | 支持通义千问、DeepSeek、OpenAI、月之暗面、智谱等多家大模型 |
| **教材页码索引** | 上传教材时自动按页索引，知识点可标注原始教材页码 |
| **教材原文引用** | 教案和 PPT 生成时自动检索教材原文，引用教材内容并标注页码 |

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
│   │   ├── lesson_agent.py        # 教案生成 Agent
│   │   ├── knowledge_agent.py     # 知识点提取 Agent
│   │   ├── chat_agent.py          # 对话修改教案 Agent
│   │   ├── ppt_agent.py           # PPT 生成 Agent
│   │   └── smart_extract_agent.py # 智能章节提取 Agent
│   ├── api/
│   │   └── routes.py              # 全部 API 路由（40+ 端点）
│   ├── core/
│   │   ├── llm.py                 # LLM 客户端（多供应商适配）
│   │   ├── parser.py              # 文档解析（PDF/DOCX/TXT/MD）
│   │   ├── prompts.py             # LLM 提示词模板
│   │   └── textbook_cache.py      # 教材原文缓存与检索
│   ├── models/
│   │   └── schemas.py             # Pydantic 数据模型
│   ├── storage/
│   │   ├── db.py                  # SQLAlchemy 异步 ORM（7 个数据表）
│   │   └── file_store.py          # 文件存储
│   ├── exporters/
│   │   ├── docx_export.py         # DOCX 教案导出
│   │   ├── pptx_export.py         # PPTX 幻灯片导出
│   │   └── markdown.py            # Markdown 导出
│   └── templates/
│       └── index.html             # 前端主页面（单页应用）
├── data/                          # 运行时数据
│   ├── lesson_prep.db             # SQLite 数据库
│   └── llm_settings.json          # LLM 设置持久化
├── uploads/                       # 上传文件存储（按课程分目录）
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
└── railway.json                   # Railway 部署配置
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
| | **教材管理** | |
| POST | `/api/courses/{id}/materials` | 上传教材文件（自动索引） |
| GET | `/api/courses/{id}/materials` | 教材列表 |
| | **知识点管理** | |
| POST | `/api/courses/{id}/smart-extract` | 一键智能章节提取 |
| POST | `/api/courses/{id}/extract-knowledge` | 知识点提取 |
| GET | `/api/courses/{id}/knowledge-points` | 知识点列表 |
| POST | `/api/courses/{id}/knowledge-points` | 新增知识点 |
| PUT | `/api/knowledge-points/{id}` | 更新知识点 |
| DELETE | `/api/knowledge-points/{id}` | 删除知识点 |
| | **教案管理** | |
| POST | `/api/courses/{id}/generate-lesson` | 生成教案（含教材原文引用） |
| GET | `/api/courses/{id}/lessons` | 教案列表 |
| PUT | `/api/lessons/{id}` | 更新教案 |
| POST | `/api/lessons/{id}/chat` | 对话修改教案 |
| | **PPT 与导出** | |
| POST | `/api/lessons/{id}/export-ppt` | 生成 PPT 数据 |
| GET | `/api/lessons/{id}/export/{fmt}` | 导出（markdown/docx/pptx） |
| | **其他** | |
| POST | `/api/courses/{id}/mindmap` | 生成思维导图 |
| GET | `/api/settings/llm` | 获取 LLM 设置 |
| PUT | `/api/settings/llm` | 更新 LLM 设置 |

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
   - **手动提取**：指定章节名称，提取该章节的知识点
   - **手动管理**：支持新增/编辑/删除知识点，标记重点/难点/考点，填写教材页码出处
4. **生成教案**：选择章节和知识点，配置教学参数（时长、风格、互动密度等），AI 自动生成六阶段结构化教案，自动引用教材原文并标注页码
5. **修改教案**：通过自然语言对话对教案进行调整（如"增加一个案例分析"、"将导入环节改为情景导入"）
6. **导出**：支持导出为 Markdown、DOCX 或 PPTX 格式

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
| 风格主题 | 青绿水墨风格（CSS 变量系统，~60 个变量） |

---

## 部署

### Railway 部署

项目包含 `railway.json` 配置文件，支持一键部署到 Railway：

1. 将代码推送至 GitHub 仓库
2. 在 Railway 中连接该仓库
3. 设置 Root Directory 为 `backend`
4. 添加环境变量 `DASHSCOPE_API_KEY` 等
5. 部署完成后访问生成的域名

### 内网穿透（临时共享）

```bash
# 启动本地服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 另一终端启动 ngrok
ngrok http 8000
```

---

## 功能测试

项目已通过 39 项功能测试，覆盖所有核心 API 端点：

- 健康检查与 LLM 连通性
- 课程 CRUD（增删改查）
- 教材上传与解析
- 章节树管理
- 知识点管理（含页码标注）
- 教案生成与导出
- PPT 生成与导出
- 思维导图生成
- LLM 设置管理

---

## 许可

本项目仅供教育和学习用途。