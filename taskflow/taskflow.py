#!/usr/bin/env python3
"""
taskflow CLI
用法：
  py taskflow.py decompose "文本内容" --source "来源"
  py taskflow.py list [--name 项目名]
  py taskflow.py status <task_id> [--project <文件>]
  py taskflow.py done <task_id> [--project <文件>]
  py taskflow.py block <task_id> <原因> [--project <文件>]
  py taskflow.py stats [--project <文件>]
  py taskflow.py board [--project <文件>]
"""

import argparse
import json
import os
import sys
import re

# 确保 src 在路径中
sys.path.insert(0, os.path.dirname(__file__))

from src.schema import TaskProject, TaskStatus, Priority
from src.engine import decompose
from src.storage import save, load, load_latest


# ── 颜色输出 ──────────────────────────────────────────────────

def c(text: str, color: str) -> str:
    """简单颜色（兼容 Windows PowerShell）"""
    # PowerShell 原样输出 ANSI，需要用 Write-Host，这里只做简单处理
    return text


def pri_label(p: str) -> str:
    return {"A": "🔴A", "B": "🟠B", "C": "🟡C", "D": "⚪D"}.get(p, p)


def status_icon(s: str) -> str:
    return {
        "pending": "📋",
        "in_progress": "🔄",
        "blocked": "🚫",
        "done": "✅",
        "cancelled": "❌",
    }.get(s, s)


# ── 核心命令 ──────────────────────────────────────────────────

def cmd_decompose(args):
    text = args.text or sys.stdin.read()
    if not text.strip():
        print("错误：没有输入文本", file=sys.stderr)
        return 1

    project = decompose(text, source=args.source or "cli")

    if args.output:
        path = save(project, args.output)
        print(f"✅ 已保存：{path}")

    if args.stats:
        _print_stats(project)

    _print_board(project)
    return 0


def cmd_list(args):
    from src import OUTPUT_DIR
    if not os.path.exists(OUTPUT_DIR):
        print("没有已保存的项目")
        return 0

    files = sorted(
        [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")],
        key=os.path.getmtime,
        reverse=True,
    )

    if not files:
        print("没有已保存的项目")
        return 0

    for f in files:
        p = load(f)
        done = sum(1 for t in p.tasks if t.status == TaskStatus.DONE)
        total = len(p.tasks)
        bar = "█" * done + "░" * (total - done)
        print(f"{os.path.basename(f)}")
        print(f"  {p.name}  [{bar}] {done}/{total}  来源：{p.source}")

    return 0


def cmd_board(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1
    _print_board(project)
    return 0


def cmd_stats(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1
    _print_stats(project)
    return 0


def cmd_done(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1

    task = project.get_task(args.task_id)
    if not task:
        print(f"错误：找不到任务 {args.task_id}", file=sys.stderr)
        return 1

    ok = project.update_task_status(args.task_id, TaskStatus.DONE, result=args.result)
    if ok:
        path = save(project)
        print(f"✅ 任务 {args.task_id} 已标记完成：{task.title}")
        print(f"   已保存：{path}")
    return 0


def cmd_block(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1

    task = project.get_task(args.task_id)
    if not task:
        print(f"错误：找不到任务 {args.task_id}", file=sys.stderr)
        return 1

    ok = project.update_task_status(
        args.task_id, TaskStatus.BLOCKED, blocked_reason=args.reason
    )
    if ok:
        path = save(project)
        print(f"🚫 任务 {args.task_id} 已标记阻塞：{task.title}")
        print(f"   原因：{args.reason}")
        print(f"   已保存：{path}")
    return 0


def cmd_resolve(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1

    task = project.get_task(args.task_id)
    if not task:
        print(f"错误：找不到任务 {args.task_id}", file=sys.stderr)
        return 1

    ok = project.update_task_status(args.task_id, TaskStatus.PENDING, blocked_reason=None)
    if ok:
        path = save(project)
        print(f"✅ 任务 {args.task_id} 已解除阻塞：{task.title}")
        print(f"   已保存：{path}")
    return 0


def cmd_start(args):
    project = _load_project(args.project, args.name)
    if not project:
        return 1

    task = project.get_task(args.task_id)
    if not task:
        print(f"错误：找不到任务 {args.task_id}", file=sys.stderr)
        return 1

    ok = project.update_task_status(args.task_id, TaskStatus.IN_PROGRESS)
    if ok:
        path = save(project)
        print(f"🔄 开始任务 {args.task_id}：{task.title}")
        print(f"   已保存：{path}")
    return 0


# ── 辅助函数 ──────────────────────────────────────────────────

def _load_project(project_path: str = None, name: str = "") -> TaskProject | None:
    if project_path:
        if not os.path.exists(project_path):
            print(f"错误：文件不存在 {project_path}", file=sys.stderr)
            return None
        return load(project_path)

    project = load_latest(name)
    if not project:
        print("错误：没有已保存的项目，请用 --project 指定文件", file=sys.stderr)
        return None
    return project


def _print_stats(project: TaskProject):
    total = len(project.tasks)
    if total == 0:
        print("无任务")
        return

    done = sum(1 for t in project.tasks if t.status == TaskStatus.DONE)
    in_prog = sum(1 for t in project.tasks if t.status == TaskStatus.IN_PROGRESS)
    blocked = sum(1 for t in project.tasks if t.status == TaskStatus.BLOCKED)
    pending = sum(1 for t in project.tasks if t.status == TaskStatus.PENDING)

    pct = done / total * 100

    # 预估 vs 实际耗时
    est_total = sum(t.estimated_minutes or 0 for t in project.tasks)
    act_total = sum(t.actual_minutes or 0 for t in project.tasks if t.status == TaskStatus.DONE)

    print(f"📊 {project.name}")
    print(f"   进度：{done}/{total} ({pct:.0f}%)")
    print(f"   状态：✅{done}  🔄{in_prog}  🚫{blocked}  📋{pending}")
    if est_total > 0:
        print(f"   耗时：实际 {act_total}min / 预估 {est_total}min")
    print(f"   来源：{project.source}")


def _print_board(project: TaskProject):
    print()
    print(f"📋 {project.name}")
    print(f"   来源：{project.source}  |  {len(project.tasks)} 个任务")
    print()

    by_status = {s: [] for s in TaskStatus}
    for t in project.tasks:
        by_status[t.status].append(t)

    status_labels = {
        TaskStatus.PENDING: "📋 待处理",
        TaskStatus.IN_PROGRESS: "🔄 进行中",
        TaskStatus.BLOCKED: "🚫 阻塞",
        TaskStatus.DONE: "✅ 完成",
        TaskStatus.CANCELLED: "❌ 取消",
    }

    for status in TaskStatus:
        tasks = by_status[status]
        if not tasks:
            continue
        print(f"  {status_labels[status]} ({len(tasks)})")
        for t in sorted(tasks, key=lambda x: x.priority.value):
            pr = pri_label(t.priority.value)
            deps = f" ← {', '.join(t.depends_on)}" if t.depends_on else ""
            est = f" ⏱{t.estimated_minutes}m" if t.estimated_minutes else ""
            blk = f" | 阻塞: {t.blocked_reason}" if t.blocked_reason else ""
            done_mark = " ✅" if t.status == TaskStatus.DONE else ""
            print(f"    {t.id} {pr} {t.title}{deps}{est}{blk}{done_mark}")
        print()


# ── CLI 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="taskflow — 任务拆解与追踪框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # decompose
    p_decomp = sub.add_parser("decompose", help="拆解文本为任务项目")
    p_decomp.add_argument("text", nargs="?", help="要拆解的文本（省略则从 stdin 读取）")
    p_decomp.add_argument("--source", "-s", help="来源标识")
    p_decomp.add_argument("--output", "-o", help="保存路径")
    p_decomp.add_argument("--stats", action="store_true", help="显示统计信息")

    # list
    sub.add_parser("list", help="列出所有已保存项目")

    # board
    p_board = sub.add_parser("board", help="显示任务看板")
    p_board.add_argument("--project", "-p")
    p_board.add_argument("--name", "-n", default="")

    # stats
    p_stats = sub.add_parser("stats", help="显示项目统计")
    p_stats.add_argument("--project", "-p")
    p_stats.add_argument("--name", "-n", default="")

    # done
    p_done = sub.add_parser("done", help="标记任务完成")
    p_done.add_argument("task_id")
    p_done.add_argument("--project", "-p")
    p_done.add_argument("--name", "-n", default="")
    p_done.add_argument("--result", "-r", default="", help="执行结果/经验")

    # block
    p_block = sub.add_parser("block", help="标记任务阻塞")
    p_block.add_argument("task_id")
    p_block.add_argument("reason")
    p_block.add_argument("--project", "-p")
    p_block.add_argument("--name", "-n", default="")

    # resolve
    p_res = sub.add_parser("resolve", help="解除任务阻塞")
    p_res.add_argument("task_id")
    p_res.add_argument("--project", "-p")
    p_res.add_argument("--name", "-n", default="")

    # start
    p_start = sub.add_parser("start", help="开始任务")
    p_start.add_argument("task_id")
    p_start.add_argument("--project", "-p")
    p_start.add_argument("--name", "-n", default="")

    args = parser.parse_args()

    commands = {
        "decompose": cmd_decompose,
        "list": cmd_list,
        "board": cmd_board,
        "stats": cmd_stats,
        "done": cmd_done,
        "block": cmd_block,
        "resolve": cmd_resolve,
        "start": cmd_start,
    }

    fn = commands.get(args.cmd)
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
