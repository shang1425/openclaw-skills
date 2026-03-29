# deepthink v2.0 使用指南

## 快速开始

### 方式1：直接导入模块（Python）

```python
from planner import plan, format_plan
from generator import generate, format_generation
from evaluator import evaluate, format_evaluation
from harness import run_harness, format_harness_result

# 运行完整的 Harness 流程
result = run_harness(
    problem="是否应该辞职回老家接手饭店？",
    context="我在一线城市工作5年，年薪30万，父亲想让我回老家接手饭店"
)

print(format_harness_result(result))
```

### 方式2：分步调用（Python）

```python
from planner import plan, format_plan
from generator import generate, format_generation
from evaluator import evaluate, format_evaluation

# 第1步：Planner 规划
plan_result = plan("你的问题")
print(format_plan(plan_result))

# 第2步：Generator 生成
subproblems = [
    {
        "id": sp.id,
        "question": sp.question,
        "assigned_role": sp.assigned_role,
        "uncertainty": sp.uncertainty.value,
    }
    for sp in plan_result.subproblems
]
sprint_contract = {
    "goal": plan_result.sprint_contract.goal,
    "deliverables": plan_result.sprint_contract.deliverables,
    "quality_bar": plan_result.sprint_contract.quality_bar,
}

gen_result = generate(subproblems, sprint_contract)
print(format_generation(gen_result))

# 第3步：Evaluator 评估
eval_result = evaluate(gen_result.thought_chain, len(subproblems))
print(format_evaluation(eval_result))
```

## 核心概念

### 问题类型

deepthink 自动识别以下问题类型：

| 类型 | 关键词 | 示例 |
|------|--------|------|
| **决策类** | 是否、应该、要不要、值得、选择 | 是否应该换工作？ |
| **预测类** | 会怎样、未来、趋势、预测、前景 | AI 行业未来会怎样？ |
| **分析类** | 为什么、原因、分析、怎么做到 | 为什么项目失败了？ |
| **规划类** | 如何、怎么、计划、方案 | 如何学习编程？ |

### 置信度等级

生成器会为每个思考步骤评估置信度：

| 等级 | 含义 | 使用场景 |
|------|------|---------|
| **A** | 高度确信 | 有充分证据和少量假设 |
| **B** | 中等确信 | 证据一般，假设中等 |
| **C** | 低度确信 | 证据不足，假设较多 |
| **D** | 很低确信 | 证据很少，假设很多 |
| **F** | 无法确信 | 无证据，无法判断 |

### 四维度评分

评估器会从四个维度评分（0-10）：

| 维度 | 含义 | 评分标准 |
|------|------|---------|
| **完整性** | 是否覆盖所有子问题 | 是否遗漏关键视角 |
| **严谨性** | 推理是否有逻辑缺口 | 证据是否充分 |
| **诚实性** | 不确定性是否充分标记 | 是否过度自信 |
| **可操作性** | 结论是否可执行 | 是否给出具体建议 |

**通过标准：** 所有维度 ≥ 7 分

## 使用示例

### 示例1：决策问题

```python
from harness import run_harness, format_harness_result

result = run_harness(
    problem="是否应该创业？",
    context="我有10年工作经验，存款100万，有一个创业想法"
)

print(format_harness_result(result))
```

**输出包括：**
- 问题拆解（4个子问题）
- 思考链（4-5个步骤）
- 四维度评分
- 改进建议（如果需要）
- 最终结论

### 示例2：预测问题

```python
result = run_harness(
    problem="未来5年房价会怎样？",
    context="考虑到政策、经济、人口等因素"
)

print(format_harness_result(result))
```

### 示例3：规划问题

```python
result = run_harness(
    problem="如何从零开始学习机器学习？",
    context="没有编程基础，想成为 ML 工程师"
)

print(format_harness_result(result))
```

## 高级用法

### 自定义配置

```python
from harness import run_harness, HarnessConfig

config = HarnessConfig(
    max_iterations=3,           # 最多迭代3次
    quality_threshold=7,        # 所有维度 ≥ 7 分通过
    enable_sprint=True,         # 启用 Sprint Contract
    evaluator_strictness="high" # 严格评估
)

result = run_harness(
    problem="你的问题",
    context="额外上下文",
    config=config
)
```

### 获取详细的迭代记录

```python
result = run_harness(problem="你的问题")

# 查看每一轮迭代
for i, iteration in enumerate(result.iterations, 1):
    print(f"\n迭代 {i}:")
    print(f"  子问题数：{len(iteration.planner_output['subproblems'])}")
    print(f"  思考步骤：{len(iteration.generator_output['thought_chain'])}")
    print(f"  平均评分：{iteration.evaluator_output['avg_score']:.1f}/10")
    print(f"  状态：{iteration.verdict}")
```

## 文件结构

```
skills/deepthink-harness/
├── ARCHITECTURE.md          # 架构文档
├── planner.py              # 规划器模块
├── generator.py            # 生成器模块
├── evaluator.py            # 评估器模块
├── harness.py              # 迭代循环主模块
├── test_e2e.py             # 端到端测试
├── TEST_REPORT.md          # 测试报告
└── publish_to_instreet.bat # InStreet 发布脚本
```

## 常见问题

### Q1: 如何处理低置信度的结论？

A: 如果评估器给出低置信度（D/F 级），系统会自动进行改进迭代。你可以：
- 提供更多上下文信息
- 明确指出哪些方面不确定
- 让系统进行多轮迭代

### Q2: 如何自定义问题分解？

A: 目前 Planner 会根据问题类型自动分解。如果需要自定义，可以：
1. 修改 `planner.py` 中的 `get_decomposition_template()` 函数
2. 或者直接调用 `generator.generate()` 并传入自定义的子问题列表

### Q3: 如何集成到其他系统？

A: deepthink 是模块化设计，可以：
1. 导入单个模块（Planner/Generator/Evaluator）
2. 或使用完整的 Harness 流程
3. 所有模块都支持 JSON 输入输出

### Q4: 性能如何？

A: 
- 单次迭代：< 1 秒（不含 API 调用）
- 完整流程（3 轮迭代）：< 3 秒
- 内存占用：< 50MB

## 技术细节

### 数据流

```
用户问题
    ↓
[Planner] → 子问题 + Sprint Contract
    ↓
[Generator] → 思考链 + 自我质疑
    ↓
[Evaluator] → 四维度评分 + 问题识别
    ↓
通过？ → 是 → 输出最终结论
    ↓
    否 → 改进反馈 → [Generator] (循环)
```

### 置信度评估算法

```
证据充分度（0-3）
+ 假设少量（0-3）
+ 思考深度（0-2）
= 总分（0-8）

总分 ≥ 8 → A 级
总分 ≥ 6 → B 级
总分 ≥ 4 → C 级
总分 ≥ 2 → D 级
总分 < 2 → F 级
```

## 版本信息

- **版本：** v2.0
- **发布日期：** 2026-03-27
- **状态：** 正式版
- **代码行数：** 1260 行
- **测试覆盖：** 3/3 通过

## 许可证

deepthink v2.0 - 开源项目

---

**需要帮助？** 查看 ARCHITECTURE.md 了解更多技术细节。
