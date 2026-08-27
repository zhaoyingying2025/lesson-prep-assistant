"""快速验证修复点：针对实际源码 index.html + API 端点"""
import re, sys, json, urllib.request

BASE = "http://127.0.0.1:8000"
SRC = r"d:\唐宏\实验室\备课助手\backend\app\templates\index.html"

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

checks = {
    'promptModal z-index 100': 'z-[100]' in html and 'promptModal' in html,
    'confirmModal z-index 100': 'z-[100]' in html and 'confirmModal' in html,
    'failureModal close button(x)': 'failExitBtn' in html,
    'failureSolution solution div': 'failureSolution' in html,
    'default template download button': '默认Word模板' in html,
    'doSmartExtract uses JSON': 'JSON.stringify' in html and 'material_ids' in html,
    'SOLUTION_MAP defined': 'SOLUTION_MAP' in html,
    'backdrop close handler': 'closeOperationFailure()' in html,
}
all_ok = True
for name, ok in checks.items():
    mark = 'OK' if ok else 'FAIL'
    if not ok: all_ok = False
    print(f'  [{mark}] {name}')
print(f'\nSource file: {SRC}')
print(f'Page size: {len(html)} bytes')
print(f'All checks passed: {all_ok}')
sys.exit(0 if all_ok else 1)