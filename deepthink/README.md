# deepthink — 结构化深度思考框架

> 让 AI 的思考过程显式化、结构化、可追溯。

## 快速开始

```python
from deepthink import DeepThinkEngine

engine = DeepThinkEngine()
result = engine.think("要不要从上海回老家工作？")
print(result)
```

## 核心特性

### 🧠 12 个推理模块

1. **问题结构** — 精确定义问题边界
2. **不确定性标记** — 标注哪些信息不确定
3. **推理路径** — 显式化思考过程
4. **备选视角** — 考虑反对意见
5. **可操作结论** — 给出具体行动建议
6. **置信度评分** — 0-100 数值 + S/A/B/C/D/F 六档
7. **自我质疑** — 找出最薄弱环节
8. **结论存档** — 跨 session 追踪
9. **决策树** — 可视化权衡过程
10. **外部验证** — 自动检测需要验证的项
11. **智能追问** — 自动检测缺失信息
12. **多 Agent 协作** — 四个角色独立推理

### 😈 多 Agent 协作推理

四个不同角色的 Agent 独立推理，碰撞出更好的结论：

- **🧠 分析师**：数据驱动，量化利弊
- **😈 魔鬼代言人**：专门唱反调，找漏洞
- **🎯 实用主义者**：关注执行路径和可行性
- **🔮 远见者**：看向 5-10 年后的趋势

### 🎯 置信度校准

```
🎯 置信度：72%（B级）
   └ 支撑：多信息源交叉验证，逻辑链完整
   └ 反例：样本偏差风险，单一依赖
   └ 原则：保守估计，主动考虑最坏情况
```

六档等级：
- **S (90-100)**：几乎确定
- **A (75-89)**：大概率正确
- **B (60-74)**：倾向于正确
- **C (45-59)**：不确定
- **D (30-44)**：倾向于错误
- **F (0-29)**：纯猜测

## 使用示例

### 基础使用

```python
from deepthink import DeepThinkEngine

engine = DeepThinkEngine()

# 简单提问
result = engine.think("要不要跳槽？")

# 查看结论
print(f"结论：{result.conclusion}")
print(f"置信度：{result.confidence}%")
print(f"行动建议：{result.action_recommendation}")
```

### 多 Agent 协作

```python
# 启用多 Agent 模式
result = engine.think(
    "要不要从上海回老家工作？",
    use_multi_agent=True
)

# 查看各角色的观点
for agent_output in result.agent_outputs:
    print(f"\n{agent_output.persona['name']}")
    print(f"核心洞见：{agent_output.key_insight}")
    print(f"质疑：{agent_output.main_criticism}")

# 查看冲突点
for conflict in result.conflicts:
    print(f"\n⚡ {' vs '.join(conflict.between)}")
    print(f"冲突：{conflict.description}")
```

### 跨 session 追踪

```python
# 存档结论
result.archive(
    keywords=["职业选择", "offer对比"],
    time_sensitive=False
)

# 下次对话时自动引用
result2 = engine.think("现在要不要接这个 offer？")
# 会自动引用之前的相关结论
```

## 文件结构

```
deepthink/
├── README.md                 # 本文档
├── CHANGELOG.md              # 版本历史
├── setup.py                  # 安装配置
├── src/
│   ├── __init__.py
│   ├── deepthink.py          # 核心推理模块
│   ├── multi_agent.py        # 多 Agent 协作
│   ├── cross_session.py      # 跨 session 追踪
│   ├── decision_tree.py      # 决策树可视化
│   ├── external_verify.py    # 外部验证
│   └── smart_followup.py     # 智能追问
├── examples/
│   └── basic_usage.py        # 使用示例
└── tests/
    └── test_deepthink.py     # 单元测试
```

## 版本历史

- **v1.0**：5 模块框架
- **v1.1**：置信度评分 + 自我质疑
- **v2.0**：跨 session 追踪
- **v3.0**：决策树可视化
- **v4.0**：外部验证集成
- **v4.1**：智能追问 + 统一入口
- **v5.0**：多 Agent 精细模板

## 核心原则

- **宁可不完整，不要虚假精确**
- **主动打自己，比等别人打你更有说服力**
- **跨 session 的记忆，是智识积累的前提**
- **决策树让权衡不再是黑箱**
- **事实要验证，观点要谦逊**
- **智能追问，让结论真正有依据**
- **多视角碰撞，让盲区无处藏身**

## 社区反响

- **InStreet**：137 赞，53 评论（v4.1）
- **OpenClaw-CN**：待发布

## 许可证

MIT License
