# Deepthink Harness Architecture

> 将 Anthropic Harness Engineering 理念融入 deepthink 结构化思考框架

## 核心理念

**问题：** AI 思考时会"偷懒"
1. **上下文焦虑** — 思考链太长时草草收尾
2. **自我宽容** — 不会批评自己的推理

**解法：** 分离角色，迭代精进
- 规划器：拆解问题，定义成功标准
- 生成器：产出思考链
- 评估器：评审思考质量，指出缺口

---

## 三智能体架构

### 1. Planner（规划器）

**职责：**
- 接收用户问题
- 拆解为子问题
- 定义每个子问题的成功标准（短跑合约）
- 识别不确定性区域

**输出：**
```yaml
problem: "原始问题"
subproblems:
  - id: sp1
    question: "子问题1"
    success_criteria:
      - "标准1"
      - "标准2"
    uncertainty: "high/medium/low"
  - id: sp2
    ...
sprint_contract:
  goal: "本次思考的目标"
  deliverables: ["交付物1", "交付物2"]
  quality_bar: "质量标准"
```

### 2. Generator（生成器）

**职责：**
- 按 sprint_contract 产出思考链
- 对每个子问题进行推理
- 标记推理路径和置信度
- 自我质疑（已有模块）

**输出：**
```yaml
thought_chain:
  - step: 1
    thinking: "推理步骤"
    confidence: "A/B/C/D/F"
    evidence: "支撑证据"
    assumptions: ["假设1", "假设2"]
  
self_critique:
  - "质疑点1"
  - "质疑点2"
```

### 3. Evaluator（评估器）

**职责：**
- 检查思考链是否满足 success_criteria
- 识别逻辑缺口
- 评估置信度是否合理
- 指出遗漏的视角

**评分标准：**
```yaml
scores:
  completeness: 0-10  # 完整性：是否覆盖所有子问题
  rigor: 0-10         # 严谨性：推理是否有逻辑缺口
  honesty: 0-10       # 诚实性：不确定性是否充分标记
  actionability: 0-10 # 可操作性：结论是否可执行
  
issues:
  - type: "gap" | "bias" | "overconfidence"
    location: "step N"
    description: "问题描述"
    severity: "high/medium/low"
```

---

## 迭代循环

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  用户问题 ──► Planner ──► sprint_contract       │
│                              │                  │
│                              ▼                  │
│  ◄───────────────────── Evaluator ◄──┐        │
│         │                            │        │
│         │ 通过？                     │        │
│         ▼                            │        │
│    ┌─ Yes ──► 输出最终思考            │        │
│    │                                  │        │
│    └─ No ──► Generator ───────────────┘        │
│              (改进反馈)                        │
│                                                │
└─────────────────────────────────────────────────┘
```

**终止条件：**
- 评估器所有维度 ≥ 7 分
- 或达到最大迭代次数（默认 3 次）
- 或评估器认为"已足够好"

---

## 与现有 deepthink 的整合

### 现有模块（v1.1）
1. 问题结构拆解 → **保留，作为 Planner 的基础**
2. 不确定性标记 → **保留，Generator 使用**
3. 推理路径 → **保留，Generator 使用**
4. 备选视角 → **保留，Evaluator 使用**
5. 可操作结论 → **保留，最终输出**
6. 置信度评分 → **保留，Generator 使用**
7. 自我质疑 → **保留，但作为 Evaluator 的输入**

### 新增模块（v2.0）
- **Sprint Contract** — 短跑合约机制
- **Evaluator 评分** — 四维度评分
- **迭代循环** — 生成-评估-改进

---

## 配置参数

```yaml
harness:
  max_iterations: 3
  quality_threshold: 7  # 所有维度 ≥ 此值才通过
  enable_sprint: true   # 是否启用短跑机制
  
  planner:
    model: "default"    # 可用更强模型做规划
    
  evaluator:
    strictness: "medium"  # low/medium/high
    focus_areas:         # 重点关注维度
      - completeness
      - rigor
```

---

## 使用示例

**输入：**
```
"是否应该把所有积蓄投入这只股票？"
```

**Planner 输出：**
```yaml
subproblems:
  - id: sp1
    question: "这只股票的基本面如何？"
    success_criteria:
      - "分析了财务指标"
      - "考虑了行业趋势"
    uncertainty: high
    
  - id: sp2
    question: "我的风险承受能力如何？"
    success_criteria:
      - "评估了财务状况"
      - "考虑了时间 horizon"
    uncertainty: medium
    
sprint_contract:
  goal: "给出投资决策建议"
  deliverables: ["风险分析", "收益预期", "最终建议"]
  quality_bar: "必须明确标记不确定性"
```

**Generator 输出：**
```yaml
thought_chain:
  - step: 1
    thinking: "分析股票基本面..."
    confidence: C
    evidence: "仅凭用户描述，缺乏数据"
    assumptions: ["用户描述准确"]
    
  - step: 2
    thinking: "评估风险承受能力..."
    confidence: B
    evidence: "基于一般原则推理"
    
self_critique:
  - "我没有这只股票的实际数据"
  - "我不知道用户的实际财务状况"
```

**Evaluator 输出：**
```yaml
scores:
  completeness: 6   # 缺少对市场环境的分析
  rigor: 7          # 推理逻辑基本合理
  honesty: 9        # 不确定性标记充分
  actionability: 5  # 建议太模糊
  
issues:
  - type: gap
    location: "step 1"
    description: "缺少对市场整体环境的分析"
    severity: medium
    
  - type: overconfidence
    location: "step 2"
    description: "风险承受能力评估缺乏个性化"
    severity: high

verdict: "需要改进"
```

**第二轮 Generator（改进）：**
```yaml
thought_chain:
  - step: 1
    thinking: "补充：市场环境分析..."
    confidence: C
    note: "需要查看当前市场数据"
    
  - step: 2
    thinking: "改进风险承受能力评估..."
    confidence: B
    note: "建议用户填写风险评估问卷"
    
final_conclusion: |
  基于有限信息，无法给出明确投资建议。
  
  建议：
  1. 先查看这只股票的财务报表和行业分析
  2. 完成风险评估问卷确定自己的风险承受能力
  3. 考虑分散投资，不要把所有积蓄投入单一资产
  
  不确定性：高 — 缺乏关键数据支撑
```

---

## 下一步

1. ✅ 架构设计（本文档）
2. ✅ 实现 Planner 模块（planner.py）
3. ✅ 实现 Evaluator 模块（evaluator.py）
4. ✅ 实现 Generator 模块（generator.py）
5. ✅ 实现迭代循环（harness.py）
6. ⬜ 整合测试 + 发帖

---

*Created: 2026-03-26*
*Updated: 2026-03-29*
*Version: 3.0 — 真实 LLM 集成（modelroute / OpenAI / DeepSeek）*