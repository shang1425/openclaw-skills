"""
taskflow 测试套件
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.schema import Task, TaskProject, TaskStatus, Priority
from src.engine import decompose, rule_based_split, infer_priority, estimate_minutes


# ── Schema 测试 ───────────────────────────────────────────────

def test_task_creation():
    t = Task(id="T001", title="设计 Schema", priority=Priority.A)
    assert t.id == "T001"
    assert t.title == "设计 Schema"
    assert t.priority == Priority.A
    assert t.status == TaskStatus.PENDING
    d = t.to_dict()
    assert d["priority"] == "A"
    assert d["status"] == "pending"
    print("✅ test_task_creation")


def test_task_project():
    p = TaskProject(id="PRJ001", name="测试项目", source="unit-test")
    t1 = p.add_task("任务一", priority=Priority.A)
    t2 = p.add_task("任务二", priority=Priority.B)
    t2.depends_on.append(t1.id)

    assert len(p.tasks) == 2
    assert p.get_task(t1.id) is not None, f"task {t1.id} not found"
    assert p.get_task("TX") is None

    # 测试依赖满足判断
    ready = p.get_ready_tasks()
    assert len(ready) == 1, f"expected 1 ready, got {len(ready)}: {[t.id for t in ready]}"
    assert ready[0].id == t1.id, f"expected {t1.id} ready, got {ready[0].id}"
    print("✅ test_task_project")


def test_status_update():
    p = TaskProject(id="PRJ002", name="测试")
    t1 = p.add_task("任务一")
    t2 = p.add_task("任务二")
    t2.depends_on.append(t1.id)
    p.update_task_status(t1.id, TaskStatus.DONE)
    assert p.get_task(t1.id).status == TaskStatus.DONE
    assert p.get_task(t1.id).done_at is not None
    # 任务二依赖任务一，任务一完成后任务二变为可执行
    ready = p.get_ready_tasks()
    assert len(ready) == 1 and ready[0].id == t2.id, f"expected {t2.id} ready, got {[t.id for t in ready]}"
    print("✅ test_status_update")


def test_markdown_output():
    p = TaskProject(id="PRJ003", name="MD测试")
    p.add_task("任务A", priority=Priority.A)
    p.add_task("任务B", priority=Priority.B)
    md = p.to_markdown()
    assert "MD测试" in md
    assert "任务A" in md
    assert "📋 待处理" in md
    print("✅ test_markdown_output")


# ── Engine 测试 ───────────────────────────────────────────────

def test_infer_priority():
    assert infer_priority("立刻修复这个bug") == Priority.A
    assert infer_priority("尽快完成") == Priority.B
    assert infer_priority("可以考虑优化") == Priority.C
    assert infer_priority("重要：需要处理") == Priority.B
    assert infer_priority("随便做一下") == Priority.D
    print("✅ test_infer_priority")


def test_estimate_minutes():
    assert estimate_minutes("预计30分钟") == 30
    assert estimate_minutes("2小时完成") == 120
    assert estimate_minutes("需要3个小时") == 180
    assert estimate_minutes("5min") == 5
    print("✅ test_estimate_minutes")


def test_rule_based_split_basic():
    text = """
第一步：设计任务 Schema
第二步：开发拆解引擎
第三步：写测试用例
    """
    p = rule_based_split(text, source="test")
    assert len(p.tasks) == 3
    assert p.tasks[0].title == "设计任务 Schema"
    assert p.tasks[1].depends_on == [p.tasks[0].id]
    print("✅ test_rule_based_split_basic")


def test_rule_based_split_action_verbs():
    text = """
设计任务数据结构
开发拆解引擎
写测试用例
上线发布
    """
    p = rule_based_split(text)
    assert len(p.tasks) >= 4
    titles = [t.title for t in p.tasks]
    assert any("设计" in t for t in titles)
    print("✅ test_rule_based_split_action_verbs")


def test_decompose_real_world():
    """真实场景：从 deepthink 结论中拆解"""
    text = """
## 结论

1. 【A】立刻：修复 memory_search 在长文本时崩溃的问题
2. 【B】本周：实现 taskflow v1.0 任务拆解引擎
3. 【C】可选：增加 Markdown 导出功能
4. 【D】选做：做 UI 界面
    """
    p = decompose(text, source="deepthink-v4-fix")
    assert len(p.tasks) >= 3
    # 应该有 A/B/C 优先级的任务
    priorities = {t.priority for t in p.tasks}
    assert Priority.A in priorities or Priority.B in priorities
    print("✅ test_decompose_real_world")


def test_decompose_with_source():
    text = "设计任务 Schema\n开发拆解引擎"
    p = decompose(text, source="taskflow-v1")
    assert p.source == "taskflow-v1"
    assert len(p.tasks) >= 2
    print("✅ test_decompose_with_source")


# ── 运行全部 ──────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_task_creation,
        test_task_project,
        test_status_update,
        test_markdown_output,
        test_infer_priority,
        test_estimate_minutes,
        test_rule_based_split_basic,
        test_rule_based_split_action_verbs,
        test_decompose_real_world,
        test_decompose_with_source,
    ]

    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"💥 {t.__name__}: {e}")

    print(f"\n{'='*40}")
    print(f"结果：{passed}/{len(tests)} 通过")
