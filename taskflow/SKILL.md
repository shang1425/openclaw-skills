# taskflow — 任务拆解与追踪框架

**版本：** v2.0 ✅
**定位**：把 deepthink 的思考结论拆成可执行任务，追踪进度，闭环沉淀。

## 核心功能

| 功能 | 说明 |
|------|------|
| **任务拆解引擎** | 输入文本，输出结构化任务列表（优先级、依赖、预估耗时） |
| **进度追踪** | pending → in_progress → blocked → done |
| **JSON 持久化** | 保存/加载项目状态 |
| **CLI 操作** | 命令行完成、阻塞、查看看板 |
| **Markdown 导出** | 生成可读的项目看板 |
| **统计面板** | 完成率、耗时对比 |

## CLI 用法

```bash
# 拆解文本（支持管道）
echo "立刻：修复bug" | py taskflow.py decompose -s "daily"
py taskflow.py decompose "本周：写测试" --source "taskflow" --stats

# 看板与统计
py taskflow.py list          # 列出所有项目
py taskflow.py board         # 显示当前看板
py taskflow.py stats         # 显示统计

# 任务操作
py taskflow.py start T001    # 开始任务
py taskflow.py done T001 -r  "经验：正则更稳"   # 标记完成 + 记录经验
py taskflow.py block T002 "需要第三方接口"     # 标记阻塞
py taskflow.py resolve T002                      # 解除阻塞
```

## Python API

```python
from taskflow.src.engine import decompose
from taskflow.src.storage import save, load
from taskflow.src.schema import TaskStatus

# 拆解
project = decompose(text, source="deepthink-v4.1")

# 操作
project.update_task_status("T001", TaskStatus.DONE, result="经验记录")
project.update_task_status("T002", TaskStatus.BLOCKED, blocked_reason="缺 API Key")

# 保存/加载
save(project)
loaded = load("path/to/project.json")

# 查可执行任务
for task in project.get_ready_tasks():
    print(f"→ {task.title}")
```

## 支持的输入格式

- `第一步：...` / `第二步：...`（时序步骤）
- `立刻：修复 XXX` / `本周：实现 XXX`（意图标记）
- `[A] 立刻：XXX` / `【B】本周：XXX`（优先级+意图）
- `设计 Schema` / `开发引擎` / `上线发布`（动词开头）
- Markdown 无序列表（`- ` 或 `* `）

## 任务 Schema

```json
{
  "id": "T001",
  "title": "设计任务 Schema 结构",
  "priority": "A",
  "depends_on": [],
  "estimated_minutes": 60,
  "status": "pending",
  "labels": ["design", "core"],
  "result": "学会了正则提取..."
}
```

## 项目结构

```
taskflow/
├── SKILL.md
├── taskflow.py        # CLI 入口
├── src/
│   ├── __init__.py
│   ├── schema.py      # 数据结构
│   ├── engine.py      # 拆解引擎
│   └── storage.py     # JSON 持久化
├── tests/
│   ├── test_taskflow.py
│   └── test_taskflow_v2.py
└── examples/
    └── taskflow_demo.py
```
