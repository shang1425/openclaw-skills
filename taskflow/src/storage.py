"""
taskflow.storage
JSON 文件持久化 — 保存/加载任务项目
"""

import json
import os
from datetime import datetime
from typing import Optional

from .schema import TaskProject, Task, TaskStatus, Priority


def save(project: TaskProject, path: Optional[str] = None) -> str:
    """保存项目到 JSON 文件，返回文件路径"""
    if not path:
        OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c if c.isalnum() else "_" for c in project.name)[:30]
        path = os.path.join(OUTPUT_DIR, f"{safe}_{ts}.json")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    return path


def load(path: str) -> TaskProject:
    """从 JSON 文件加载项目"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = []
    for td in data.get("tasks", []):
        pri = Priority(td.get("priority", "C"))
        status = TaskStatus(td.get("status", "pending"))
        created = _parse_dt(td.get("created_at"))
        updated = _parse_dt(td.get("updated_at"))
        done_at = _parse_dt(td.get("done_at"))
        task = Task(
            id=td["id"],
            title=td["title"],
            description=td.get("description", ""),
            priority=pri,
            depends_on=td.get("depends_on", []),
            estimated_minutes=td.get("estimated_minutes"),
            actual_minutes=td.get("actual_minutes"),
            status=status,
            labels=td.get("labels", []),
            blocked_reason=td.get("blocked_reason"),
            created_at=created,
            updated_at=updated,
            done_at=done_at,
            result=td.get("result"),
        )
        tasks.append(task)

    created = _parse_dt(data.get("created_at"))
    updated = _parse_dt(data.get("updated_at"))
    project = TaskProject(
        id=data["id"],
        name=data["name"],
        description=data.get("description", ""),
        source=data.get("source", ""),
        tasks=tasks,
        created_at=created,
        updated_at=updated,
        meta=data.get("meta", {}),
    )
    return project


def _parse_dt(s: Optional[str]) -> datetime:
    if not s:
        return datetime.now()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.now()


def load_latest(name: str = "") -> Optional[TaskProject]:
    """从 OUTPUT_DIR 加载最新的项目文件"""
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
    if not os.path.exists(OUTPUT_DIR):
        return None

    files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".json"):
            files.append(os.path.join(OUTPUT_DIR, f))

    if not files:
        return None

    # 按修改时间倒序
    files.sort(key=os.path.getmtime, reverse=True)

    # 如果指定了名字，模糊匹配
    if name:
        matches = [f for f in files if name in os.path.basename(f)]
        if matches:
            return load(matches[0])

    return load(files[0])
