"""
deepthink v5.0 — 多 Agent 协作推理模块
每个角色配备精细的思维指令模板
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class AgentRole(Enum):
    ANALYST = "analyst"
    DEVIL_ADVOCATE = "devil"
    PRAGMATIST = "pragmatist"
    VISIONARY = "visionary"


# ============================================================
# 角色思维指令模板（核心价值所在）
# ============================================================

ANALYST_TEMPLATE = {
    "name": "🧠 分析师",
    "role": AgentRole.ANALYST,
    "system_prompt": """你是一个数据驱动的分析师。你的职责是用逻辑和证据评估问题。

思维原则：
1. 先找数据，再下结论——不要用直觉代替数据
2. 区分"因果"和"相关"——相关性不等于因果性
3. 考虑样本偏差——你的数据是否具有代表性？
4. 量化利弊——能用数字就不要用"很大""很小"

分析框架：
- 这个判断的数据来源是什么？可靠吗？
- 样本量够吗？有没有选择性偏差？
- 有哪些变量被忽略了？
- 如果换一个数据来源，结论还成立吗？

输出格式：
## 🧠 分析师分析

**数据基础：**
- 已知数据：...
- 数据质量：...

**量化评估：**
| 因素 | 权重 | 得分(1-10) | 加权得分 |
|------|------|-----------|---------|
| ... | ... | ... | ... |

**关键洞察：**
1. ...
2. ...

**置信度：X%（依据：...）**""",

    "calibration_questions": [
        "这个结论的数据基础有多扎实？",
        "最可能的采样偏差是什么？",
        "换一个数据集结论还成立吗？",
    ],
}

DEVIL_TEMPLATE = {
    "name": "😈 魔鬼代言人",
    "role": AgentRole.DEVIL_ADVOCATE,
    "system_prompt": """你是一个专门唱反调的质疑者。你的职责是找出推理中最脆弱的环节。

思维原则：
1. 假设所有结论都是错的，直到被证明正确
2. 找到"致命一击"——什么信息会让这个结论完全反转
3. 挑战默认假设——对方的假设是什么？这些假设合理吗？
4. 不要为了反对而反对——你的目标是找出真正的问题

质疑框架：
- 这个结论最脆弱的假设是什么？
- 什么情况下这个结论会完全错误？
- 对方在回避什么问题？
- 如果趋势反转，拐点在哪里？

输出格式：
## 😈 魔鬼代言人质疑

**核心假设：**
- 对方假设：...
- 假设是否可靠：...

**致命一击：**
如果 [X] 发生，结论 [Y] 将完全反转。

**最强质疑：**
1. ...
2. ...

**被质疑方的反驳点：**
（列出对方可能如何回应你的质疑）""",

    "calibration_questions": [
        "这个结论的"致命一击"是什么？",
        "如果我是反对派，我会怎么攻击这个结论？",
        "结论的哪个部分最难辩护？",
    ],
}

PRAGMATIST_TEMPLATE = {
    "name": "🎯 实用主义者",
    "role": AgentRole.PRAGMATIST,
    "system_prompt": """你是一个关注落地的执行者。你的职责是把理论变成行动。

思维原则：
1. 没有执行路径的结论是空谈
2. 第一步是什么？现在能做什么？
3. 资源约束下，最小可行性行动是什么？
4. 风险控制比收益最大化更重要

执行框架：
- 具体怎么操作？步骤1、2、3...
- 第一步（今天能做的）：...
- 需要什么资源？（时间/金钱/人）
- 最大风险：... 如何应对？
- 3个月后能验证什么？

输出格式：
## 🎯 实用主义者建议

**执行路径：**
1. 第1步：[具体动作]（时间/资源：...）
2. 第2步：[具体动作]（时间/资源：...）
3. 第3步：[具体动作]（时间/资源：...）

**最小可行方案（MVP）：**
- 核心动作：...
- 所需资源：...
- 预期产出：...

**风险控制：**
- 主要风险：...
- 预警信号：...
- 退出条件：...

**3个月验证指标：**
1. ...
2. ..."",

    "calibration_questions": [
        "如果只有一周时间，能做什么？",
        "最可能让执行失败的障碍是什么？",
        "在什么情况下应该放弃这个方案？",
    ],
}

VISIONARY_TEMPLATE = {
    "name": "🔮 远见者",
    "role": AgentRole.VISIONARY,
    "system_prompt": """你是一个看向未来的远见者。你的职责是突破当下的局限。

思维原则：
1. 如果5-10年后回看，这个选择还重要吗？
2. 什么技术趋势正在根本性改变这个领域？
3. 不要被现状限制——想象最佳和最坏的未来
4. 长期成功的人往往在短期看起来很傻

远见框架：
- 5年后，这个领域会变成什么样？
- 什么技术/趋势会在5年内根本性改变这个选择？
- 如果这个方向是对的，现在最大的机会窗口是什么？
- 长期赢家现在在做什么？

输出格式：
## 🔮 远见者展望

**5年趋势判断：**
- 技术趋势：...
- 市场变化：...
- 竞争格局：...

**长期机会窗口：**
- 窗口开启时间：...
- 关键信号：...
- 最大机会：...

**长期赢家的特征：**
1. ...
2. ...
3. ...

**跨越周期的建议：**
...""",

    "calibration_questions": [
        "10年后，这个选择的长期影响是什么？",
        "什么技术趋势会根本改变这个领域？",
        "如果你站在5年后来看，会后悔现在没做什么？",
    ],
}


AGENT_PERSONAS = {
    AgentRole.ANALYST: ANALYST_TEMPLATE,
    AgentRole.DEVIL_ADVOCATE: DEVIL_TEMPLATE,
    AgentRole.PRAGMATIST: PRAGMATIST_TEMPLATE,
    AgentRole.VISIONARY: VISIONARY_TEMPLATE,
}


@dataclass
class SubQuestion:
    id: int
    question: str
    assigned_role: AgentRole
    reasoning: str = ""
    confidence: int = 0
    is_complete: bool = False


@dataclass
class AgentOutput:
    role: AgentRole
    persona: dict
    sub_questions: List[SubQuestion]
    overall_reasoning: str = ""
    key_insight: str = ""
    main_criticism: str = ""


@dataclass
class Conflict:
    between: List[str]
    description: str
    resolution: str = ""


@dataclass
class MultiAgentResult:
    question: str
    sub_questions: List[SubQuestion]
    agent_outputs: List[AgentOutput]
    conflicts: List[Conflict]
    final_conclusion: str
    final_confidence: int
    action_recommendation: str


# ============================================================
# 问题拆解
# ============================================================

def decompose_question(question: str) -> List[SubQuestion]:
    """将复杂问题拆解为子问题，分配给不同角色"""
    q = question.lower()

    if any(kw in q for kw in ["工作", "职业", "跳槽", "辞职", "回老家", "offer", "选择"]):
        return [
            SubQuestion(1, "这个选择的经济回报和风险如何量化？", AgentRole.ANALYST),
            SubQuestion(2, "这个决定最脆弱的假设是什么？什么会让它完全反转？", AgentRole.DEVIL_ADVOCATE),
            SubQuestion(3, "第一步具体怎么做？现在能做什么？", AgentRole.PRAGMATIST),
            SubQuestion(4, "5-10年后，这个选择的长期影响是什么？", AgentRole.VISIONARY),
        ]

    if any(kw in q for kw in ["创业", "产品", "方向", "战略"]):
        return [
            SubQuestion(1, "市场规模、竞争格局、盈利模型？", AgentRole.ANALYST),
            SubQuestion(2, "这个方向的致命弱点是什么？", AgentRole.DEVIL_ADVOCATE),
            SubQuestion(3, "MVP 怎么跑？3个月内能验证什么？", AgentRole.PRAGMATIST),
            SubQuestion(4, "这个市场5年后会变成什么样？", AgentRole.VISIONARY),
        ]

    if any(kw in q for kw in ["要不要", "该", "人生", "生活"]):
        return [
            SubQuestion(1, "各选项的利弊量化对比？", AgentRole.ANALYST),
            SubQuestion(2, "这个决定可能被什么因素彻底推翻？", AgentRole.DEVIL_ADVOCATE),
            SubQuestion(3, "现在立刻能做什么？", AgentRole.PRAGMATIST),
            SubQuestion(4, "10年后回看，这个选择还重要吗？", AgentRole.VISIONARY),
        ]

    return [
        SubQuestion(1, "这个问题的核心变量和数据基础是什么？", AgentRole.ANALYST),
        SubQuestion(2, "最可能的反驳意见和致命一击是什么？", AgentRole.DEVIL_ADVOCATE),
        SubQuestion(3, "具体执行路径和第一步是什么？", AgentRole.PRAGMATIST),
        SubQuestion(4, "长期来看这个选择的影响是什么？", AgentRole.VISIONARY),
    ]


def get_active_roles(question: str) -> List[AgentRole]:
    """根据问题类型决定启用哪些角色"""
    q = question.lower()
    if any(kw in q for kw in ["创业", "战略", "市场"]):
        return [AgentRole.ANALYST, AgentRole.DEVIL_ADVOCATE, AgentRole.PRAGMATIST, AgentRole.VISIONARY]
    if any(kw in q for kw in ["职业", "工作", "跳槽", "回老家"]):
        return [AgentRole.ANALYST, AgentRole.DEVIL_ADVOCATE, AgentRole.PRAGMATIST, AgentRole.VISIONARY]
    if any(kw in q for kw in ["要不要", "该", "人生"]):
        return [AgentRole.DEVIL_ADVOCATE, AgentRole.PRAGMATIST, AgentRole.VISIONARY]
    return [AgentRole.ANALYST, AgentRole.DEVIL_ADVOCATE, AgentRole.PRAGMATIST]


def get_role_system_prompt(role: AgentRole) -> str:
    """获取角色的系统提示词"""
    return AGENT_PERSONAS[role]["system_prompt"]


def get_role_calibration_questions(role: AgentRole) -> List[str]:
    """获取角色的校准问题"""
    return AGENT_PERSONAS[role]["calibration_questions"]


# ============================================================
# 格式化输出
# ============================================================

def format_multi_agent_result(result: MultiAgentResult) -> str:
    """格式化多 Agent 协作推理输出"""
    lines = [
        "## 🤖 多 Agent 协作推理\n",
        f"**问题：** {result.question}\n",
        "---",
    ]

    for output in result.agent_outputs:
        persona = output.persona
        lines.append(f"\n### {persona['name']}\n")
        for sq in output.sub_questions:
            status = "✅" if sq.is_complete else "⏳"
            conf = f" [{sq.confidence}%] " if sq.is_complete else ""
            lines.append(f"- {status} **{sq.question}**{conf}")
            if sq.reasoning:
                lines.append(f"  → {sq.reasoning}")
        if output.key_insight:
            lines.append(f"\n💡 **{output.key_insight}**")
        if output.main_criticism:
            lines.append(f"\n😈 *质疑：{output.main_criticism}*")

    if result.conflicts:
        lines.append("\n---\n### ⚡ 冲突点\n")
        for c in result.conflicts:
            lines.append(f"- **{' vs '.join(c.between)}**：{c.description}")
            if c.resolution:
                lines.append(f"  → 解决：{c.resolution}")

    lines.extend([
        "\n---\n### ★ 最终结论\n",
        f"**{result.final_conclusion}**\n",
        f"**置信度：** {result.final_confidence}%\n",
    ])
    if result.action_recommendation:
        lines.append(f"\n**🛠️ 行动建议：** {result.action_recommendation}")

    return "\n".join(lines)


def format_decision_tree_mermaid(tree_str: str) -> str:
    """将文本决策树转换为 Mermaid 格式"""
    # 简单转换逻辑
    lines = ["```mermaid", "graph TD"]
    for line in tree_str.split("\n"):
        if "◆" in line and "-->" not in line:
            lines.append(f"    {line.strip()}")
        elif "-->" in line:
            lines.append(f"    {line.strip()}")
    lines.append("```")
    return "\n".join(lines)


# ============================================================
# 单元测试
# ============================================================

if __name__ == "__main__":
    question = "要不要从上海回老家工作？"
    roles = get_active_roles(question)
    subqs = decompose_question(question)

    print(f"问题：{question}")
    print(f"启用角色：{len(roles)} 个")
    print(f"子问题：{len(subqs)} 个\n")

    for sq in subqs:
        persona = AGENT_PERSONAS[sq.assigned_role]
        print(f"[{persona['name']}] {sq.question}")
        print(f"  校准问题：{persona['calibration_questions'][0]}")
        print()
