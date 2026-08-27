import requests, json
r = requests.post('http://127.0.0.1:8000/api/lessons/15/export-ppt', json={'style':'clean','density':'normal'}, timeout=30)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type","")}')
print(f'Body: {r.text[:1000]}')