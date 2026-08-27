"""快速检查页面元素"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    html = page.content()
    checks = [
        "fullscreenLessonModal", "toggleEditBtn", "saveLessonBtn",
        "closeFullscreenBtn", "templateLibraryModal", "openTemplateLibraryBtn",
        "genLessonBtn", "genPPTBtn"
    ]
    print(f"HTML长度: {len(html)}")
    print()
    for c in checks:
        in_html = c in html
        dom_count = page.locator(f"#{c}").count()
        status = "✅" if in_html else "❌"
        print(f"  #{c}: HTML中={status}, DOM查询={dom_count}个")
    browser.close()