import sys, json, urllib.request
url = "http://127.0.0.1:8000/api/courses/14/chat-messages"
with urllib.request.urlopen(url) as resp:
    r = json.loads(resp.read().decode("utf-8"))
msgs = r.get("data", [])
print("count:", len(msgs))
for m in msgs:
    role = m.get("role", "")
    content = (m.get("content", "") or "")[:80]
    print(f"  [{role}] {content}")
