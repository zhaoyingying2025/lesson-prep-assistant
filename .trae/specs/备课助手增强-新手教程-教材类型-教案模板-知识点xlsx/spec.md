# 备课助手产品增强 PRD

## Overview
- **Summary**: 在已有"教材→知识点→教案→课件"主链路上，补齐四项核心能力：①首次使用引导/右上角详细新手教程；②教材上传前选择类型（六类）；③教案模板库（内置+用户上传+可在线修改）；④当前课程一键提取知识点（支持选教材、AI识别+联网准确性校验、XLSX按模板导出），并同步优化教案/PPT生成失败时的错误提示与备用方案，最后做全链路测试。
- **Purpose**: 让"首次打开就会用"、"上传的材料被正确识别并处理"、"教案结构可控"、"知识点输出可对接知识图谱模板系统"，同时提升失败场景的可恢复性，减少用户"卡住"感。
- **Target Users**: 高校/高职一线任课老师（唐宏老师为代表的用户），熟悉课程标准→教材→学情→目标→活动→教案→课件→作业工作流。

## Goals
- 首次进入系统时，中间对话区自动展示 8 步使用流程（简单文字版）。
- 顶部右上角新增"新手教程"按钮，点击弹出详细教程（含步骤描述、操作要点、常见问题 Q&A）。
- 教材上传模态框增加"教材类型"预选（六类枚举：课程标准/大纲、教科书、教参教辅、练习题册、学术论文、其他），并在列表中用图标或标签展示。
- 新增"教案模板库"：内置 1 套默认全表格模板，支持模板结构在线编辑、用户上传自定义模板 JSON 文件、多套模板切换/重命名/删除；教案生成 API 接收 `template_id` 并按模板结构构造 plan_json 基本骨架。
- 当前课程右侧"新建章 +"相邻处新增"一键提取知识点"按钮，点击弹出"选择教材资源（单选/多选）"模态框，后端用 LLM 批量识别知识点，并对每个知识点进行联网搜索二次校验，输出"准确性"评分与校验说明；导出时按用户提供的 14 列 XLSX 模板格式（分类/知识点层级路径 + 前置/后置/关联节点 + 标签 + 知识点分类 + 节点说明）生成文件。
- 教案生成、PPT 生成接口返回 HTTP 500/502/非 JSON 的场景下，前端 toast 增加"错误原因简述 + 备用操作按钮组"（重试 / 降参数重试 / 跳过 AI 生成改用模板填充 / 导出当前草稿 / 打开帮助）。
- 对以上新增功能 + 既有主链路做集成测试，保证 10 项关键 API 正常、UI 按钮不重叠、不永久禁用失效。

## Non-Goals
- 不实现学情分析、课程标准独立模块（仅支持"课程标准/大纲"作为教材类型上传与处理）。
- 不实现作业独立表、作业 Agent（仅在教案里保留 homework 字段）。
- 不做交互式导游（Tour / 高亮浮动气泡）。
- 不实现前端 PPT 逐页在线预览（slide_data 渲染）。
- 不修改 XLSX 模板格式本身，完全贴合用户给出的模板结构生成。

## Background & Context
- 用户当前工作流偏好：课程标准 → 教材 → 学情 → 目标 → 活动 → 教案 → 课件 → 作业（参考 `user_profile.md`）。
- UI 风格偏好：青绿水墨风（cyan-green），表格化布局。
- 项目基于 FastAPI + SQLAlchemy async + 原生 HTML 单页模板（Tailwind CDN），部署路径 `backend/app/templates/index.html`。
- 前端无原生 `prompt()/confirm()` 能力，必须使用自定义对话框（参考 `project_memory.md`）。
- 模板文件已在项目根目录：`importTopicTemplate2-知识图谱导入模板 - 离散数学（1）课程大纲知识图谱.xlsx`，第一行为说明、第二行为表头（14列）、第三行起为实际数据：节点类型*｜节点名称(列B-H 层级路径)｜前置节点｜后置节点｜关联节点｜标签｜知识点分类｜节点说明。
- `schemas.py` 已定义 6 种 `MaterialType`：`textbook / syllabus / training_plan / handout / paper / other`；用户确认的六类枚举需要把这 6 种重新映射（去掉 training_plan，改为用户期望的"课程标准/大纲、教科书、教参教辅、练习题册、学术论文、其他"）。
- 之前已确认：联网校验"真实联网搜索"，使用 `WebSearch`/后端对每个知识点做搜索摘要二次判断。
- 之前已确认：教案模板采用"多套模板库管理"。

## Functional Requirements
- **FR-1 首次使用引导（中间栏）**：若 `localStorage` 未标记 `tutorial_shown=1`，则中间对话空态区渲染 8 步工作流卡片（课程空间新建课→+新建章→上传教材并选类型→一键提取知识点→章节条①提取→②生成教案→对话微调→③生成PPT+导出）；右上角有"知道了"按钮，点击标记已看并还原默认空态提示。
- **FR-2 顶部右上角"新手教程"按钮**：在 `settingsBtn` 旁新增 `tutorialBtn`（图标"？"或"教程"文字），点击弹出居中模态框（青绿水墨风格，头部+8 个章节+Q&A 区+关闭按钮），内容为详细教程：每步均包含"前置条件/操作/预期结果/常见错误"4 段说明；Q&A 至少 6 条（如未配置 LLM、教材解析失败、知识点为空、教案生成失败、PPT 文件空白、上传 PPT显示加载失败）。
- **FR-3 教材类型预选**：上传教材模态框（uploadModal）中拖放区顶部新增 1 行 "教材类型" 单选按钮组，枚举 6 类（课程标准/大纲、教科书、教参教辅、练习题册、学术论文、其他），默认"自动识别"，勾选后前端用 `FormData.append('material_type', value)` 传给后端；后端接收并覆盖 `detect_material_type` 的结果；前端教材列表每项新增彩色 type-badge 显示对应当前类型。
- **FR-4 教案模板库**：新增数据库表 `lesson_templates`（id、course_scope=null 全局/课程id、name、description、structure_json、is_default、created_at/updated_at），至少内置 1 套默认模板（对应当前 `LessonPlan` 字段的"全表格模板"骨架）；前端新增"教案模板"模态框（顶部模板管理按钮或参数面板内"T 模板"按钮打开）：列表/新建/编辑 JSON 结构/删除/上传 JSON 文件/下载当前模板/设为默认；`generate_lesson_api` 新增 `template_id`（可选）参数；`lesson_agent.generate_lesson` 根据模板 structure_json 补充默认字段与空列表，保证输出即使 LLM 失败也能渲染全表格。
- **FR-5 一键提取知识点入口**：当前课程标题栏（`新建章+` 同一行）在其左侧新增"📖 一键提取知识点"按钮（不与加号重叠，用 flex gap）；点击弹出"选择教材资源"模态框（可多选，全选按钮，确认后进入处理）。
- **FR-6 后端多教材批量知识点提取与联网校验**：新增 `POST /courses/{course_id}/smart-extract-points`，Body 含 `material_ids[]`，对每个教材原文合并成块（按教材），调用 `extract_knowledge` 合并去重；之后对每个知识点名称执行联网搜索（后端 `requests.get` 百度百科/ DuckDuckGo 摘要或 LLM 侧 `search` 工具），将校验结果（`accuracy_score: 0-5`、`accuracy_reason: str`、`accuracy_flag: 'pass'|'warn'|'fail'`）写回每个知识点的 `metadata`；整个过程返回任务进度（或同步执行带超时保护，>100 个知识点时分批）。
- **FR-7 知识点 XLSX 导出**：新增 `POST /courses/{course_id}/knowledge-points/export-xlsx`，Body 可选 `filter_ids[]`、`chapter_name`，读取 DB 知识点，按 layer/parent 构建层级路径，填写用户模板的 14 列（节点类型=分类/知识点，B-H 列填层级路径空值截止，I-K 列填 prerequisites / 后置推导 / 关联，L 列标签=重点/难点/考点/思政拼接，M 列知识点分类=事实性/概念性/程序性/元认知（映射 layer），N 列节点说明=definition）；生成 xlsx 必须保留 R1（说明行）+ R2（表头行）完全同模板。
- **FR-8 生成失败优化与备用方案**：
  - 后端 `POST generate-lesson` / `POST export-ppt` 捕获异常时，返回结构化错误 `{ "success": false, "message": "...", "error_code": "...", "fallbacks": ["retry","lower_params","template_fallback","export_draft"] }` 而不是裸 HTTPException；
  - 前端 `extractKnowledge`/`genLessonBtn`/`genPptBtn` 的 catch 分支：在 toast 上弹出"操作失败"自定义对话框（而不是单行 toast），对话框内提供"重试 / 降低参数（温+更长 max_tokens）/ 用模板快速填充 / 保存当前草稿 / 打开帮助"5 个按钮。
- **FR-9 集成测试**：用 Python 脚本测试 10+ 项 API（课程列表、上传6类教材、smart-extract-points + 导出 xlsx、模板 CRUD、generate-lesson）、并浏览器冒烟测试 8 项 UI 交互（新建课程、上传教材并改类型、一键提取、生成教案失败重试、模板编辑、新手教程、XLSX 下载、按钮点击无重叠无永久禁用）。

## Non-Functional Requirements
- **NFR-1 布局**：所有按钮使用 `flex gap-x` 布局，不使用 `float`；任何新增按钮的 wrapper 均有 `position: relative`，z-index 用 `9999` 的下拉放在 header 外独立层，避免遮挡/点击穿透。
- **NFR-2 性能**：XLSX 导出 ≤ 3 秒（500 知识点以内）；一键提取进度 UI 有进度提示，不阻塞整页。
- **NFR-3 容错**：联网搜索失败（无网、接口限制）时自动降级为"无网络校验，保留原 AI 结果 + 打 warn 标签"，不中断整体提取。
- **NFR-4 一致性**：所有新增模态框遵循现有青绿水墨风（`.modal-mask / .modal-panel / .modal-header / .modal-body / .modal-footer`），不再出现原生 `alert/prompt/confirm`。
- **NFR-5 兼容性**：requirements 只增量添加 `openpyxl`（xlsx 导出），不删除既有依赖。数据库字段全部使用 nullable+default 的新增列/表，采用 Alembic/启动时 `run_sync` 自动创建（不迁移既有数据）。

## Constraints
- **Technical**: FastAPI + SQLAlchemy async + 单页 index.html（Tailwind CDN）；无 Node/Vite 构建流程；不能使用原生对话框。
- **Business**: XLSX 必须 100% 贴合用户提供的模板 R1 说明 + R2 表头结构，不能随意加列；分类与知识点节点的"知识点分类"字段只能填"事实性/概念性/程序性/元认知"之一。
- **Dependencies**: XLSX 依赖 `openpyxl`；联网校验依赖环境能外网访问（失败降级）。

## Assumptions
- 服务器能访问外网用于知识点校验（失败降级至本地 warn 标签）。
- 教案模板 structure_json 采用"表格定义数组"格式，前端导出预览时会据此渲染表格类型（title-table / info-table / goal-table / stage-table 等，沿用已有 60+ CSS 变量体系）。
- `WebSearch` 仅在 Spec 描述中作为目标能力，实际实现中若后端无法调用，则使用 `requests` 到公开搜索摘要 API（如 DuckDuckGo Instant Answer / Wikipedia OpenSearch）。

## Acceptance Criteria

### AC-1: 首次使用流程展示
- **Type**: `rule`
- **Given**: 浏览器清空 `localStorage.tutorial_shown` 并打开首页
- **When**: 页面加载完成
- **Then**: 中间对话空态区出现 8 步流程卡片，含对应标题、文字描述、"知道了"按钮；点击"知道了"后 `localStorage.tutorial_shown=1` 且空态恢复"备课助手·智能备课伴侣"默认文案；刷新页面后流程卡片不再出现。
- **Pass Condition**: 3 步均按预期。
- **Evidence**: 浏览器手动测试截图 + 控制台检查 localStorage。

### AC-2: 顶部新手教程按钮功能
- **Type**: `rule`
- **Given**: 已加载首页且 LLM 状态正常
- **When**: 点击顶部"新手教程"按钮
- **Then**: 弹出青绿风格模态框，含 8 个章节（与流程一一对应）及 Q&A 区；每个章节有前置条件/操作/预期/常见错误；Q&A ≥6 条；点击关闭/X/遮罩关闭均不触发其他操作；打开教程不影响其他输入框与按钮（按钮点击层级正确）。
- **Pass Condition**: 模态框出现、内容完整、关闭行为正常、按钮不重叠。
- **Evidence**: 浏览器手动测试截图。

### AC-3: 教材类型预选
- **Type**: `rule`
- **Given**: 已选择课程，课程列表与上传按钮可用
- **When**: 点击上传教材；在模态框"教材类型"选择"练习题册"；选择任意 test.md 上传；随后查看教材列表
- **Then**: 前端 formData 包含 `material_type=exercise_book`（或用户指定的枚举值）；后端 DB 中该 material 的 material_type 与选择一致；教材列表中每项材料旁有类型标签（彩色 badge）。
- **Pass Condition**: 6 类类型均能保存成功；修改默认值并重新上传验证字段一致。
- **Evidence**: Python API 脚本 + 浏览器截图。

### AC-4: 教案模板库多套管理
- **Type**: `rule`
- **Given**: 数据库中存在默认模板
- **When**: 打开模板管理；新增模板 A；修改其 structure_json；上传一个合法 JSON 作为模板 B；删除模板 A；将模板 B 设为默认
- **Then**: 新建/修改/上传/删除/设默认 5 个操作均对应 DB 变更；删除默认模板不允许（有禁止提示或保护）；上传 JSON 非法时给出错误 toast；模板管理对话框内按钮点击位置不重叠、不被 header 遮挡。
- **Pass Condition**: 所有 5 项 CRUD 操作通过；非法 JSON 拒绝入库；默认模板受保护。
- **Evidence**: Python API 脚本（CRUD 5 条 API 结果）+ 浏览器截图。

### AC-5: 教案生成按模板输出
- **Type**: `rule`
- **Given**: 已选默认非内置模板 B（在参数面板选择）
- **When**: 生成该章节教案
- **Then**: 返回的 `plan_json` 含模板 B 中所有必需字段（即使 LLM 未返回也会按 template 默认值补齐）；右栏预览表格结构与模板一致；生成失败时有 fallback 备用结构。
- **Pass Condition**: plan_json 字段 ≥ 模板 B 中定义的必需字段数。
- **Evidence**: Python API 脚本直接解析生成后的 plan_json。

### AC-6: 当前课程一键提取知识点入口
- **Type**: `rule`
- **Given**: 已选课程且课程下存在 ≥2 个教材
- **When**: 点击"📖 一键提取知识点"按钮
- **Then**: 弹出多选教材资源模态框，列出全部当前课程教材；可多选/全选；取消按钮关闭；确定按钮带 loading 状态且不可连击；确定后状态机不重复创建模态。
- **Pass Condition**: 弹窗正常、功能全、关闭行为正确、按钮不与 + / 当前课程名重叠。
- **Evidence**: 浏览器截图与点击序列。

### AC-7: 多教材 AI 提取 + 联网校验结果
- **Type**: `rule`
- **Given**: 选择 2 个有效教材
- **When**: 调用 smart-extract-points API
- **Then**: 返回结果 points ≥ 1；每个 point 含 `accuracy_score/accuracy_reason/accuracy_flag` 字段；若网络失败或接口超时，points 依然返回，flag 均为 `warn`；知识点不会因为联网校验超时缺失。
- **Pass Condition**: 调用返回 success=true，且每个知识点有 3 项元数据。
- **Evidence**: Python API 脚本 + 控制台日志。

### AC-8: XLSX 导出贴合模板格式
- **Type**: `rule`
- **Given**: 至少 10 条知识点的课程
- **When**: 调用 XLSX 导出 API，并读取生成的 xlsx 前 3 行与表头
- **Then**: Sheet 名 `Sheet3`（与模板一致）；R1 第 1 列含说明文字（与模板原文一致或等价）；R2 14 列标题与模板完全一致（`节点类型*` 到 `节点说明`）；R3 起每行数据填充：A 列填"分类/知识点"，B-H 填层级路径并在首个空列后保持为空；I-K 分号分隔字符串；L 列标签拼接含"重点/难点/考点"至少 1 条；M 列∈{事实性/概念性/程序性/元认知}；N 列=definition。
- **Pass Condition**: 结构 100% 匹配（R1/R2 完全同模板）、数据类型合法，总行列 ≥ 模板示例。
- **Evidence**: Python pandas 读取导出文件打印输出。

### AC-9: 失败提示 + 备用方案按钮
- **Type**: `rule`
- **Given**: 主动触发 `POST /courses/{course_id}/generate-lesson` 错误场景（如手动将 base_url 改成 `http://invalid.invalid:9999` 或 LLM API 返回空）
- **When**: 点击生成教案
- **Then**: 弹出失败对话框（非单行 toast），包含错误码/简短原因文字 + 5 个按钮（重试/降参/模板填充/保存草稿/帮助）；5 按钮点击分别触发对应动作：重试原请求 / 降低 temperature + 提高 max_tokens 再请求 / 用模板默认结构生成 plan_json 直接入库 / 当前草稿导出 JSON / 打开新手教程。所有点击行为均有 toast 反馈，不出现无响应。
- **Pass Condition**: 5 个按钮全部动作执行（可观察到对应调用/保存）。
- **Evidence**: Python API 脚本模拟错误 + 浏览器截图。

### AC-10: 集成测试 10 条 API + 8 项 UI 均通过
- **Type**: `rule`
- **Given**: 服务器运行在 127.0.0.1:8000
- **When**: 运行集成测试脚本
- **Then**: 课程列表/上传教材（6 种类型各 1 次）/ smart-extract-points / xlsx 导出 / 模板 CRUD / generate-lesson 共 ≥10 条 API success；浏览器 8 项 UI 点击链路（新建课→新建章→上传教材选类型→一键提取→生成教案→模板管理→新手教程→导出 xlsx）无报错、无按钮重叠、无永久禁用。
- **Pass Condition**: 10/10 API 通过；8/8 UI 通过。
- **Evidence**: 测试脚本输出截图 + 浏览器测试截图。

### AC-11: 按钮布局不重叠（rubric）
- **Type**: `rubric`
- **Dimension**: UI 布局合理性
- **Scale**: 1-5
- **Anchors**: 1 = 新增按钮明显遮挡已有按钮/点击穿透；3 = 不遮挡但视觉不一致；5 = 所有新增按钮尺寸、颜色、间距、z-index 与现有青绿风统一，拖动缩放 / 窄屏下无重叠，点击全部生效。
- **Pass Threshold**: >= 4
- **Evidence**: 浏览器 1280px、900px、1600px 三档窗口宽度的截图与点击验证。

## Open Questions
- 已澄清（用户答复见对话）：①教材类型 = 6 类细分；②联网 = 真实联网搜索；③模板 = 多套模板库；④教程 = 简单文字描述；⑤注意页面布局合理性。
