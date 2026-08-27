"""调试：检查默认模板查询"""
import urllib.request, json

r = urllib.request.urlopen("http://127.0.0.1:8000/api/lesson-templates?course_id=16")
data = json.loads(r.read())
items = data.get("data", [])
print(f"Total items: {len(items)}")
for t in items:
    print(f'  id={t["id"]} name={t["name"]} is_default={t.get("is_default")} course_id={t.get("course_id")}')

default = [t for t in items if t.get("is_default")]
print(f"Default templates found: {len(default)}")

# Also test without course_id
r2 = urllib.request.urlopen("http://127.0.0.1:8000/api/lesson-templates")
data2 = json.loads(r2.read())
items2 = data2.get("data", [])
print(f"\nWithout course_id - Total items: {len(items2)}")
for t in items2:
    print(f'  id={t["id"]} name={t["name"]} is_default={t.get("is_default")} course_id={t.get("course_id")}')