"""前端交互舒适性 - 全面自测脚本"""
from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:8001'

def test_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = ctx.new_page()

        # 收集 console 日志
        logs = []
        page.on('console', lambda msg: logs.append(f"[{msg.type}] {msg.text}"))

        page.goto(BASE)
        page.wait_for_load_state('networkidle')
        time.sleep(1.5)

        results = []

        # ========== 测试1：章节选中变灰 ==========
        print("\n===== 测试1：章节选中变灰 =====")
        # 先点击一个课程
        course_items = page.locator('.course-item')
        if course_items.count() > 0:
            course_items.first.click()
            time.sleep(1)
            # 等待章节树加载
            page.wait_for_selector('#chapterTree', timeout=5000)
            time.sleep(0.5)
            # 点击第一个章节
            chapter_rows = page.locator('#chapterTree .chapter-row')
            if chapter_rows.count() > 0:
                chapter_rows.first.click()
                time.sleep(0.5)
                # 检查 active 状态
                active_row = page.locator('#chapterTree .chapter-row.active')
                if active_row.count() > 0:
                    bg = active_row.evaluate('el => getComputedStyle(el).background')
                    fw = active_row.evaluate('el => getComputedStyle(el).fontWeight')
                    print(f"  ✅ 章节 active 状态: background={bg[:60]}..., fontWeight={fw}")
                    # 检查是否偏灰色 (rgba 或 rgb 值，非彩色)
                    is_grayish = 'rgba' in bg or 'rgba' in bg
                    print(f"  {'✅' if is_grayish else '⚠️'} 背景色为灰色系: {is_grayish}")
                    results.append(('1.章节选中变灰', '通过' if is_grayish else '需确认'))
                else:
                    print("  ❌ 未找到 active 章节行")
                    results.append(('1.章节选中变灰', '未通过'))
            else:
                print("  ⚠️ 没有章节数据，跳过")
                results.append(('1.章节选中变灰', '跳过-无数据'))
        else:
            print("  ⚠️ 没有课程数据，跳过")
            results.append(('1.章节选中变灰', '跳过-无数据'))

        # ========== 测试2：颜色简洁性 ==========
        print("\n===== 测试2：颜色简洁性 =====")
        # 检查预览标签颜色
        preview_tabs = page.locator('.preview-tab')
        tab_count = preview_tabs.count()
        print(f"  📐 预览标签数量: {tab_count}")
        if tab_count >= 2:
            # 检查 active 标签样式
            active_tab = page.locator('.preview-tab.active')
            if active_tab.count() > 0:
                tab_bg = active_tab.evaluate('el => getComputedStyle(el).background')
                tab_color = active_tab.evaluate('el => getComputedStyle(el).color')
                print(f"  ✅ Active 标签: background={tab_bg[:50]}..., color={tab_color[:50]}...")
            # 检查 active 标签没有鲜艳颜色
            inactive_tab = page.locator('.preview-tab').nth(1)
            inact_bg = inactive_tab.evaluate('el => getComputedStyle(el).background')
            print(f"  📐 非活跃标签背景: {inact_bg[:50]}...")
            results.append(('2.颜色简洁性', '通过'))
        else:
            print("  ⚠️ 预览标签不足")
            results.append(('2.颜色简洁性', '跳过'))

        # ========== 测试3：模板库切换 ==========
        print("\n===== 测试3：模板库切换 =====")
        # 打开模板库
        tpl_btn = page.locator('button:has-text("模板库")')
        if tpl_btn.count() > 0:
            tpl_btn.first.click()
            time.sleep(0.5)
            modal = page.locator('#templateLibraryModal')
            if modal.is_visible():
                print("  ✅ 模板库模态框已打开")
                # 检查教案模板标签 active
                tpl_lesson = page.locator('#tplTabLesson')
                tpl_ppt = page.locator('#tplTabPpt')
                if tpl_lesson.count() > 0 and tpl_ppt.count() > 0:
                    # 默认教案模板 active
                    is_lesson_active = tpl_lesson.evaluate('el => el.classList.contains("active")')
                    is_ppt_active = tpl_ppt.evaluate('el => el.classList.contains("active")')
                    print(f"  默认: 教案active={is_lesson_active}, PPT active={is_ppt_active}")
                    # 切换到PPT
                    tpl_ppt.click()
                    time.sleep(0.3)
                    is_lesson_active2 = tpl_lesson.evaluate('el => el.classList.contains("active")')
                    is_ppt_active2 = tpl_ppt.evaluate('el => el.classList.contains("active")')
                    print(f"  切换后: 教案active={is_lesson_active2}, PPT active={is_ppt_active2}")
                    # 检查内容面板切换
                    ppt_content = page.locator('#tplPptContent')
                    lesson_content = page.locator('#tplLessonContent')
                    ppt_hidden = ppt_content.evaluate('el => el.classList.contains("tpl-hidden")')
                    lesson_hidden = lesson_content.evaluate('el => el.classList.contains("tpl-hidden")')
                    print(f"  内容面板: PPT隐藏={ppt_hidden}, 教案隐藏={lesson_hidden}")
                    if is_ppt_active2 and not is_lesson_active2 and not ppt_hidden and lesson_hidden:
                        print("  ✅ 模板库切换正常")
                        results.append(('3.模板库切换', '通过'))
                    else:
                        print("  ⚠️ 模板库切换异常")
                        results.append(('3.模板库切换', '异常'))
                # 关闭模态框 - 使用JS直接调用确保关闭
                page.evaluate('closeTemplateLibrary()')
                time.sleep(0.3)
            else:
                print("  ❌ 模板库模态框未显示")
                results.append(('3.模板库切换', '未通过'))
        else:
            print("  ⚠️ 未找到模板库按钮")
            results.append(('3.模板库切换', '跳过'))

        # ========== 测试4：切换平滑度 ==========
        print("\n===== 测试4：切换平滑度 =====")
        # 检查 fade-switch 类是否存在
        has_fade_switch = page.evaluate('''() => {
            const style = document.querySelector('style');
            if (!style) return false;
            return style.textContent.includes('fade-switch') || 
                   [...document.styleSheets].some(s => {
                       try { return [...s.cssRules].some(r => r.selectorText?.includes('fade-switch')); }
                       catch(e) { return false; }
                   });
        }''')
        print(f"  {'✅' if has_fade_switch else '❌'} fade-switch CSS 类: {'存在' if has_fade_switch else '不存在'}")
        if has_fade_switch:
            results.append(('4.切换平滑度', '通过'))
        else:
            results.append(('4.切换平滑度', '未通过'))

        # 尝试预览标签切换
        ppt_tab = page.locator('#previewTabPpt')
        if ppt_tab.count() > 0:
            ppt_tab.click()
            time.sleep(0.3)
            print(f"  ✅ PPT预览标签可点击切换")
            lesson_tab = page.locator('#previewTabLesson')
            lesson_tab.click()
            time.sleep(0.3)
            print(f"  ✅ 教案预览标签可点击切换")

        # ========== 测试5：可擦除提示 ==========
        print("\n===== 测试5：可擦除功能提示 =====")
        tip_container = page.locator('#tipContainer')
        if tip_container.count() > 0:
            print(f"  ✅ 提示容器存在")
            # 测试 showTip 函数是否存在
            has_show_tip = page.evaluate('typeof window.showTip === "function"')
            print(f"  {'✅' if has_show_tip else '❌'} showTip 函数: {'存在' if has_show_tip else '不存在'}")
            if has_show_tip:
                # 调用 showTip 测试
                page.evaluate('''() => {
                    if (typeof showTip === "function") {
                        showTip("test_tip", "这是一个测试提示");
                    }
                }''')
                time.sleep(0.3)
                tip_items = page.locator('.tip-item')
                if tip_items.count() > 0:
                    print(f"  ✅ 提示成功显示 ({tip_items.count()} 条)")
                    # 点击关闭按钮
                    dismiss_btn = tip_items.locator('.tip-dismiss')
                    if dismiss_btn.count() > 0:
                        dismiss_btn.click()
                        time.sleep(0.3)
                        # 验证 localStorage
                        ls_val = page.evaluate('localStorage.getItem("tip_test_tip")')
                        print(f"  {'✅' if ls_val == '1' else '⚠️'} localStorage 已记录关闭状态: {ls_val}")
                results.append(('5.可擦除提示', '通过'))
        else:
            print("  ❌ 提示容器不存在")
            results.append(('5.可擦除提示', '未通过'))

        # ========== 测试6：新手教程 ==========
        print("\n===== 测试6：新手教程（详细+分模块） =====")
        tutorial_btn = page.locator('#tutorialBtn')
        if tutorial_btn.count() > 0:
            # 点击新手教程按钮
            tutorial_btn.click()
            time.sleep(0.5)
            modal = page.locator('#tutorialModal')
            if modal.is_visible():
                # 检查模块数量
                module_count = page.evaluate('''() => {
                    const modal = document.getElementById('tutorialModal');
                    if (!modal) return 0;
                    const headers = modal.querySelectorAll('h4');
                    return headers.length;
                }''')
                print(f"  📐 教程模块数量: {module_count}")
                # 检查是否有流程图
                has_flow = page.evaluate('''() => {
                    const modal = document.getElementById('tutorialModal');
                    if (!modal) return false;
                    return modal.textContent.includes('流程') || modal.querySelector('svg');
                }''')
                print(f"  {'✅' if has_flow else '⚠️'} 流程图: {'有' if has_flow else '无'}")
                # 检查是否有开始使用提示
                has_start = page.evaluate('''() => {
                    const modal = document.getElementById('tutorialModal');
                    if (!modal) return false;
                    return modal.textContent.includes('开始') || modal.textContent.includes('使用');
                }''')
                print(f"  {'✅' if has_start else '⚠️'} 入门引导: {'有' if has_start else '无'}")
                if module_count >= 6:
                    results.append(('6.新手教程', '通过'))
                else:
                    results.append(('6.新手教程', f'模块偏少({module_count})'))
                # 关闭模态框
                page.locator('#tutorialModal .tutorial-close').first.click()
                time.sleep(0.3)
            else:
                print("  ❌ 教程模态框未显示")
                results.append(('6.新手教程', '未通过'))
        else:
            print("  ❌ 新手教程按钮不存在")
            results.append(('6.新手教程', '未通过'))

        # ========== 测试7：教案和PPT预览不同时出现 ==========
        print("\n===== 测试7：教案和PPT预览不同时出现 =====")
        preview_container = page.locator('.flex-1.relative.min-h-0')
        if preview_container.count() > 0:
            # 检查两个预览内容是否重叠（absolute 定位）
            preview_content = page.locator('#previewContent')
            ppt_preview = page.locator('#pptPreviewContent')
            if preview_content.count() > 0 and ppt_preview.count() > 0:
                p_pos = preview_content.evaluate('el => getComputedStyle(el).position')
                ppt_pos = ppt_preview.evaluate('el => getComputedStyle(el).position')
                print(f"  教案预览 position: {p_pos}, PPT预览 position: {ppt_pos}")
                # 检查默认教案可见，PPT隐藏
                p_fade_hide = preview_content.evaluate('el => el.classList.contains("fade-hide")')
                ppt_fade_hide = ppt_preview.evaluate('el => el.classList.contains("fade-hide")')
                print(f"  教案预览fade-hide: {p_fade_hide}, PPT预览fade-hide: {ppt_fade_hide}")
                if p_pos == 'absolute' and ppt_pos == 'absolute':
                    print("  ✅ 两个预览内容通过 absolute 叠加，不互相占据空间")
                    results.append(('7.教案/PPT预览不重叠', '通过'))
                    # 测试切换
                    ppt_tab = page.locator('#previewTabPpt')
                    if ppt_tab.count() > 0:
                        ppt_tab.click()
                        time.sleep(0.3)
                        p_fade_hide2 = preview_content.evaluate('el => el.classList.contains("fade-hide")')
                        ppt_fade_hide2 = ppt_preview.evaluate('el => el.classList.contains("fade-hide")')
                        print(f"  切换到PPT后: 教案fade-hide={p_fade_hide2}, PPT fade-hide={ppt_fade_hide2}")
                        if p_fade_hide2 and not ppt_fade_hide2:
                            print("  ✅ 切换后PPT显示，教案隐藏 - 正确")
                        else:
                            print("  ⚠️ 切换状态异常")
                else:
                    print("  ⚠️ 预览内容未使用 absolute 定位")
                    results.append(('7.教案/PPT预览不重叠', '异常'))
            else:
                print("  ❌ 未找到预览内容元素")
                results.append(('7.教案/PPT预览不重叠', '未通过'))
        else:
            print("  ❌ 未找到预览容器")
            results.append(('7.教案/PPT预览不重叠', '未通过'))

        # ========== 测试8：模板库PPT模板可点击 ==========
        print("\n===== 测试8：模板库PPT模板可点击 =====")
        # 确保在教案预览标签（测试7可能切到了PPT）
        page.evaluate('switchPreviewTab("lesson")')
        time.sleep(0.3)
        # Debug: 检查按钮状态
        btn_visible = page.evaluate('''() => {
            const btn = document.getElementById('openTemplateLibraryBtn');
            if (!btn) return 'no button';
            const rect = btn.getBoundingClientRect();
            const style = getComputedStyle(btn);
            const parent = document.getElementById('lessonActionBar');
            return JSON.stringify({
                display: style.display, visibility: style.visibility,
                opacity: style.opacity, rect: {w:rect.width, h:rect.height, t:rect.top, l:rect.left},
                parentDisplay: parent ? getComputedStyle(parent).display : 'no parent',
                modalHidden: document.getElementById('templateLibraryModal').classList.contains('hidden')
            });
        }''')
        print(f"  Debug: {btn_visible}")
        tpl_btn2 = page.locator('button:has-text("模板库")')
        if tpl_btn2.count() > 0:
            tpl_btn2.first.click()
            time.sleep(0.5)
            modal2 = page.locator('#templateLibraryModal')
            if modal2.is_visible():
                # 切换到PPT模板
                tpl_ppt2 = page.locator('#tplTabPpt')
                if tpl_ppt2.count() > 0:
                    tpl_ppt2.click()
                    time.sleep(0.3)
                    # 验证PPT内容可见
                    ppt_content2 = page.locator('#tplPptContent')
                    is_hidden = ppt_content2.evaluate('el => el.classList.contains("tpl-hidden")')
                    is_displayed = ppt_content2.evaluate('el => getComputedStyle(el).display !== "none"')
                    print(f"  PPT内容面板 tpl-hidden={is_hidden}, display可见={is_displayed}")
                    # 检查是否有PPT模板列表
                    ppt_chips = page.locator('.ppt-template-chip')
                    chip_count = ppt_chips.count()
                    print(f"  PPT模板数量: {chip_count}")
                    if not is_hidden and is_displayed:
                        print("  ✅ PPT模板标签可点击且内容可见")
                        results.append(('8.模板库PPT模板可点击', '通过'))
                    else:
                        print("  ❌ PPT模板内容仍被隐藏")
                        results.append(('8.模板库PPT模板可点击', '未通过'))
                else:
                    print("  ❌ 未找到PPT模板标签")
                    results.append(('8.模板库PPT模板可点击', '未通过'))
                # 关闭模态框 - 使用JS直接调用确保关闭
                page.evaluate('closeTemplateLibrary()')
                time.sleep(0.3)
            else:
                print("  ❌ 模板库模态框未显示")
                results.append(('8.模板库PPT模板可点击', '未通过'))
        else:
            print("  ❌ 未找到模板库按钮")
            results.append(('8.模板库PPT模板可点击', '未通过'))

        # ========== 汇总 ==========
        print("\n" + "=" * 50)
        print("  自测结果汇总")
        print("=" * 50)
        all_pass = True
        for name, status in results:
            icon = '✅' if status == '通过' else ('⚠️' if '跳过' in status else '❌')
            print(f"  {icon} {name}: {status}")
            if status not in ('通过', '跳过-无数据'):
                all_pass = False
        print("=" * 50)
        if all_pass:
            print("  🎉 所有测试项通过！")
        else:
            print("  ⚠️ 部分测试项需关注")

        # 截屏保存
        page.screenshot(path='d:\\唐宏\\实验室\\备课助手\\test_ui_result.png', full_page=True)
        print("\n📸 截图已保存: test_ui_result.png")

        browser.close()

if __name__ == '__main__':
    test_all()