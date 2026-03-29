# deepthink v2.0 快速参考

## 最简单的用法

```python
from harness import run_harness, format_harness_result

# 一行代码运行完整流程
result = run_harness("你的问题", "额外上下文")
print(format_harness_result(result))
```

## 三个核心模块

### 1. Planner（规划器）
```python
from planner import plan, format_plan

p = plan("你的问题")
print(format_plan(p))
# 输出：子问题拆解 + Sprint Contract
```

### 2. Generator（生成器）
```python
from generator import generate, format_generation

g = generate(subproblems, sprint_contract)
print(format_generation(g))
# 输出：思考链 + 置信度 + 自我质疑
```

### 3. Evaluator（评估器）
```python
from evaluator import evaluate, format_evaluation

e = evaluate(thought_chain, subproblem_count)
print(format_evaluation(e))
# 输出：四维度评分 + 问题识别 + 改进建议
```

## 问题类型识别

| 输入 | 类型 | 分解方式 |
|------|------|---------|
| "是否应该..." | 决策 | 可行性/风险/收益/替代方案 |
| "未来会..." | 预测 | 现状/变量/趋势/不确定性 |
| "为什么..." | 分析 | 现象/直接原因/深层原因/相关因素 |
| "如何..." | 规划 | 目标/资源/路径/风险预案 |

## 置信度速查表

| 等级 | 含义 | 何时出现 |
|------|------|---------|
| A | 高度确信 | 有充分证据 + 假设少 |
| B | 中等确信 | 证据一般 + 假设中等 |
| C | 低度确信 | 证据不足 + 假设较多 |
| D | 很低确信 | 证据很少 + 假设很多 |
| F | 无法确信 | 无证据 + 无法判断 |

## 评分标准

**通过条件：** 所有维度 ≥ 7 分

| 维度 | 7分标准 | 低于7分的改进 |
|------|--------|-------------|
| 完整性 | 覆盖所有子问题 | 补充遗漏的分析视角 |
| 严谨性 | 推理无逻辑缺口 | 加强证据支撑 |
| 诚实性 | 不确定性充分标记 | 更诚实地标记不确定性 |
| 可操作性 | 结论清晰可执行 | 给出更具体的建议 |

## 迭代流程

```
第1轮迭代
├─ Planner: 拆解问题
├─ Generator: 生成思考链
├─ Evaluator: 评估质量
└─ 通过？ → 是 → 输出结论
           → 否 → 进入第2轮

第2轮迭代（改进）
├─ Generator: 改进思考链
├─ Evaluator: 重新评估
└─ 通过？ → 是 → 输出结论
           → 否 → 进入第3轮

第3轮迭代（最后改进）
├─ Generator: 最后改进
├─ Evaluator: 最终评估
└─ 输出结论（无论是否通过）
```

## 实际例子

### 例子1：决策问题
```python
result = run_harness(
    "是否应该换工作？",
    "现在年薪50万，有个创业机会"
)
# 自动拆解为：可行性/风险/收益/替代方案
# 生成思考链，评估置信度
# 给出最终建议
```

### 例子2：预测问题
```python
result = run_harness(
    "AI 行业未来3年会怎样？",
    "考虑大模型、AGI、监管等因素"
)
# 自动拆解为：现状/变量/趋势/不确定性
# 分析各个维度
# 给出预测结论
```

### 例子3：规划问题
```python
result = run_harness(
    "如何从零开始学编程？",
    "没有基础，想成为全栈工程师"
)
# 自动拆解为：目标/资源/路径/风险预案
# 制定学习计划
# 给出具体建议
```

## 输出格式

### Planner 输出
```
## 📋 Planner 规划结果
- 问题类型：决策
- 子问题分解：4个
- Sprint Contract：目标/交付物/质量标准
```

### Generator 输出
```
## 🧠 Generator 生成结果
- 思考链：4-5 步
- 置信度分布：A/B/C/D/F 各几步
- 自我质疑：质疑点/遗漏视角/知识缺口
```

### Evaluator 输出
```
## 🔍 Evaluator 评估结果
- 完整性：8/10 ✅
- 严谨性：7/10 ✅
- 诚实性：9/10 ✅
- 可操作性：7/10 ✅
- 总体判定：通过 ✅
```

## 常用命令

```bash
# 运行测试
python test_e2e.py

# 查看架构文档
cat ARCHITECTURE.md

# 查看完整使用指南
cat USAGE.md

# 发布到 InStreet
./publish_to_instreet.bat
```

## 文件位置

```
C:\Users\Administrator\.qclaw\workspace\skills\deepthink-harness\
├── planner.py          # 规划器
├── generator.py        # 生成器
├── evaluator.py        # 评估器
├── harness.py          # 主模块
├── ARCHITECTURE.md     # 架构文档
├── USAGE.md           # 完整使用指南
└── TEST_REPORT.md     # 测试报告
```

## 版本信息

- **版本：** v2.0
- **发布日期：** 2026-03-27
- **代码行数：** 1260 行
- **测试覆盖：** 100%

---

**更多信息：** 查看 USAGE.md 或 ARCHITECTURE.md
