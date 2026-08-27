"""多教材版本管理冒烟测试

验证：
1. 创建课程
2. 上传两本教材（带 version_label 和 is_primary 标记）
3. 列表接口返回 version_label 和 is_primary 字段
4. set-primary 切换主教材
5. update_material 修改版本标签

注意：避免真实 LLM 调用，仅测试 CRUD 与字段透传。
"""
from __future__ import annotations

import io
import sys
import time
import urllib.request
import json
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8000"
TMP = Path(__file__).resolve().parent / "_tmp_smoke_textbook"
TMP.mkdir(exist_ok=True)


def _req(method: str, path: str, body: bytes | None = None,
         headers: dict | None = None, is_form: bool = False):
    url = BASE + path
    h = headers or {}
    if body is not None and not is_form:
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def assert_true(cond: bool, msg: str):
    if not cond:
        print(f"[FAIL] {msg}")
        sys.exit(1)
    print(f"[OK]   {msg}")


def make_text(name: str, content: str) -> tuple[bytes, str]:
    """构造一个 multipart form 文件 part 的最小可用纯文本 .txt 文件"""
    p = TMP / name
    p.write_text(content, encoding="utf-8")
    return p.read_bytes(), name


# ---------- 1. 创建课程 ----------
print("\n[1] 创建课程")
status, body = _req("POST", "/api/courses", body=json.dumps({
    "name": "多教材测试课程",
    "description": "smoke",
    "subject": "math",
}).encode("utf-8"))
assert_true(status == 200, f"创建课程 HTTP 200 (got {status})")
course = json.loads(body)["data"]
course_id = course["id"]
print(f"  course_id = {course_id}")


# ---------- 2. 上传主教材（人教版 + is_primary=true） ----------
print("\n[2] 上传主教材（人教版 + is_primary=true）")
file_bytes, fname = make_text("renjiao.txt", (
    "第一章 函数与极限\n"
    "1.1 函数的概念\n"
    "设 x 和 y 是两个变量，D 是一个给定的数集..."
    "（人教版教材内容）\n" * 5
))
# 手动构造 multipart/form-data
boundary = "----smoke_boundary_" + str(int(time.time()))
parts = []
parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\n"
             "Content-Type: text/plain\r\n\r\n".encode("utf-8") + file_bytes + b"\r\n")
parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"material_type\"\r\n\r\ntextbook\r\n".encode("utf-8"))
parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"version_label\"\r\n\r\n人教版\r\n".encode("utf-8"))
parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"is_primary\"\r\n\r\ntrue\r\n".encode("utf-8"))
parts.append(f"--{boundary}--\r\n".encode("utf-8"))
payload = b"".join(parts)
status, body = _req("POST", f"/api/courses/{course_id}/materials", body=payload,
                   headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, is_form=True)
assert_true(status == 200, f"上传主教材 HTTP 200 (got {status})")
up1 = json.loads(body)["data"]
assert_true(up1.get("version_label") == "人教版", f"version_label 透传 = 人教版 (got {up1.get('version_label')!r})")
assert_true(up1.get("is_primary") is True, f"is_primary = True (got {up1.get('is_primary')!r})")
mat1_id = up1["id"]
print(f"  material_id = {mat1_id}")


# ---------- 3. 上传副教材（高教版，未设主教材） ----------
print("\n[3] 上传副教材（高教版）")
file_bytes2, fname2 = make_text("gaojiao.txt", (
    "第一章 函数\n"
    "1.1 函数定义\n"
    "若对于某个范围内的每个 x 值..."
    "（高教版教材内容）\n" * 5
))
parts2 = []
parts2.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname2}\"\r\n"
              "Content-Type: text/plain\r\n\r\n".encode("utf-8") + file_bytes2 + b"\r\n")
parts2.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"material_type\"\r\n\r\ntextbook\r\n".encode("utf-8"))
parts2.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"version_label\"\r\n\r\n高教版\r\n".encode("utf-8"))
parts2.append(f"--{boundary}--\r\n".encode("utf-8"))
payload2 = b"".join(parts2)
status, body = _req("POST", f"/api/courses/{course_id}/materials", body=payload2,
                   headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, is_form=True)
assert_true(status == 200, f"上传副教材 HTTP 200 (got {status})")
up2 = json.loads(body)["data"]
assert_true(up2.get("version_label") == "高教版", f"version_label 透传 = 高教版 (got {up2.get('version_label')!r})")
assert_true(up2.get("is_primary") is False, f"副教材 is_primary = False (got {up2.get('is_primary')!r})")
mat2_id = up2["id"]
print(f"  material_id = {mat2_id}")


# ---------- 4. 列表接口返回 version_label + is_primary ----------
print("\n[4] GET /materials 返回 version_label + is_primary")
status, body = _req("GET", f"/api/courses/{course_id}/materials")
assert_true(status == 200, f"列表 HTTP 200 (got {status})")
mats = json.loads(body)["data"]
assert_true(len(mats) == 2, f"共 2 本教材 (got {len(mats)})")
# 第一个上传的是主教材
m1 = next(m for m in mats if m["id"] == mat1_id)
m2 = next(m for m in mats if m["id"] == mat2_id)
assert_true(m1.get("version_label") == "人教版" and m1.get("is_primary") is True,
            f"主教材字段正确 (got v={m1.get('version_label')!r} p={m1.get('is_primary')!r})")
assert_true(m2.get("version_label") == "高教版" and m2.get("is_primary") is False,
            f"副教材字段正确 (got v={m2.get('version_label')!r} p={m2.get('is_primary')!r})")


# ---------- 5. set-primary 切换主教材 ----------
print("\n[5] 切换主教材到副教材")
status, body = _req("PUT", f"/api/materials/{mat2_id}/set-primary")
assert_true(status == 200, f"set-primary HTTP 200 (got {status})")
status, body = _req("GET", f"/api/courses/{course_id}/materials")
mats = json.loads(body)["data"]
m1 = next(m for m in mats if m["id"] == mat1_id)
m2 = next(m for m in mats if m["id"] == mat2_id)
assert_true(m2.get("is_primary") is True, f"切换后 mat2 is_primary=True")
assert_true(m1.get("is_primary") is False, f"切换后 mat1 is_primary=False (同课程仅一本主教材)")


# ---------- 6. update_material 修改 version_label ----------
print("\n[6] update_material 修改版本标签")
status, body = _req("PUT", f"/api/materials/{mat1_id}", body=json.dumps({
    "version_label": "人教版(2024修订)",
}).encode("utf-8"))
assert_true(status == 200, f"update_material HTTP 200 (got {status})")
upd = json.loads(body)["data"]
assert_true(upd.get("version_label") == "人教版(2024修订)",
            f"version_label 更新成功 (got {upd.get('version_label')!r})")


# ---------- 清理 ----------
print("\n[7] 清理测试数据")
_req("DELETE", f"/api/courses/{course_id}")
print("\n=== ALL SMOKE TESTS PASSED ===")
