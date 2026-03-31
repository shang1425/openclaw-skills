"""
taskflow.task_schema
任务数据结构定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Priority(str, Enum):
    A = "A"  # 最高，立刻处理
    B = "B"  # 高，本周内完成
    C = "C"  # 中，可延期
    D = "D"  # 低，选做
    F = "F"  # 拦截阻塞


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    priority: Priority = Priority.C
    depends_on: list[str] = field(default_factory=list)
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    labels: list[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    done_at: Optional[datetime] = None
    result: Optional[str] = None  # 执行结果/经验

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "depends_on": self.depends_on,
            "estimated_minutes": self.estimated_minutes,
            "actual_minutes": self.actual_minutes,
            "status": self.status.value,
            "labels": self.labels,
            "blocked_reason": self.blocked_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "done_at": self.done_at.isoformat() if self.done_at else None,
            "result": self.result,
        }

    @staticmethod
    def gen_id() -> str:
        return f"T{str(uuid.uuid4().hex[:6]).upper()}"


@dataclass
class TaskProject:
    id: str
    name: str
    description: str = ""
    source: str = ""  # 来源，如 deepthink-session-xxx
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    meta: dict = field(default_factory=dict)  # 扩展字段

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "meta": self.meta,
        }

    def get_task(self, task_id: str) -> Task | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def add_task(self, title: str, **kwargs) -> Task:
        task = Task(id=Task.gen_id(), title=title, **kwargs)
        self.tasks.append(task)
        self.updated_at = datetime.now()
        return task

    def update_task_status(
        self, task_id: str, status: TaskStatus, **kwargs
    ) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        task.status = status
        task.updated_at = datetime.now()
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        if status == TaskStatus.DONE:
            task.done_at = datetime.now()
        self.updated_at = datetime.now()
        return True

    def get_ready_tasks(self) -> list[Task]:
        """返回所有依赖已满足、可执行的任务"""
        done_ids = {t.id for t in self.tasks if t.status == TaskStatus.DONE}
        ready = []
        for t in self.tasks:
            if t.status != TaskStatus.PENDING:
                continue
            deps_done = all(d in done_ids for d in t.depends_on)
            if deps_done:
                ready.append(t)
        return ready

    def to_markdown(self) -> str:
        lines = [f"# {self.name}", ""]
        if self.description:
            lines.append(f"{self.description}")
            lines.append("")
        lines.append(f"**来源：** {self.source}  ")
        lines.append(f"**创建：** {self.created_at.strftime('%Y-%m-%d %H:%M')}  ")
        lines.append("")
        lines.append("## 任务列表")
        lines.append("")

        # 按状态分组
        by_status = {s: [] for s in TaskStatus}
        for t in self.tasks:
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
            lines.append(f"### {status_labels[status]} ({len(tasks)})")
            for t in sorted(tasks, key=lambda x: x.priority.value):
                pr = f"[{t.priority.value}]" if t.priority else ""
                deps = f" ← {', '.join(t.depends_on)}" if t.depends_on else ""
                est = f" ⏱{t.estimated_minutes}min" if t.estimated_minutes else ""
                lines.append(f"- **{t.id}** {pr} {t.title}{deps}{est}")
                if t.blocked_reason:
                    lines.append(f"  - 🚫 阻塞: {t.blocked_reason}")
                if t.result:
                    lines.append(f"  - 📝 {t.result}")
            lines.append("")

        return "\n".join(lines)
