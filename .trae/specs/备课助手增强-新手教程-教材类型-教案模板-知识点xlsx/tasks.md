# 备课助手增强 · 实现计划

## Task 1: 数据库模型与新增表（lesson_templates + 扩展字段）
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `storage/db.py` 中新增 `LessonTemplateORM` 表（id、course_id 可空、name、description、structure_json(JSON)、is_default(bool)、created_at、updated_at）。
  - `MaterialORM.material_type` 保持 50-length string，但后端枚举需要与 UI 六类对应（新增 `extended_material_type` 或直接用字符串字面量）；确保已有数据不迁移、不报错。
  - 在启动初始化流程 `init_db` 中用 `run_sync` 新增表（或复用 `metadata.create_all` 因为新增表会被 Base.metadata 自动覆盖）。
  - 在 `models/schemas.py` 新增 `LessonTemplateCreate / LessonTemplateOut` pydantic schema，以及 `AccuracyMeta`（score/reason/flag）附加到 `KnowledgePoint` 作为 optional dict 字段。
- **Acceptance Criteria Addressed**: AC-4, AC-10
- **Test Requirements**:
  - `rule` TR-1.1: 启动 uvicorn 不报错；`DESCRIBE lesson_templates` 或 inspect 能看到新表；Material 插入新类型枚举值不抛 IntegrityError。
  - `rule` TR-1.2: Pydantic LessonTemplateOut 可被 ApiResponse(data=...) 正常序列化；knowledge point accuracy meta 为 None 时序列化 OK。

## Task 2: 教材类型 API 校验 + 六类枚举对齐
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 在 `schemas.py` 中把 `MaterialType` Literal 改为 6 类：`syllabus`(课程标准/大纲), `textbook`(教科书), `reference`(教参教辅), `exercise_book`(练习题册), `paper`(学术论文), `other`(其他)，并保持向后兼容（原 training_plan 自动转为 syllabus）。
  - `parser.detect_material_type` 启发式同步更新为这六类。
  - 后端 `upload_material` 路由中，若传入的 material_type ∉ 新枚举，自动 fallback 为 "other" 并在响应 message 中附带 "类型已修正" 提示。
  - 新增 `PUT /materials/{id}` 路由支持修改教材类型（UI 列表右键或按钮"改类型"）。
- **Acceptance Criteria Addressed**: AC-3, AC-10
- **Test Requirements**:
  - `rule` TR-2.1: 用 6 种类型分别上传 1 个 1KB txt，material_type DB 字段与输入一致；上传带 training_plan legacy 字符串被自动修正为 syllabus。
  - `rule` TR-2.2: 非法材料类型被 fallback 为 "other" 且响应消息包含 "类型已修正"。

## Task 3: 教案模板库 CRUD 路由与 storage
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - `routes.py` 新增：`GET /lesson-templates`（全局 + 课程私有）、`POST /lesson-templates`、`PUT /lesson-templates/{id}`、`DELETE /lesson-templates/{id}`、`POST /lesson-templates/{id}/set-default`、`POST /lesson-templates/import`（文件上传 JSON）。
  - 启动时 seed 默认模板：模板 JSON 对应当前 `LessonPlan` 结构的"全表格模板"骨架（字段列表 + 默认值）+ 渲染所需的表格类型标签。
  - `generate_lesson_api` 增加 `template_id: Optional[int] = Form(None)`；若有 template_id 则读其 structure_json，在进入 LLM 之前作为 `default_plan` 传给 agent，LLM 未返回的字段使用默认值回填；LLM 抛错时直接保存默认模板骨架。
- **Acceptance Criteria Addressed**: AC-4, AC-5, AC-10
- **Test Requirements**:
  - `rule` TR-3.1: seed 默认模板存在（GET 返回 1 条）。
  - `rule` TR-3.2: CRUD 5 条路由均返回 success=true（除删除默认模板返回 success=false + 原因）。
  - `rule` TR-3.3: 带 template_id 生成教案，返回的 plan_json 结构包含模板 JSON 中的全部 key。

## Task 4: 后端一键提取知识点 + 联网校验 + XLSX 导出
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**:
  - 新增 `POST /courses/{course_id}/smart-extract-points`：body `material_ids: list[int]`。读取每个 material 的 content_text，拼接按 12000 char 分块；调用 `extract_knowledge`；合并 deduplicate（按 name 归一化大小写）；为每个点追加 accuracy 元数据：使用 `requests` 联网搜索（优先 DuckDuckGo Instant Answer / Wikipedia，失败回退 LLM 自检打分）；最终写 DB（写入 `KnowledgePointORM.accuracy_json` 新字段，如结构不允许则临时保存在 `definition` 末尾但更合理的做法是新增 JSON 列到 KP 表）。
  - 新增 `POST /courses/{course_id}/knowledge-points/export-xlsx`：参数 `filter_ids`、`chapter_name`；读取 KP 数据并按 layer/parent 构造 B-H 层级路径；填写 L 标签（重点/难点/考点/思政）；M 映射 layer：basic→事实性 / core→概念性 / extension→程序性；分类节点固定"元认知"；I 列前置 = prerequisites；J 列后置 = 由 prerequisites 反向推导；K 列关联默认为空或 AI 自动生成（若无则留空）；N = definition。
  - 输出 xlsx 的 `Sheet3`：R1 原模板说明文字整行复制（从项目根目录 xlsx 文件作为模板 source）；R2 表头一致；R3 起填分类节点（课程 / 章 / 节 / 模块）+ 知识点节点；总层数最多 7 层（B-H）。
  - 新增 `openpyxl` 到 `requirements.txt`（如有重复则去重）。
- **Acceptance Criteria Addressed**: AC-7, AC-8, AC-10
- **Test Requirements**:
  - `rule` TR-4.1: smart-extract-points 返回 success + 列表，每个点含 accuracy_* 三字段。
  - `rule` TR-4.2: 断网模拟（requests 代理空）或超时（1s）时返回 warn 不中断。
  - `rule` TR-4.3: 导出 xlsx pandas 读取第一行/第二行/第三行结构 100% 匹配模板表头与说明（允许 R1 说明文字精简但字段数 14 列 + B-H-J-K-L-M-N 语义一致）。

## Task 5: 错误处理 fallback 改造（后端 + 前端）
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 后端：
    - `POST generate-lesson`：LLMError/其他异常均捕获并统一返回 `ApiResponse(success=False, message=..., error_code=..., data={"fallbacks": [...]})`，不 HTTP 500/502（只有无法序列化等严重情况才 500）。
    - `POST export-ppt`：异常同上；fallback 可用 `generate_ppt_content` 传入 style=minimal 重试。
    - 新增 `POST /lessons/{id}/fallback-template`：直接从指定 template_id 生成 plan_json 骨架（跳过 AI）。
  - 前端：
    - 抽出 `showOperationFailure(title, err, actions)` 复用函数（青绿模态框），在 extractKnowledge / genLesson / genPpt catch 中调用；默认 actions = 5 项按钮（重试/降参/模板/草稿/帮助）。
    - 每项 action 对应执行函数：retry 直接再调原函数；lower_params 改 LessonParams（temperature 降低，max_tokens 加倍）；template 调用 fallback-template API；draft 用 Blob 下载当前 JSON 草稿；help 打开新手教程。
- **Acceptance Criteria Addressed**: AC-9, AC-10
- **Test Requirements**:
  - `rule` TR-5.1: 构造一个会抛 LLMError 的请求（mock 或改 base_url），返回结构化 error_code+fallbacks，不是裸 HTTPError。
  - `rule` TR-5.2: 前端点击 5 个备用按钮分别有对应动作执行成功（toast 反馈可观测）。

## Task 6: 前端 UI：首次使用流程卡片、新手教程按钮、教材类型选择
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 中间栏 `chatStream` 空态初始 HTML 增加"工作流引导卡片"容器（默认隐藏，首次启动时 JS 判定 `tutorial_shown!=1` 显示）；卡片内含 8 步编号 + 标题 + 说明 + "知道了"。
  - 顶部 header 在 `settingsBtn` 左侧增加 `新手教程` 按钮；点击打开"新手教程"模态框，Modal 结构：标题"备课助手使用教程"；8 段章节（每段含前置条件/操作/预期/常见错误）；Q&A ≥ 6 条；关闭按钮。
  - 上传教材模态框内增加教材类型单选项 6 类（图标/label），默认选中"自动识别"；`uploadFiles` 里每次请求前先读取选中类型并 `fd.append('material_type', value)`；教材列表渲染中增加 `type-badge` 彩色标签。
  - 所有新增 UI 使用 flex/grid，按钮尺寸与 `btn-ghost btn-primary` 一致，不重叠；z-index 不超出 header 父容器 100 范围的下拉保持 9999。
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-11
- **Test Requirements**:
  - `rule` TR-6.1: 清 localStorage 后刷新，看到流程卡片；点击"知道了"后消失。
  - `rule` TR-6.2: 教程按钮点击 → 教程模态打开；关闭 → 隐藏；不影响其他输入；Q&A ≥6。
  - `rule` TR-6.3: 上传模态内可见 6 类教材类型；选择 1 类型上传后 DB 字段一致。
  - `rubric` TR-6.4: 布局合理性；scale 1-5；阈值≥4；evidence=1280/900/1600px 三种分辨率截图。

## Task 7: 前端 UI：一键提取知识点按钮 + 多选教材对话框 + 进度条 + XLSX 导出
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 2, Task 4
- **Description**:
  - 当前课程标题栏（"新建章 +"左边）新增"📖 提知"按钮（或文字图标混合），两者之间 flex gap-2；按钮 title="一键提取知识点（选教材）"。
  - 点击打开"选择教材资源"模态：当前课程全部材料以 checkbox 列表显示；底部有"全选/取消全选/确定/取消"四个按钮；确定后调用 smart-extract-points 接口，期间显示进度条（百分比/轮播圆点都可）。
  - 完成后，失败 → 调用 showOperationFailure；成功 → 弹出"共提取 X 个知识点"提示，并提供"立即导出 XLSX"按钮。
  - 知识点面板（knowledgePanel）顶部新增"导出 XLSX 📥"按钮：直接调用 export-xlsx API 触发下载。
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-8, AC-11
- **Test Requirements**:
  - `rule` TR-7.1: 点击按钮 → 弹出选择框（含全部材料，至少 2 项）；全选后确定 → 有进度反馈；完成后有结果提示。
  - `rule` TR-7.2: XLSX 下载后 pandas 读取成功（与 AC-8 重复，只保留 AC-8 做终态，此处只验证 HTTP 200）。

## Task 8: 前端 UI：教案模板管理按钮 + 模板编辑器对话框
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 教案参数面板内新增"T 模板"按钮（或在参数面板最右侧一列），打开"教案模板库"模态框。
  - 左侧：模板列表（active / 默认标记）+ 4 个操作（编辑/删除/设默认/下载）；顶部有"+ 新建模板"和"⬆ 上传 JSON"两个按钮。
  - 右侧：结构编辑器（JSON textarea 或更友好的树形编辑，如"字段/必填/默认/表格类型"表单；MVP 使用 JSON textarea + 语法提示）。
  - 保存模板时：后端 `PUT /lesson-templates/{id}`；新建则 POST；删除若为默认则阻止并提示。
  - 生成教案前端参数时始终将"当前激活模板 id"写入 hidden state 并在 FormData 中提交 template_id。
- **Acceptance Criteria Addressed**: AC-4, AC-5, AC-11
- **Test Requirements**:
  - `rule` TR-8.1: 模态 UI 能完成模板新建/JSON 编辑/保存/下载 JSON/上传 JSON 全流程。
  - `rule` TR-8.2: 默认模板删除按钮被 disable 或 alert "不允许删除默认模板"。
  - `rule` TR-8.3: 切换激活模板后，下次生成教案 API 请求 formData 含 template_id。

## Task 9: 集成测试 + 浏览器冒烟
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1-8
- **Description**:
  - 在 backend/ 下写 `tests_integration.py`：涵盖课程列表；6 种类型上传；smart-extract；xlsx 导出；模板 CRUD；generate-lesson（模板 + 无模板 + fallback）≥ 10 API。
  - 浏览器用 Playwright 测 8 步 UI：新建课 → +新建章 → 上传教材选"教参教辅"→ 点击 📖 提知 → 全选 2 教材 → 等待提取成功 → 打开模板管理编辑 → 下载导出 XLSX → 生成教案 → 查看布局。
  - 最后运行测试，把结果截图与控制台输出存入 completion evidence。
- **Acceptance Criteria Addressed**: AC-10
- **Test Requirements**:
  - `rule` TR-9.1: Python 集成脚本 10+ API 通过（exit code 0）。
  - `rule` TR-9.2: 浏览器 8 UI 步骤无报错、按钮全部能点击不 overlap。
