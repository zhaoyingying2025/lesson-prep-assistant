import json, urllib.request
url = "http://127.0.0.1:8000/api/lesson-templates"
with urllib.request.urlopen(url) as resp:
    r = json.loads(resp.read().decode("utf-8"))
tpls = r.get("data", [])
print("count:", len(tpls))
for t in tpls:
    print(f"  id={t.get('id')} name={t.get('name')} default={t.get('is_default')} course_id={t.get('course_id')}")
