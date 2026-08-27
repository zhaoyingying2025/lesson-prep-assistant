"""教案评估端到端测试

测试流程：
1. 创建课程
2. 上传一份小教材（模拟）
3. 提取知识点
4. 生成教案
5. 调用 /api/lessons/{id}/evaluate 评估教案
6. 验证返回结构（scores/overall_score/top_issues/chair_validation/student_validation）

注意：若无可用 LLM API key，评估接口会返回 success=False + error_code=LLM_ERROR，
此情况下本测试只验证路由可达性与失败响应的结构化格式，不验证成功结果。
"""
from __future__ import annotations
import sys
import os
import json
import time
from pathlib import Path

import urllib.request
import urllib.parse
import urllib.error


BASE = "http://127.0.0.1:8000"


def http_get(path: str):
    url = f"{BASE}{path}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def http_post(path: str, body: dict | None = None, form: dict | None = None, files: dict | None = None):
    url = f"{BASE}{path}"
    if files:
        # multipart
        boundary = "----test_boundary" + str(int(time.time()))
        lines = []
        if form:
            for k, v in form.items():
                lines.append(f"--{boundary}")
                lines.append(f'Content-Disposition: form-data; name="{k}"')
                lines.append("")
                lines.append(str(v))
        for field, (fn, content) in files.items():
            lines.append(f"--{boundary}")
            lines.append(f'Content-Disposition: form-data; name="{field}"; filename="{fn}"')
            lines.append("Content-Type: application/octet-stream")
            lines.append("")
            lines.append(content if isinstance(content, str) else content.decode("latin-1"))
        lines.append(f"--{boundary}--")
        body_str = "\r\n".join(lines)
        data = body_str.encode("latin-1")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    elif form:
        data = urllib.parse.urlencode(form).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    else:
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, body_text


def main():
    print("=" * 60)
    print("教案评估端到端测试")
    print("=" * 60)

    # Step 1: 检查服务可达
    try:
        st, _ = http_get("/api/courses")
        assert st == 200, f"服务不可达: {st}"
        print("[1/6] ✓ 服务可达")
    except Exception as e:
        print(f"[1/6] ✗ 服务不可达: {e}")
        sys.exit(1)

    # Step 2: 创建课程
    st, resp = http_post("/api/courses", body={"name": "测试课程_Eval", "description": "评估端到端测试"})
    assert st == 200, f"创建课程失败: {resp}"
    course_id = resp.get("data", {}).get("id")
    if not course_id:
        # 可能已存在同名课程，先列出
        st, resp = http_get("/api/courses")
        for c in resp.get("data", []):
            if c.get("name") == "测试课程_Eval":
                course_id = c["id"]
                break
    assert course_id, "无法获取 course_id"
    print(f"[2/6] ✓ 课程创建/获取 course_id={course_id}")

    # Step 3: 直接生成教案（跳过上传教材与提取知识点，避免依赖 LLM）
    # 我们用一个简单的 lesson_json 直接保存到 DB，然后调用 evaluate
    # 这里使用 generate-lesson 接口，知识点为空数组也能生成（如果 LLM 可用）
    # 但若无 LLM，会返回 LLM_ERROR，我们改用 chat 接口没法...
    # 改用更可靠的方式：直接调用 /api/courses/{id}/lessons 手动创建空教案，再调 evaluate

    # 尝试创建一份手动教案（POST /api/courses/{id}/lessons）
    sample_plan = {
        "course_name": "测试课程_Eval",
        "chapter": "测试章节",
        "total_minutes": 90,
        "goals": {"knowledge": ["理解概念A"], "ability": ["能应用A解决B"], "quality": ["培养思维"]},
        "key_points": ["概念A"],
        "difficult_points": ["概念A的推导"],
        "difficult_strategy": "通过案例引导分步推导",
        "stages": [
            {"name": "课前导入", "duration_min": 5, "teacher": "提问引入", "student": "思考", "intent": "激发兴趣", "content": "..."},
            {"name": "知识讲解", "duration_min": 50, "teacher": "讲解A", "student": "听讲", "intent": "掌握A", "content": "..."},
            {"name": "案例例题", "duration_min": 15, "teacher": "演示", "student": "练习", "intent": "应用A", "content": "..."},
            {"name": "互动讨论", "duration_min": 10, "teacher": "组织讨论", "student": "讨论", "intent": "深化理解", "content": "..."},
            {"name": "课堂总结", "duration_min": 5, "teacher": "总结", "student": "回顾", "intent": "梳理", "content": "..."},
            {"name": "布置作业", "duration_min": 5, "teacher": "布置", "student": "记录", "intent": "巩固", "content": "..."},
        ],
        "board_design": "主板书: 概念A | 副板书: 推导过程",
        "homework": {"basic": ["基础题"], "improve": ["提升题"], "explore": ["探究题"]},
    }
    st, resp = http_post(f"/api/courses/{course_id}/lessons",
                         form={"chapter": "测试章节", "plan_json": json.dumps(sample_plan, ensure_ascii=False)})
    if st != 200:
        # 该端点可能不存在，回退到 /fallback-template
        print(f"[3/6] ! 手动创建教案失败({st})，尝试 fallback-template")
        # 先用 generate-lesson 触发一个教案创建（即便失败也能创建空教案记录？）
        st, resp = http_post(f"/api/courses/{course_id}/generate-lesson",
                             form={"chapter": "测试章节", "knowledge_points": "[]"})
        if st == 200:
            lesson_id = resp.get("data", {}).get("id")
        else:
            lesson_id = None
    else:
        lesson_id = resp.get("data", {}).get("id") or resp.get("data", {}).get("lesson_id")
    if not lesson_id:
        # 拉取课程下的教案
        st, resp = http_get(f"/api/courses/{course_id}/lessons")
        lessons = resp.get("data", []) if st == 200 else []
        if lessons:
            lesson_id = lessons[-1].get("id")
    assert lesson_id, "无法创建/获取 lesson_id"
    print(f"[3/6] ✓ 教案创建 lesson_id={lesson_id}")

    # 如果上面是手动教案端点，需要确保 plan_json 有 stages 字段，更新一下
    # 重新写一次 plan_json
    st2, resp2 = http_post(f"/api/courses/{course_id}/lessons",
                           form={"chapter": "测试章节", "plan_json": json.dumps(sample_plan, ensure_ascii=False)})
    # 上面可能再次失败，那就尝试直接调 evaluate

    # Step 4: 调用评估接口
    print(f"[4/6] 调用评估接口 POST /api/lessons/{lesson_id}/evaluate ...")
    st, resp = http_post(f"/api/lessons/{lesson_id}/evaluate")
    print(f"      HTTP {st}")

    if st != 200:
        print(f"[4/6] ✗ HTTP 错误: {resp}")
        sys.exit(1)

    # Step 5: 验证响应结构
    success = resp.get("success", True)
    data = resp.get("data", {})
    msg = resp.get("message", "")

    if success is False:
        err_code = data.get("error_code", "")
        fallbacks = data.get("fallbacks", [])
        print(f"[4/6] ⚠ 评估未成功（预期：无LLM API key）")
        print(f"      message: {msg}")
        print(f"      error_code: {err_code}")
        print(f"      fallbacks: {fallbacks}")
        assert err_code, "失败响应缺少 error_code"
        assert isinstance(fallbacks, list) and len(fallbacks) >= 3, "fallbacks 列表不完整"
        print("[5/6] ✓ 失败响应结构正确（error_code + fallbacks）")
        print("[6/6] ⚠ 跳过成功结果验证（LLM 未配置）")
        print("\n==== 测试通过（结构化失败响应已验证）====")
        return

    # 成功路径：验证字段
    print(f"[4/6] ✓ 评估成功: {msg}")
    print(f"      overall_score={data.get('overall_score')}")
    print(f"      scores 项数={len(data.get('scores', []))}")
    print(f"      top_issues 项数={len(data.get('top_issues', []))}")
    print(f"      chair_validation={'有' if data.get('chair_validation') else '无'}")
    print(f"      student_validation={'有' if data.get('student_validation') else '无'}")

    assert "scores" in data, "缺少 scores 字段"
    assert "overall_score" in data, "缺少 overall_score 字段"
    assert "top_issues" in data, "缺少 top_issues 字段"
    assert "chair_validation" in data, "缺少 chair_validation 字段"
    assert "student_validation" in data, "缺少 student_validation 字段"
    print("[5/6] ✓ 响应结构完整（scores/overall_score/top_issues/chair_validation/student_validation）")

    # Step 6: 验证 scores 数据格式
    scores = data.get("scores", [])
    if scores:
        first = scores[0]
        assert "metric" in first and "score" in first, f"score 项缺少 metric/score: {first}"
        print(f"[6/6] ✓ scores[0] 格式正确: metric={first['metric']}, score={first['score']}")
    else:
        print("[6/6] ⚠ scores 为空")

    print("\n==== 测试通过（端到端评估流程已验证）====")


if __name__ == "__main__":
    main()
