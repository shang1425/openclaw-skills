# OpenClaw Skills — 结构化思考 + 任务拆解

> 两个互联的 AI 思考工具：**deepthink** 让 AI 真正思考，**taskflow** 把结论拆成行动。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🦞 两者关系

```
💭 deepthink（真正想清楚）
   ↓
📋 taskflow（拆成可执行任务）
   ↓
✅ 执行 + 反思
```

---

## 📦 deepthink — 结构化深度思考框架 v3.0

> **真实 LLM 驱动** — 规划器、生成器、评估器全部接入真实模型推理

### 核心架构：Harness 三智能体

```
用户问题
   ↓
🎯 Planner（规划器）→ 拆解子问题 + Sprint Contract
   ↓
🧠 Generator（生成器）→ 思考链 + Self-Reflection Loop（反思链）
   ↓
🔍 Evaluator（评估器）→ 四维度评分 → 通过？→ 输出结论
                        ↑
                   不通过？→ 迭代改进
```

### 四维度评分

| 维度 | 说明 |
|------|------|
| completeness（完整性） | 是否覆盖所有关键问题 |
| rigor（严谨性） | 推理逻辑是否有漏洞 |
| honesty（诚实性） | 不确定性是否充分标记 |
| actionability（可操作性） | 结论是否清晰可执行 |

### Self-Reflection Loop

Generator 输出的思考链会经过反思评估：
- 识别逻辑漏洞、遗漏视角
- 判断是否需要重新生成
- 改进提示注入下一轮生成

### 支持的模型

| Provider | 模型 | 配置 |
|----------|------|------|
| **QClaw（默认）** | 本地代理 modelroute | 开箱即用 |
| **OpenAI** | GPT-4o / GPT-4o-mini | 设置 `OPENAI_API_KEY` |
| **DeepSeek** | deepseek-chat | 设置 `DEEPSEEK_API_KEY` |

**快速开始：**
```python
from harness import run_harness, format_harness_result, HarnessConfig
from llm_client import get_client

client = get_client()  # 自动使用 QClaw 本地代理
result = run_harness(
    problem="是否应该辞职回老家接手饭店？",
    context="在一线城市工作5年，年薪30万，父亲想让我回老家",
    llm_client=client,
)
print(format_harness_result(result))
```

**CLI 模式：**
```bash
py deepthink/harness.py
```

---

## 📋 taskflow — 任务拆解与追踪框架 v2.0

> 把 deepthink 的思考结论拆成可执行任务，追踪进度，闭环沉淀。

### 核心功能

- 📝 自动任务拆解（时序步骤 / 意图标记 / 动作动词）
- 🎯 优先级推断（A/B/C/D）+ 耗时估算
- 🔗 依赖关系自动推断
- 💾 JSON 持久化（save/load）
- 🖥️ CLI 工具（decompose / list / board / stats / done / block）

**快速开始：**
```python
from taskflow.src.engine import decompose
from taskflow.src.storage import save

project = decompose("本周：完成用户认证，下周：API对接，可选：性能优化", source="deepthink")
save(project)

# 查看可执行任务
for task in project.get_ready_tasks():
    print(f"→ [{task.priority}] {task.title}")
```

**CLI：**
```bash
py taskflow/taskflow.py decompose "立刻：修复登录bug" --source daily
py taskflow/taskflow.py board
py taskflow/taskflow.py done T001 -r "经验：正则更稳"
```

---

## 📂 文件结构

```
.
├── README.md
├── LICENSE
├── .gitignore
├── deepthink/                  # deepthink v3.0
│   ├── SKILL.md               # 完整文档（12模块 + 多Agent）
│   ├── ARCHITECTURE.md        # 架构说明
│   ├── harness.py             # 迭代循环主模块
│   ├── planner.py             # 规划器（LLM 驱动）
│   ├── generator.py           # 生成器（LLM 驱动 + 反思链）
│   ├── evaluator.py           # 评估器（LLM 驱动）
│   ├── llm_client.py          # 统一模型调用入口
│   ├── cross_session.py       # 跨 session 追踪
│   ├── decision_tree.py       # 决策树可视化
│   ├── external_verify.py     # 外部验证集成
│   ├── smart_followup.py      # 智能追问
│   ├── multi_agent.py         # 多Agent协作
│   ├── examples.py            # 调用示例
│   └── test_e2e.py            # 端到端测试
└── taskflow/                   # taskflow v2.0
    ├── SKILL.md               # 完整文档
    ├── taskflow.py            # CLI 入口
    └── src/
        ├── engine.py          # 拆解引擎
        ├── schema.py           # 数据结构
        └── storage.py          # JSON 持久化
```

---

## 🧪 测试

```bash
# deepthink 端到端测试
py deepthink/test_e2e.py

# taskflow 单元测试
py -m pytest taskflow/tests/ -v
```

---

## 📊 社区反响

| 技能 | 赞 | 评论 | 平台 |
|------|-----|------|------|
| deepthink v4.1 | **137** | 53 | InStreet |
| taskflow v1.0 | **18** | 4 | InStreet |
| flash-thought v1.0 | 3 | 0 | InStreet |

---

## 🛣️ 路线图

### deepthink
- [x] v1.0–v5.0：5模块→多Agent协作
- [x] **v3.0：真实 LLM 集成 + Self-Reflection Loop**
- [ ] v6.0：Mermaid 可视化 + 实时搜索
- [ ] v7.0：多模型协作（不同子问题用不同模型）

### taskflow
- [x] v1.0：任务拆解引擎
- [x] v2.0：JSON 持久化 + CLI
- [ ] v3.0：经验沉淀（自动写 MEMORY）
- [ ] v4.0：与 deepthink v3.0 深度联动

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

---

**最后更新：** 2026-03-29
**版本：** deepthink **v3.0**（真实 LLM 集成）+ taskflow v2.0
