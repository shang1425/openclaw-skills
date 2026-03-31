"""
taskflow v2.0 测试套件 — 持久化 + CLI
"""

import sys, os, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.schema import TaskProject, Task, TaskStatus, Priority
from src.engine import decompose
from src.storage import save, load, load_latest


TMP_DIR = None


def setup():
    global TMP_DIR
    TMP_DIR = tempfile.mkdtemp()
    # Patch OUTPUT_DIR
    import src.storage as storage
    import src
    src.OUTPUT_DIR = TMP_DIR
    storage.OUTPUT_DIR = TMP_DIR


def teardown():
    if TMP_DIR and os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


def test_save_and_load():
    setup()
    try:
        p = TaskProject(id="PRJ_TEST", name="保存加载测试", source="v2-test")
        t1 = p.add_task("任务A", priority=Priority.A)
        t2 = p.add_task("任务B", priority=Priority.B)
        t2.depends_on.append(t1.id)
        p.update_task_status(t1.id, TaskStatus.DONE)

        path = save(p)
        assert os.path.exists(path), f"文件未创建: {path}"

        # 加载回来
        p2 = load(path)
        assert p2.name == "保存加载测试"
        assert len(p2.tasks) == 2
        assert p2.get_task(t1.id).status == TaskStatus.DONE
        assert p2.get_task(t2.id).depends_on == [t1.id]
        print("✅ test_save_and_load")
    finally:
        teardown()


def test_task_result():
    setup()
    try:
        p = TaskProject(id="PRJ_TEST2", name="结果记录", source="v2-test")
        t = p.add_task("写代码", priority=Priority.B)
        p.update_task_status(t.id, TaskStatus.DONE, result="学会了正则提取")

        path = save(p)
        p2 = load(path)

        loaded_task = p2.get_task(t.id)
        assert loaded_task.result == "学会了正则提取"
        assert loaded_task.done_at is not None
        print("✅ test_task_result")
    finally:
        teardown()


def test_cli_decompose():
    """验证 CLI decompose 命令能正常工作"""
    import subprocess
    result = subprocess.run(
        ["py", "-X", "utf8", "taskflow.py", "decompose",
         "立刻：修复 bug\n本周：写测试", "--source", "cli-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    assert result.returncode == 0, f"CLI 失败: {result.stderr}"
    assert "taskflow" in result.stdout.lower() or "任务" in result.stdout
    assert "bug" in result.stdout or "BUG" in result.stdout
    print("✅ test_cli_decompose")
    print(f"   输出片段: {result.stdout[:200]}")


def test_cli_list():
    setup()
    try:
        # 先创建一个项目
        p = TaskProject(id="PRJ_LIST", name="CLI列表测试", source="cli-test")
        p.add_task("任务1")
        save(p)

        import subprocess
        result = subprocess.run(
            ["py", "-X", "utf8", "taskflow.py", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0, f"CLI 失败: {result.stderr}"
        assert "CLI列表测试" in result.stdout
        print("✅ test_cli_list")
    finally:
        teardown()


if __name__ == "__main__":
    tests = [
        test_save_and_load,
        test_task_result,
        test_cli_decompose,
        test_cli_list,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            import traceback
            print(f"💥 {t.__name__}: {e}")
            traceback.print_exc()

    print(f"\n{'='*40}")
    print(f"结果：{passed}/{len(tests)} 通过")
