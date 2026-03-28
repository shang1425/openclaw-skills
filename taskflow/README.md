# taskflow — 任务拆解与追踪框架

> 把思考结论拆成可执行任务，追踪进度，闭环沉淀。

## 快速开始

```python
from taskflow import TaskflowEngine

engine = TaskflowEngine()
tasks = engine.decompose("""
1. 立刻修复 memory_search 在长文本时的崩溃
2. 本周实现 taskflow v1.0 拆解引擎
3. 下周测试用例，要看核心路径
4. 可选：增加 Markdown 导出
5. 不做：Web UI
""")

for task in tasks:
    print(f"[{task.priority}] {task.title} ({task.estimated_hours}h)")
```

## 核心特性

### 📝 自动任务拆解

识别三类信息：
- **时序步骤**：第1步、第2步、接下来...
- **意图标记**：立刻、本周、可选、不做...
- **动作动词**：修复、实现、测试、增加...

### 🎯 优先级推断

自动分配 A/B/C/D 优先级：
- **[A]** 立刻、马上、立即、紧急、阻塞
- **[B]** 本周、本月、尽快、重要
- **[C]** 可选、可延迟、低优先级
- **[D]** 不做、暂停、废弃

### 🔗 依赖关系推断

自动检测任务间的依赖：
```
Task A (完成) → Task B (可开始)
Task B (阻塞) → Task C (等待)
```

### 💾 JSON 持久化

保存和加载任务状态：
```python
# 保存
engine.save("my_project.json")

# 加载
engine.load("my_project.json")
```

### 🖥️ CLI 工具

```bash
# 拆解任务
taskflow decompose "1. 做A 2. 做B"

# 查看任务列表
taskflow list

# 看板视图
taskflow board

# 统计信息
taskflow stats

# 标记完成
taskflow done task_id

# 标记阻塞
taskflow block task_id "原因"

# 解除阻塞
taskflow resolve task_id
```

### 📊 Markdown 看板导出

```python
board_md = engine.export_board()
print(board_md)
```

输出：
```
## 📋 任务看板

### 🔴 [A] 立刻 (3 个任务)
- [x] 修复 memory_search 崩溃
- [ ] 实现 taskflow v1.0

### 🟡 [B] 本周 (2 个任务)
- [ ] 测试用例

### 🟢 [C] 可选 (1 个任务)
- [ ] 增加 Markdown 导出

### ⚫ [D] 不做 (1 个任务)
- [ ] Web UI
```

## 使用示例

### 基础使用

```python
from taskflow import TaskflowEngine

engine = TaskflowEngine()

# 拆解任务
tasks = engine.decompose("""
1. 立刻修复 bug
2. 本周完成功能 A
3. 下周测试
4. 可选：优化性能
5. 不做：Web UI
""")

# 查看任务
for task in tasks:
    print(f"[{task.priority}] {task.title}")
    print(f"  耗时：{task.estimated_hours}h")
    print(f"  依赖：{task.dependencies}")
```

### 任务追踪

```python
# 标记完成
engine.mark_done("task_1")

# 标记阻塞
engine.mark_blocked("task_2", "等待 API 文档")

# 解除阻塞
engine.resolve_blocked("task_2")

# 查看进度
stats = engine.get_stats()
print(f"完成率：{stats['completion_rate']}%")
print(f"阻塞任务：{stats['blocked_count']}")
```

### 与 deepthink 联动

```python
from deepthink import DeepThinkEngine
from taskflow import TaskflowEngine

# 第一步：深度思考
deepthink = DeepThinkEngine()
result = deepthink.think("要不要跳槽？")

# 第二步：拆解成任务
taskflow = TaskflowEngine()
tasks = taskflow.decompose(result.action_recommendation)

# 第三步：追踪执行
for task in tasks:
    print(f"[{task.priority}] {task.title}")
```

## 文件结构

```
taskflow/
├── README.md                 # 本文档
├── CHANGELOG.md              # 版本历史
├── setup.py                  # 安装配置
├── src/
│   ├── __init__.py
│   ├── engine.py             # 核心拆解引擎
│   ├── schema.py             # 数据结构
│   └── storage.py            # JSON 持久化
├── examples/
│   └── basic_usage.py        # 使用示例
└── tests/
    ├── test_taskflow.py      # v1.0 测试
    └── test_taskflow_v2.py   # v2.0 测试
```

## 版本历史

- **v1.0**：任务拆解引擎（10/10 测试通过）
- **v2.0**：JSON 持久化 + CLI（14/14 测试通过）
- **v3.0**（计划）：经验沉淀（完成任务自动写 MEMORY）
- **v4.0**（计划）：与 deepthink 深度联动

## 核心原则

- **自动化优于手工**：尽可能自动推断优先级和依赖
- **可见性优于隐藏**：所有任务状态一目了然
- **灵活性优于严格**：支持多种输入格式
- **可追踪优于遗忘**：持久化保存所有状态

## 社区反响

- **InStreet**：18 赞，4 评论（v1.0）
- **OpenClaw-CN**：待发布

## 许可证

MIT License
