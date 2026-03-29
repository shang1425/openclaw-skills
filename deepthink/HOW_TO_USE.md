# deepthink v2.0 调用指南

## 📍 技能位置

```
C:\Users\Administrator\.qclaw\workspace\skills\deepthink-harness\
```

## 🚀 快速调用

### 方式1：Python 直接调用（最简单）

```python
from harness import run_harness, format_harness_result

# 一行代码
result = run_harness("你的问题", "额外上下文")
print(format_harness_result(result))
```

### 方式2：分模块调用

```python
from planner import plan, format_plan
from generator import generate, format_generation
from evaluator import evaluate, format_evaluation

# 第1步：规划
p = plan("你的问题")
print(format_plan(p))

# 第2步：生成
g = generate(subproblems, sprint_contract)
print(format_generation(g))

# 第3步：评估
e = evaluate(thought_chain, subproblem_count)
print(format_evaluation(e))
```

## 📚 文档

| 文件 | 用途 |
|------|------|
| **QUICKSTART.md** | 快速参考（推荐先读） |
| **USAGE.md** | 完整使用指南 |
| **ARCHITECTURE.md** | 技术架构文档 |
| **TEST_REPORT.md** | 测试报告 |
| **examples.py** | 调用示例代码 |

## 🎯 核心模块

### 1. Planner（规划器）
**文件：** `planner.py`

**功能：** 拆解问题，定义成功标准

**调用：**
```python
from planner import plan, format_plan

result = plan("你的问题", "上下文")
print(format_plan(result))
```

**输出：**
- 问题类型识别
- 子问题拆解
- 角色分配
- Sprint Contract

### 2. Generator（生成器）
**文件：** `generator.py`

**功能：** 生成思考链，评估置信度

**调用：**
```python
from generator import generate, format_generation

result = generate(subproblems, sprint_contract, context)
print(format_generation(result))
```

**输出：**
- 思考链（多个步骤）
- 置信度评估（A/B/C/D/F）
- 自我质疑
- 最终结论

### 3. Evaluator（评估器）
**文件：** `evaluator.py`

**功能：** 评估思考质量，识别问题

**调用：**
```python
from evaluator import evaluate, format_evaluation

result = evaluate(thought_chain, subproblem_count)
print(format_evaluation(result))
```

**输出：**
- 四维度评分（0-10）
- 问题识别
- 改进建议
- 总体判定

### 4. Harness（迭代循环）
**文件：** `harness.py`

**功能：** 协调三个模块，自动迭代改进

**调用：**
```python
from harness import run_harness, format_harness_result

result = run_harness("你的问题", "上下文")
print(format_harness_result(result))
```

**输出：**
- 完整的迭代过程
- 最终评分
- 最终结论

## 💡 使用场景

### 场景1：决策问题
```python
result = run_harness(
    "是否应该换工作？",
    "现在年薪50万，有个创业机会"
)
```

### 场景2：预测问题
```python
result = run_harness(
    "AI 行业未来会怎样？",
    "考虑大模型、AGI、监管等因素"
)
```

### 场景3：分析问题
```python
result = run_harness(
    "为什么项目失败了？",
    "投入200万，没有产生预期收益"
)
```

### 场景4：规划问题
```python
result = run_harness(
    "如何学习编程？",
    "没有基础，想成为全栈工程师"
)
```

## 🔧 配置选项

```python
from harness import run_harness, HarnessConfig

config = HarnessConfig(
    max_iterations=3,              # 最多迭代3次
    quality_threshold=7,           # 所有维度 ≥ 7 分通过
    enable_sprint=True,            # 启用 Sprint Contract
    evaluator_strictness="medium"  # 评估严格度：low/medium/high
)

result = run_harness(
    problem="你的问题",
    context="上下文",
    config=config
)
```

## 📊 输出解读

### 四维度评分

| 维度 | 含义 | 7分标准 |
|------|------|--------|
| **完整性** | 覆盖程度 | 覆盖所有子问题 |
| **严谨性** | 逻辑质量 | 推理无缺口 |
| **诚实性** | 不确定性标记 | 充分标记 |
| **可操作性** | 结论可执行性 | 清晰可执行 |

**通过条件：** 所有维度 ≥ 7 分

### 置信度等级

| 等级 | 含义 | 何时出现 |
|------|------|---------|
| **A** | 高度确信 | 证据充分 + 假设少 |
| **B** | 中等确信 | 证据一般 + 假设中等 |
| **C** | 低度确信 | 证据不足 + 假设较多 |
| **D** | 很低确信 | 证据很少 + 假设很多 |
| **F** | 无法确信 | 无证据 + 无法判断 |

## 🔄 迭代流程

```
输入问题
    ↓
Planner: 拆解问题
    ↓
Generator: 生成思考链
    ↓
Evaluator: 评估质量
    ↓
通过？ ──是→ 输出结论
    ↓
    否 → 改进反馈 → Generator (循环)
```

## 📁 文件结构

```
deepthink-harness/
├── planner.py              # 规划器（280行）
├── generator.py            # 生成器（280行）
├── evaluator.py            # 评估器（380行）
├── harness.py              # 主模块（320行）
├── test_e2e.py             # 测试脚本
├── examples.py             # 调用示例
├── ARCHITECTURE.md         # 架构文档
├── USAGE.md               # 完整指南
├── QUICKSTART.md          # 快速参考
├── TEST_REPORT.md         # 测试报告
└── publish_to_instreet.bat # 发布脚本
```

## ✅ 测试验证

所有模块都已通过测试：

```
✅ 决策类问题：通过
✅ 预测类问题：通过
✅ 规划类问题：通过
总体通过率：3/3 (100%)
```

## 🎓 学习路径

1. **快速开始** → 读 QUICKSTART.md
2. **基本使用** → 运行 examples.py
3. **深入理解** → 读 ARCHITECTURE.md
4. **完整掌握** → 读 USAGE.md

## 🚀 下一步

- **v3：** 跨 session 追踪推理结论
- **v4：** 决策树可视化
- **v5：** 多 Agent 协作推理

## 📞 技术支持

- 查看 ARCHITECTURE.md 了解技术细节
- 查看 examples.py 了解调用方式
- 查看 TEST_REPORT.md 了解测试结果

---

**版本：** v2.0  
**发布日期：** 2026-03-27  
**状态：** 正式版  
**代码行数：** 1260 行
