"""调试测试：检查模板库按钮事件绑定"""
from playwright.sync_api import sync_playwright
import time

BASE = 'http://127.0.0.1:8001'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    page.on('console', lambda msg: print(f"  [CONSOLE {msg.type}] {msg.text}"))
    page.on('pageerror', lambda err: print(f"  [PAGE ERROR] {err}"))

    page.goto(BASE)
    page.wait_for_load_state('networkidle')
    time.sleep(2)

    # 检查按钮是否存在
    btn = page.locator('#openTemplateLibraryBtn')
    print(f"Button exists: {btn.count() > 0}")
    print(f"Button visible: {btn.is_visible()}")

    # 检查事件监听器 - 通过 JS 检查
    has_listener = page.evaluate('''() => {
        const btn = document.getElementById('openTemplateLibraryBtn');
        if (!btn) return 'no button';
        // 获取事件监听器 (需要 Chrome DevTools Protocol)
        return 'button found, id=' + btn.id;
    }''')
    print(f"JS check: {has_listener}")

    # 检查是否有全局 click 事件处理
    has_click_handler = page.evaluate('''() => {
        const btn = document.getElementById('openTemplateLibraryBtn');
        const clone = btn.cloneNode(true);
        let handlerCalled = false;
        const originalClick = btn.click;
        // 尝试获取 listeners
        return typeof btn.onclick === 'function' ? 'onclick assigned' : 'onclick not assigned';
    }''')
    print(f"onclick check: {has_click_handler}")

    # 直接检查 openTemplateLibrary 可访问性
    accessible = page.evaluate('typeof window.openTemplateLibrary')
    print(f"openTemplateLibrary accessible: {accessible}")

    # 手动分发 click 事件
    print("\n手动分发 click 事件...")
    page.evaluate('''() => {
        const btn = document.getElementById('openTemplateLibraryBtn');
        if (btn) {
            btn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            console.log('dispatched click event');
        }
    }''')
    time.sleep(0.5)

    modal = page.locator('#templateLibraryModal')
    print(f"modal visible after dispatch: {modal.is_visible()}")
    print(f"modal classes: {modal.evaluate('el => el.className')}")

    # 检查 addEventListener 是否工作 - 直接添加一个新 listener
    print("\n测试直接添加 listener...")
    page.evaluate('''() => {
        const btn = document.getElementById('openTemplateLibraryBtn');
        btn.addEventListener('click', function() {
            console.log('direct listener fired');
            window.openTemplateLibrary();
        });
    }''')
    time.sleep(0.2)

    # 点击按钮
    print("点击按钮...")
    btn.click()
    time.sleep(0.5)
    print(f"modal visible after click: {modal.is_visible()}")
    print(f"modal classes: {modal.evaluate('el => el.className')}")

    browser.close()