"""综合测试脚本：覆盖所有修改过的功能点"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8002"
results = {"passed": [], "failed": []}

def test(name, condition, detail=""):
    if condition:
        results["passed"].append(f"  PASS: {name}")
    else:
        results["failed"].append(f"  FAIL: {name}  {detail}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        ignore_https_errors=True
    )
    page = context.new_page()

    # 收集控制台日志
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    print("\n" + "="*60)
    print("  测试 1: 页面加载")
    print("="*60)
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    js_errors = [e for e in console_errors if "favicon" not in e.lower()]
    test("页面加载无JS错误", len(js_errors) == 0, f"错误: {js_errors[:5]}")
    test("页面标题存在", page.title() != "")
    test("body内容渲染", page.locator("body").inner_html() != "")

    page.screenshot(path="/tmp/test_01_initial.png", full_page=True)
    print("  -> 截图: /tmp/test_01_initial.png")

    print("\n" + "="*60)
    print("  测试 2: 左侧栏结构")
    print("="*60)

    left_panel = page.locator("#leftPanel")
    test("左侧栏存在", left_panel.count() > 0)

    # 检查左侧栏中的section
    schedule_section = page.locator("#scheduleSection")
    material_section = page.locator("#materialSection")
    test("教学日历区域存在", schedule_section.count() > 0)
    test("教材资源区域存在", material_section.count() > 0)

    # 检查已移除的区域
    lesson_section = page.locator("#lessonSection")
    ppt_section = page.locator("#pptSection")
    v_resizer2 = page.locator("#vResizer2")
    v_resizer3 = page.locator("#vResizer3")
    test("教案记录区域已移除", lesson_section.count() == 0)
    test("PPT记录区域已移除", ppt_section.count() == 0)
    test("vResizer2已移除", v_resizer2.count() == 0)
    test("vResizer3已移除", v_resizer3.count() == 0)

    page.screenshot(path="/tmp/test_02_sidebar.png", full_page=True)
    print("  -> 截图: /tmp/test_02_sidebar.png")

    print("\n" + "="*60)
    print("  测试 3: 倒三角折叠功能")
    print("="*60)

    # courseInfo 初始为 hidden，需要先让它可见才能测试折叠按钮
    page.evaluate("""() => {
        const ci = document.querySelector('#courseInfo');
        if (ci) ci.classList.remove('hidden');
    }""")
    page.wait_for_timeout(300)

    collapse_btns = page.locator(".collapse-btn")
    btn_count = collapse_btns.count()
    test("折叠按钮存在", btn_count > 0, f"找到 {btn_count} 个")

    if btn_count > 0:
        first_btn = collapse_btns.first
        parent_section = page.locator("#scheduleSection")
        was_collapsed = parent_section.evaluate("el => el.classList.contains('collapsed')")
        first_btn.click()
        page.wait_for_timeout(300)
        is_collapsed = parent_section.evaluate("el => el.classList.contains('collapsed')")
        test("点击折叠按钮可切换折叠状态", is_collapsed != was_collapsed,
             f"初始: {was_collapsed}, 点击后: {is_collapsed}")
        first_btn.click()
        page.wait_for_timeout(300)
        is_back = parent_section.evaluate("el => el.classList.contains('collapsed')")
        test("再次点击可展开", is_back == was_collapsed,
             f"展开后: {is_back}, 期望: {was_collapsed}")

    page.screenshot(path="/tmp/test_03_collapse.png", full_page=True)
    print("  -> 截图: /tmp/test_03_collapse.png")

    print("\n" + "="*60)
    print("  测试 4: 预览标签切换")
    print("="*60)

    ppt_tab = page.locator("#previewTabPpt")
    lesson_tab = page.locator("#previewTabLesson")
    test("教案预览标签存在", lesson_tab.count() > 0)
    test("PPT预览标签存在", ppt_tab.count() > 0)

    ppt_tab.click()
    page.wait_for_timeout(500)
    ppt_active = ppt_tab.evaluate("el => el.classList.contains('active')")
    lesson_active = lesson_tab.evaluate("el => el.classList.contains('active')")
    test("点击PPT标签后PPT标签激活", ppt_active)
    test("点击PPT标签后教案标签取消激活", not lesson_active)

    ppt_bar = page.locator("#pptActionBar")
    lesson_bar = page.locator("#lessonActionBar")
    test("PPT操作栏显示", ppt_bar.evaluate("el => el.style.display !== 'none'"))
    test("教案操作栏隐藏", lesson_bar.evaluate("el => el.style.display === 'none'"))

    lesson_tab.click()
    page.wait_for_timeout(500)
    test("点击教案标签后教案操作栏显示",
         lesson_bar.evaluate("el => el.style.display !== 'none'"))
    test("点击教案标签后PPT操作栏隐藏",
         ppt_bar.evaluate("el => el.style.display === 'none'"))

    page.screenshot(path="/tmp/test_04_tab_switch.png", full_page=True)
    print("  -> 截图: /tmp/test_04_tab_switch.png")

    print("\n" + "="*60)
    print("  测试 5: PPT操作栏按钮")
    print("="*60)

    ppt_tab.click()
    page.wait_for_timeout(500)

    tpl_btn = page.locator("#pptOpenTemplateLibraryBtn")
    fs_btn = page.locator("#pptFullscreenBtn")
    save_btn = page.locator("#pptSaveBtn")
    export_btn = page.locator("#pptExportFileBtn")

    test("模板库按钮可见", tpl_btn.is_visible())
    test("全屏按钮可见", fs_btn.is_visible())
    test("模板库按钮未禁用", tpl_btn.is_enabled())
    test("全屏按钮初始禁用", fs_btn.is_disabled())
    test("保存按钮默认隐藏", save_btn.evaluate("el => el.classList.contains('hidden')"))
    test("导出PPT按钮默认隐藏", export_btn.evaluate("el => el.classList.contains('hidden')"))

    page.screenshot(path="/tmp/test_05_ppt_buttons.png", full_page=True)
    print("  -> 截图: /tmp/test_05_ppt_buttons.png")

    print("\n" + "="*60)
    print("  测试 6: 模板库模态框")
    print("="*60)

    tpl_btn.click()
    page.wait_for_timeout(500)
    tpl_modal = page.locator("#templateLibraryModal")
    test("模板库模态框弹出", tpl_modal.is_visible())

    ppt_tpl_tab = page.locator("#tplTabPpt")
    lesson_tpl_tab = page.locator("#tplTabLesson")
    test("教案模板标签存在", lesson_tpl_tab.count() > 0)
    test("PPT模板标签存在", ppt_tpl_tab.count() > 0)

    close_btn = page.locator(".tpl-close").first
    if close_btn.count() > 0:
        close_btn.click()
        page.wait_for_timeout(500)
        test("模板库模态框可关闭", not tpl_modal.is_visible())
    else:
        # 尝试点击遮罩层关闭
        tpl_modal.click(position={"x": 10, "y": 10})
        page.wait_for_timeout(500)
        test("点击遮罩层可关闭模板库模态框", not tpl_modal.is_visible())

    page.screenshot(path="/tmp/test_06_template_lib.png", full_page=True)
    print("  -> 截图: /tmp/test_06_template_lib.png")

    print("\n" + "="*60)
    print("  测试 7: 右侧预览区记录列表")
    print("="*60)

    lesson_file_list = page.locator("#lessonFileList")
    ppt_file_list = page.locator("#pptFileList")
    test("教案文件列表容器存在", lesson_file_list.count() > 0)
    test("PPT文件列表容器存在", ppt_file_list.count() > 0)

    # 在教案标签下，教案列表应可见，PPT列表应隐藏
    lesson_tab.click()
    page.wait_for_timeout(300)
    test("教案标签下教案列表显示",
         lesson_file_list.evaluate("el => !el.classList.contains('hidden')"))
    test("教案标签下PPT列表隐藏",
         ppt_file_list.evaluate("el => el.classList.contains('hidden')"))

    # 在PPT标签下，PPT列表应可见，教案列表应隐藏
    ppt_tab.click()
    page.wait_for_timeout(300)
    test("PPT标签下PPT列表显示",
         ppt_file_list.evaluate("el => !el.classList.contains('hidden')"))
    test("PPT标签下教案列表隐藏",
         lesson_file_list.evaluate("el => el.classList.contains('hidden')"))

    page.screenshot(path="/tmp/test_07_file_lists.png", full_page=True)
    print("  -> 截图: /tmp/test_07_file_lists.png")

    print("\n" + "="*60)
    print("  测试 8: 上传按钮")
    print("="*60)

    # 先切到教案标签
    lesson_tab.click()
    page.wait_for_timeout(300)

    upload_lesson_btn = page.locator("#uploadLessonBtn")
    upload_ppt_btn = page.locator("#uploadPptBtn")
    test("教案上传按钮存在", upload_lesson_btn.count() > 0)
    test("PPT上传按钮存在", upload_ppt_btn.count() > 0)
    test("教案上传按钮初始禁用", upload_lesson_btn.is_disabled())
    test("PPT上传按钮初始禁用", upload_ppt_btn.is_disabled())

    upload_lesson_input = page.locator("#uploadLessonInput")
    upload_ppt_input = page.locator("#uploadPptInput")
    test("教案文件输入框存在", upload_lesson_input.count() > 0)
    test("PPT文件输入框存在", upload_ppt_input.count() > 0)
    test("教案文件输入框隐藏", upload_lesson_input.evaluate("el => el.classList.contains('hidden')"))
    test("PPT文件输入框隐藏", upload_ppt_input.evaluate("el => el.classList.contains('hidden')"))

    page.screenshot(path="/tmp/test_08_upload_buttons.png", full_page=True)
    print("  -> 截图: /tmp/test_08_upload_buttons.png")

    # 清理
    browser.close()

    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    print(f"  通过: {len(results['passed'])}")
    print(f"  失败: {len(results['failed'])}")
    print()
    for p in results["passed"]:
        print(p)
    for f in results["failed"]:
        print(f)
    print()

    exit_code = 1 if results["failed"] else 0
    sys.exit(exit_code)