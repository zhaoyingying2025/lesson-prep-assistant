import requests, io, json

base = 'http://127.0.0.1:8000'

# 1. 测试 extract-progress 端点
r = requests.get(base + '/api/courses/1/extract-progress', timeout=10)
data = r.json()
print('[extract-progress] status=%d, data=%s' % (r.status_code, json.dumps(data, ensure_ascii=False)[:200]))

# 2. 获取默认模板并测试 upload-docx
r = requests.get(base + '/api/lesson-templates', params={'course_id': None}, timeout=10)
templates = r.json().get('data', [])
default = [t for t in templates if t.get('is_default')]
if default:
    tpl_id = default[0]['id']
    print('[默认模板] id=%d' % tpl_id)
    
    r = requests.get(base + '/api/lesson-templates/%d/download' % tpl_id, timeout=20)
    docx_bytes = r.content
    print('[下载模板] %d bytes' % len(docx_bytes))
    
    buf = io.BytesIO(docx_bytes)
    r = requests.put(base + '/api/lesson-templates/%d/upload-docx' % tpl_id,
                     files={'file': ('test.docx', buf, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')},
                     timeout=30)
    data = r.json()
    print('[upload-docx] status=%d, success=%s, msg=%s' % (r.status_code, data.get('success'), data.get('message','')))
    
    buf = io.BytesIO(b'not a docx file')
    r = requests.put(base + '/api/lesson-templates/%d/upload-docx' % tpl_id,
                     files={'file': ('test.txt', buf, 'text/plain')},
                     timeout=30)
    data = r.json()
    print('[upload-docx 错误格式] status=%d, success=%s, msg=%s' % (r.status_code, data.get('success'), data.get('message','')[:80]))

print('\n✅ 新增端点验证完成')