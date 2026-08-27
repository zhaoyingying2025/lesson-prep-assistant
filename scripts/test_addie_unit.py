"""ADDIE 多智能体审议流程单元测试

用 mock LLM 验证 lesson_agent_addie.generate_lesson_with_addie 的 4 阶段串联：
  Analyze → Develop → Evaluate → Refine(条件触发)
不调用真实 LLM，确保测试可在无 API key 环境下运行。
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# 把项目根加到 sys.path，便于直接导入
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def make_mock_llm():
    """构造一个 mock LLM，按调用顺序返回预设 JSON"""
    calls = []

    # 各阶段预设返回
    analyze_resp = {
        "prior_knowledge": "学生已掌握一元二次方程与基本初等函数概念",
        "cognitive_obstacles": ["极限的ε-δ定义抽象", "无穷小量比较易混淆"],
        "key_strategies": ["用图示引入极限直观理解", "用对比表呈现无穷小量阶"],
        "learner_summary": "学生整体基础扎实，但抽象推理能力较弱，本节难点为极限形式化定义",
    }
    develop_resp = {
        "course_name": "高等数学",
        "chapter": "第一章 函数与极限",
        "total_minutes": 90,
        "teaching_object": "大一新生",
        "teacher_name": "",
        "knowledge_goal": "掌握函数与极限的基本概念",
        "ability_goal": "能用极限语言描述函数变化趋势",
        "value_goal": "培养严谨的数学思维",
        "key_points": ["函数概念(P23)", "极限定义(P25)"],
        "difficult_points": ["ε-δ语言(P26)"],
        "difficult_strategy": "图示+分步推导",
        "stages": [
            {"name": "课前导入", "duration_min": 8, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
            {"name": "知识讲解", "duration_min": 50, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
            {"name": "案例例题", "duration_min": 15, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
            {"name": "互动讨论", "duration_min": 10, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
            {"name": "课堂总结", "duration_min": 5, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
            {"name": "布置作业", "duration_min": 2, "teacher_activity": "...", "student_activity": "...", "design_intent": "...", "content": "..."},
        ],
        "board_design": "主板书：极限定义\n副板书：推导过程",
        "homework": ["【基础】习题1(P30)", "【提升】习题2(P31)"],
        "reflection": "（课后填写）",
    }
    # 测试 Refine 触发：评估返回 needs_refine=true
    evaluate_resp_with_refine = {
        "overall_score": 70,
        "issues": [
            {"dimension": "结构完整性", "severity": "error", "description": "六阶段时间总和为90，但案例例题时间过短", "suggestion": "将案例例题从15min提到20min，从知识讲解扣除5min"},
        ],
        "needs_refine": True,
        "refine_focus": "调整案例例题与知识讲解的时间分配",
    }
    refine_resp = json.loads(json.dumps(develop_resp))  # 深拷贝
    refine_resp["stages"][1]["duration_min"] = 45  # 知识讲解 -5min
    refine_resp["stages"][2]["duration_min"] = 20  # 案例例题 +5min
    refine_resp["stages"][1]["content"] = "（精修后）知识讲解内容..."
    # 测试 Refine 不触发：评估返回 needs_refine=false
    evaluate_resp_no_refine = {
        "overall_score": 92,
        "issues": [],
        "needs_refine": False,
        "refine_focus": "",
    }

    # 调用顺序：analyze, develop, evaluate, [refine]
    responses_with_refine = [analyze_resp, develop_resp, evaluate_resp_with_refine, refine_resp]
    responses_no_refine = [analyze_resp, develop_resp, evaluate_resp_no_refine]

    class _MockLLM:
        def __init__(self, seq):
            self._seq = list(seq)
            self.calls = []

        async def chat_json(self, system_prompt, user_prompt, temperature=0.7):
            self.calls.append({
                "system": system_prompt[:40],
                "user": user_prompt[:80],
                "temperature": temperature,
            })
            if not self._seq:
                raise RuntimeError("unexpected extra LLM call")
            return self._seq.pop(0)

    return _MockLLM, responses_with_refine, responses_no_refine, calls


async def run_case(case_name: str, expect_refine: bool):
    _MockLLM, with_refine, no_refine, _ = make_mock_llm()
    seq = with_refine if expect_refine else no_refine
    mock = _MockLLM(seq)

    progress_events = []

    async def progress_cb(stage, payload):
        progress_events.append({"stage": stage, "payload_keys": list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__})

    from backend.app.agents.lesson_agent_addie import generate_lesson_with_addie
    from backend.app.models.schemas import LessonParams

    params = LessonParams()

    with patch("backend.app.agents.lesson_agent_addie.get_llm", return_value=mock):
        final_dict, addie_meta = await generate_lesson_with_addie(
            course_name="高等数学",
            chapter="第一章 函数与极限",
            knowledge_points=[{"name": "函数概念", "source_pages": "P23-P25"}, {"name": "极限定义", "source_pages": "P25-P28"}],
            params=params,
            textbook_context="教材原文片段...",
            subject="math",
            progress_callback=progress_cb,
        )

    # 期望调用次数：with_refine → 4次；no_refine → 3次
    expected_calls = 4 if expect_refine else 3
    assert len(mock.calls) == expected_calls, f"[{case_name}] LLM 调用次数 = {len(mock.calls)}, 期望 {expected_calls}"
    print(f"[OK] {case_name}: LLM 调用 {len(mock.calls)} 次（符合预期）")

    # 验证 addie_meta
    assert addie_meta["mode"] == "addie"
    assert "analyze" in addie_meta["stages_run"]
    assert "develop" in addie_meta["stages_run"]
    assert "evaluate" in addie_meta["stages_run"]
    assert ("refine" in addie_meta["stages_run"]) == expect_refine
    assert addie_meta["refined"] == expect_refine
    print(f"[OK] {case_name}: stages_run = {addie_meta['stages_run']}, refined = {addie_meta['refined']}")

    # 验证学情分析完整
    la = addie_meta["learner_analysis"]
    assert la.get("learner_summary") and la.get("cognitive_obstacles") and la.get("key_strategies")
    print(f"[OK] {case_name}: 学情分析字段完整")

    # 验证评估结果
    ev = addie_meta["evaluation"]
    assert "overall_score" in ev and "issues" in ev and "needs_refine" in ev
    print(f"[OK] {case_name}: 评估 overall_score = {ev['overall_score']}, needs_refine = {ev['needs_refine']}")

    # 验证最终教案结构
    assert "stages" in final_dict and len(final_dict["stages"]) == 6
    total = sum(s["duration_min"] for s in final_dict["stages"])
    assert total == params.total_minutes, f"[{case_name}] 时间总和 {total} ≠ {params.total_minutes}"
    print(f"[OK] {case_name}: 最终教案 6 阶段, 时间总和 = {total}min")

    # 验证 progress_callback 被触发
    expected_progress = ["analyze_start", "analyze_done", "develop_start", "develop_done", "evaluate_start", "evaluate_done"]
    if expect_refine:
        expected_progress += ["refine_start", "refine_done"]
    actual_progress = [e["stage"] for e in progress_events]
    assert actual_progress == expected_progress, f"[{case_name}] 进度事件 {actual_progress} ≠ {expected_progress}"
    print(f"[OK] {case_name}: 进度回调 {len(actual_progress)} 个事件, 顺序正确")

    # 验证 Refine 后内容是否被修订
    if expect_refine:
        # 精修后案例例题应从15→20
        case_stage = next(s for s in final_dict["stages"] if s["name"] == "案例例题")
        assert case_stage["duration_min"] == 20, f"[{case_name}] 精修后案例例题时间应为20min, 实际 {case_stage['duration_min']}"
        # 知识讲解应从50→45
        teach_stage = next(s for s in final_dict["stages"] if s["name"] == "知识讲解")
        assert teach_stage["duration_min"] == 45, f"[{case_name}] 精修后知识讲解时间应为45min, 实际 {teach_stage['duration_min']}"
        print(f"[OK] {case_name}: 精修已生效，案例例题15→20min，知识讲解50→45min")


async def main():
    print("\n=== ADDIE 多智能体审议流程单元测试 ===\n")
    await run_case("Case1-触发Refine", expect_refine=True)
    print()
    await run_case("Case2-不触发Refine", expect_refine=False)
    print("\n=== ALL TESTS PASSED ===\n")


if __name__ == "__main__":
    asyncio.run(main())
