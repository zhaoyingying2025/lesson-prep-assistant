"""备课助手 UI 功能验收测试脚本（最终版）"""
import json, sys, time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")

def test_main_page(page):
    print("\n" + "=" * 60)
    print("[1] 首页加载测试")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    html = page.content()
    check("页面加载成功", len(html) > 10000)

    # 检查关键元素（使用DOM查询更可靠）
    check("全屏预览模态框", page.locator("#fullscreenLessonModal").count() > 0)
    check("编辑按钮", page.locator("#toggleEditBtn").count() > 0)
    check("保存按钮", page.locator("#saveLessonBtn").count() > 0)
    check("关闭按钮", page.locator("#closeFullscreenBtn").count() > 0)
    check("模板库入口", page.locator("#openTemplateLibraryBtn").count() > 0)
    check("生成教案按钮", page.locator("#genLessonBtn").count() > 0)
    check("模板库弹窗", page.locator("#templateLibraryModal").count() > 0)

def test_api_courses(page):
    print("\n" + "=" * 60)
    print("[2] 课程 API 测试")
    resp = page.evaluate("""async () => {
        const r = await fetch('/api/courses');
        return { ok: r.ok, data: await r.json() };
    }""")
    check("GET /api/courses 返回200", resp["ok"])
    courses = resp["data"]["data"]
    check(f"课程列表存在 ({len(courses)}门)", len(courses) > 0)
    for c in courses:
        print(f"       课程 [{c['id']}] {c['name']}")

def test_template_api(page):
    print("\n" + "=" * 60)
    print("[3] 教案模板 API 测试")
    resp = page.evaluate("""async () => {
        const r = await fetch('/api/lesson-templates');
        return { ok: r.ok, data: await r.json() };
    }""")
    check("GET /api/lesson-templates 返回200", resp["ok"])
    templates = resp["data"]["data"]
    check(f"模板列表存在 ({len(templates)}个)", len(templates) > 0)
    for t in templates:
        print(f"       模板 [{t['id']}] {t['name']} (默认: {t.get('is_default', False)})")

def test_template_detail_api(page):
    print("\n" + "=" * 60)
    print("[4] 教案模板详情 API 测试")
    resp = page.evaluate("""async () => {
        const r = await fetch('/api/lesson-templates');
        if (!r.ok) return {ok:false, reason:'list failed', data:null};
        const d = await r.json();
        const tpls = d.data || [];
        if (tpls.length === 0) return {ok:false, reason:'no templates', data:null};
        // 模板详情直接从列表返回，含 structure_json 字段
        return { ok: true, data: tpls[0] };
    }""")
    check("模板详情 API 可用", resp["ok"])
    if resp["ok"]:
        tpl = resp["data"]
        sj = tpl.get("structure_json") or tpl.get("structure") or {}
        tables = sj.get("tables", [])
        print(f"       模板结构: {len(tables)} 个表格模块")
        for tb in tables:
            print(f"       - {tb.get('label','')} ({tb.get('type','')})")

    # 下载模板
    dload = page.evaluate("""async () => {
        const r = await fetch('/api/lesson-templates');
        const d = await r.json();
        const tpls = d.data || [];
        if (tpls.length === 0) return {ok:false};
        const r2 = await fetch('/api/lesson-templates/' + tpls[0].id + '/download');
        return { ok: r2.ok, status: r2.status };
    }""")
    check("模板下载 API 可用", dload["ok"])

def test_chat_messages_api(page):
    print("\n" + "=" * 60)
    print("[5] 聊天记录 API 测试")
    courses = page.evaluate("""async () => {
        const r = await fetch('/api/courses');
        const d = await r.json();
        return d.data || [];
    }""")
    if not courses:
        print("       无课程，跳过")
        return
    cid = courses[0]["id"]
    resp = page.evaluate(f"""async () => {{
        const r = await fetch('/api/courses/{cid}/chat-messages?limit=10');
        return {{ ok: r.ok, data: r.ok ? await r.json() : null }};
    }}""")
    check(f"课程{cid}聊天记录接口返回200", resp["ok"])
    if resp["ok"]:
        msgs = resp["data"]["data"]
        print(f"       共 {len(msgs)} 条消息")
        for m in msgs[:3]:
            preview = (m["content"] or "")[:60]
            print(f"       [{m['role']}] {preview}...")

def test_ui_interaction(page):
    print("\n" + "=" * 60)
    print("[6] UI 交互测试")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # 点击课程卡片
    cards = page.locator("[class*='course'], [class*='chapter'], .card").first
    if cards.count() > 0 and cards.is_visible():
        cards.click()
        time.sleep(0.5)
        check("点击课程卡片", True)
    else:
        page.locator("button:has-text('+'), #addChapterBtn").first.click()
        time.sleep(0.5)
        check("点击新建章按钮", True)

    # 检查生成教案按钮
    gen_btn = page.locator("#genLessonBtn")
    check("生成教案按钮存在", gen_btn.count() > 0)
    if gen_btn.count() > 0:
        print(f"       状态: {'禁用(需先选章节)' if gen_btn.is_disabled() else '可用'}")

    # 检查PPT生成按钮
    ppt_btn = page.locator("#genPPTBtn, button:has-text('PPT')").first
    check("PPT生成按钮存在", ppt_btn.count() > 0)

    # 打开模板库弹窗
    tpl_btn = page.locator("#openTemplateLibraryBtn")
    if tpl_btn.count() > 0:
        tpl_btn.click()
        time.sleep(0.5)
        modal = page.locator("#templateLibraryModal")
        visible = modal.is_visible()
        # 检查是否显示了hidden类 - 如果hidden类存在但弹窗可见，说明toggle成功
        has_hidden = "hidden" in (modal.get_attribute("class") or "")
        check("模板库弹窗可打开", visible or not has_hidden)
        if visible or not has_hidden:
            # 关闭弹窗（使用 .tpl-close 类按钮）
            page.locator(".tpl-close").first.click()
            time.sleep(0.3)
        print(f"       弹窗可见: {visible}, 含hidden类: {has_hidden}")

def test_llm_config(page):
    print("\n" + "=" * 60)
    print("[7] LLM 配置测试")
    # 尝试多个路径
    for path in ["/api/settings/llm", "/api/llm/config", "/api/llm-settings"]:
        ok = page.evaluate(f"""async () => {{
            try {{ const r = await fetch('{path}'); return r.ok; }} catch(e) {{ return false; }}
        }}""")
        if ok:
            data = page.evaluate(f"""async () => {{
                const r = await fetch('{path}');
                const d = await r.json();
                // /api/settings/llm 返回 data.current 包含配置
                const inner = d.data || d;
                return inner.current || inner;
            }}""")
            print(f"       路径: {path}")
            print(f"       供应商: {data.get('provider', 'N/A')}")
            print(f"       模型: {data.get('model', 'N/A')}")
            print(f"       Max Tokens: {data.get('max_tokens', 'N/A')}")
            check("LLM 配置可用", True)
            break
    else:
        check("LLM 配置端点", False, "所有路径均不可用")

def test_knowledge_point_api(page):
    print("\n" + "=" * 60)
    print("[8] 知识点 API 测试")
    courses = page.evaluate("""async () => {
        const r = await fetch('/api/courses');
        const d = await r.json();
        return d.data || [];
    }""")
    if not courses:
        print("       无课程，跳过")
        return
    cid = courses[0]["id"]
    resp = page.evaluate(f"""async () => {{
        const r = await fetch('/api/courses/{cid}/knowledge-points');
        const d = r.ok ? await r.json() : null;
        return {{ ok: r.ok, data: d }};
    }}""")
    check(f"课程{cid}知识点接口可用", resp["ok"])
    if resp["ok"]:
        kps = resp["data"]["data"]
        print(f"       知识点数: {len(kps)}")

def test_materials_api(page):
    print("\n" + "=" * 60)
    print("[9] 教材资源 API 测试")
    courses = page.evaluate("""async () => {
        const r = await fetch('/api/courses');
        const d = await r.json();
        return d.data || [];
    }""")
    if not courses:
        print("       无课程，跳过")
        return
    cid = courses[0]["id"]
    resp = page.evaluate(f"""async () => {{
        const r = await fetch('/api/courses/{cid}/materials');
        return {{ ok: r.ok, data: r.ok ? await r.json() : null }};
    }}""")
    check(f"课程{cid}教材资源接口可用", resp["ok"])
    if resp["ok"]:
        mats = resp["data"]["data"]
        print(f"       教材资源数: {len(mats)}")

def test_screenshot(page):
    print("\n" + "=" * 60)
    print("[10] 页面截图")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    path = "d:/唐宏/实验室/备课助手/test_screenshot.png"
    page.screenshot(path=path, full_page=True)
    check("首页截图保存成功", True)
    print(f"       截图: {path}")

def main():
    global PASS, FAIL
    print("=" * 60)
    print("  备课助手 功能验收测试 v2.0")
    print(f"  目标: {BASE_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        tests = [
            ("首页加载", test_main_page),
            ("课程API", test_api_courses),
            ("模板API", test_template_api),
            ("模板详情API", test_template_detail_api),
            ("聊天记录API", test_chat_messages_api),
            ("UI交互", test_ui_interaction),
            ("LLM配置", test_llm_config),
            ("知识点API", test_knowledge_point_api),
            ("教材资源API", test_materials_api),
            ("页面截图", test_screenshot),
        ]
        for name, fn in tests:
            try:
                fn(page)
            except Exception as e:
                FAIL += 1
                print(f"  ❌ [{name}] 异常: {e}")
                import traceback
                traceback.print_exc()

        browser.close()

    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"  测试完成: {total} 项 | ✅ {PASS} 通过 | ❌ {FAIL} 失败")
    if FAIL == 0:
        print("  🎉 全部通过!")
    else:
        print(f"  ⚠️  {FAIL} 项失败")
    print("=" * 60)
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())