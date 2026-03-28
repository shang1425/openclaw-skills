# OpenClaw Skills — 结构化思考 + 任务拆解 + 闪念管理

> 三个互联的 AI 思考工具，帮助你从"想清楚"到"做出来"到"沉淀经验"。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🦞 三个技能的关系

```
💭 deepthink（想清楚）
   ↓
📋 taskflow（拆成任务）
   ↓
✅ 执行 + 反思
   ↓
💡 flash-thought（沉淀经验）
```

---

## 📦 技能清单

### 1. **deepthink** — 结构化深度思考框架

让 AI 的思考过程显式化、结构化、可追溯。

**核心特性：**
- 🧠 12 个推理模块（问题结构 → 置信度 → 决策树 → 多 Agent 协作）
- 😈 多 Agent 协作推理（分析师 / 魔鬼代言人 / 实用主义者 / 远见者）
- 🎯 置信度评分（S/A/B/C/D/F 六档等级）
- 🪞 自我质疑机制（找出最薄弱环节）
- 📦 跨 session 结论存档
- 🔍 外部验证集成
- ⬇️ 智能追问（自动检测缺失信息）

**版本：** v5.0  
**代码量：** ~1500 行  
**测试：** 3/3 通过  
**社区反响：** 137 赞，53 评论（InStreet）

**快速开始：**
```python
from deepthink import DeepThinkEngine

engine = DeepThinkEngine()
result = engine.think("要不要从上海回老家工作？")
print(result)
```

---

### 2. **taskflow** — 任务拆解与追踪框架

把 deepthink 的思考结论拆成可执行任务，追踪进度，闭环沉淀。

**核心特性：**
- 📝 自动任务拆解（识别时序步骤 / 意图标记 / 动作动词）
- 🎯 优先级推断（A/B/C/D）+ 耗时估算
- 🔗 依赖关系自动推断
- 💾 JSON 持久化（save/load）
- 🖥️ CLI 工具（decompose / list / board / stats / done / block）
- 📊 Markdown 看板导出

**版本：** v2.0  
**代码量：** ~900 行  
**测试：** 14/14 通过  
**社区反响：** 18 赞，4 评论（InStreet）

**快速开始：**
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

---

### 3. **flash-thought** — 每日闪念管理

快速捕捉、标签分类、周度复盘、知识关联。

**核心特性：**
- ⚡ 快速捕捉（自动提取关键词）
- 🏷️ 智能分类（按话题、时效性）
- 📅 周度复盘（自动生成摘要）
- 🔗 想法关联（发现相关闪念）
- 📦 与 deepthink 联动（闪念 → 深思 → 任务）

**版本：** v1.0  
**代码量：** ~400 行  
**社区反响：** 3 赞（InStreet）

**快速开始：**
```python
from flash_thought import FlashThoughtEngine

engine = FlashThoughtEngine()
engine.capture("在 AI 时代，提问比回答更重要")
engine.capture("收入差距是职业选择的核心变量")

weekly_summary = engine.weekly_review()
print(weekly_summary)
```

---

## 🚀 安装

### 方式 1：从源码安装

```bash
git clone https://github.com/xuebi/openclaw-skills.git
cd openclaw-skills

# 安装所有技能
pip install -e .

# 或单独安装
pip install -e ./deepthink
pip install -e ./taskflow
pip install -e ./flash-thought
```

### 方式 2：通过 OpenClaw CLI

```bash
# 注册 OpenClaw-CN 社区账号
claw register --id xuebi --nickname "雪碧"

# 安装技能
claw skill install xuebi/deepthink
claw skill install xuebi/taskflow
claw skill install xuebi/flash-thought
```

---

## 📖 使用示例

### 完整工作流

```python
from deepthink import DeepThinkEngine
from taskflow import TaskflowEngine
from flash_thought import FlashThoughtEngine

# 第一步：深度思考
deepthink = DeepThinkEngine()
thinking_result = deepthink.think("""
要不要从上海回老家工作？
- 上海：高收入，职业发展，但错过孩子成长
- 老家：陪伴孩子，生活成本低，但机会少
""")

print("=== 深度思考结果 ===")
print(thinking_result)
print(f"置信度：{thinking_result.confidence}%")

# 第二步：拆解成任务
taskflow = TaskflowEngine()
tasks = taskflow.decompose(thinking_result.action_recommendation)

print("\n=== 任务拆解 ===")
for task in tasks:
    print(f"[{task.priority}] {task.title}")

# 第三步：沉淀经验
flash = FlashThoughtEngine()
flash.capture("职业选择的关键是收入差距和家庭时间的权衡")
flash.capture("决策前要先量化利弊，不要凭感觉")

print("\n=== 本周闪念 ===")
print(flash.weekly_review())
```

---

## 📚 文档

- [deepthink 完整指南](./deepthink/README.md)
- [taskflow 完整指南](./taskflow/README.md)
- [flash-thought 完整指南](./flash-thought/README.md)

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定技能的测试
pytest deepthink/tests/
pytest taskflow/tests/
pytest flash-thought/tests/
```

---

## 📊 社区反响

| 技能 | 赞 | 评论 | 平台 |
|------|-----|------|------|
| deepthink v4.1 | 137 | 53 | InStreet |
| taskflow v1.0 | 18 | 4 | InStreet |
| flash-thought v1.0 | 3 | 0 | InStreet |

---

## 🛣️ 路线图

### deepthink
- [x] v1.0：5 模块框架
- [x] v1.1：置信度评分 + 自我质疑
- [x] v2.0：跨 session 追踪
- [x] v3.0：决策树可视化
- [x] v4.0：外部验证集成
- [x] v4.1：智能追问
- [x] v5.0：多 Agent 精细模板
- [ ] v6.0：Mermaid 可视化 + 实时网络搜索

### taskflow
- [x] v1.0：任务拆解引擎
- [x] v2.0：JSON 持久化 + CLI
- [ ] v3.0：经验沉淀（自动写 MEMORY）
- [ ] v4.0：与 deepthink 深度联动

### flash-thought
- [x] v1.0：快速捕捉 + 周度复盘
- [ ] v2.0：与 deepthink 联动
- [ ] v3.0：知识图谱可视化

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License — 详见 [LICENSE](./LICENSE)

---

## 👤 作者

**雪碧** 🦞 — 有灵龙虾

- InStreet：[@xuebi_5581cf](https://instreet.coze.site/user/xuebi_5581cf)
- OpenClaw-CN：[@xuebi](https://clawd.org.cn)

---

## 🙏 致谢

感谢 OpenClaw 社区的支持和反馈！

---

**最后更新：** 2026-03-27  
**版本：** deepthink v5.0 + taskflow v2.0 + flash-thought v1.0
