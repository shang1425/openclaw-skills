"""
deepthink — 核心推理模块
问题结构拆解 + 置信度评分 + 自我质疑
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class ConfidenceGrade:
    """置信度等级"""
    S = "S"  # 90-100 几乎确定
    A = "A"  # 75-89 大概率正确
    B = "B"  # 60-74 倾向于正确
    C = "C"  # 45-59 不确定
    D = "D"  # 30-44 倾向于错误
    F = "F"  # 0-29 纯猜测


def get_grade(score: int) -> str:
    """根据分数获取等级"""
    if score >= 90: return ConfidenceGrade.S
    if score >= 75: return ConfidenceGrade.A
    if score >= 60: return ConfidenceGrade.B
    if score >= 45: return ConfidenceGrade.C
    if score >= 30: return ConfidenceGrade.D
    return ConfidenceGrade.F


def format_confidence(score: int, support: str = "", counter_example: str = "") -> str:
    """格式化置信度输出"""
    grade = get_grade(score)
    lines = [f"🎯 置信度：{score}%（{grade}级）"]
    if support:
        lines.append(f"   └ 支撑：{support}")
    if counter_example:
        lines.append(f"   └ 反例：{counter_example}")
    return "\n".join(lines)


def format_self_doubt(
    weakest: str = "",
    fatal_blow: str = "",
    unanswered: str = ""
) -> str:
    """格式化自我质疑输出"""
    lines = ["🪞 自我质疑"]
    if weakest:
        lines.append(f"   └ 最薄弱环节：{weakest}")
    if fatal_blow:
        lines.append(f"   └ 致命一击：{fatal_blow}")
    if unanswered:
        lines.append(f"   └ 未回答的问题：{unanswered}")
    return "\n".join(lines)


def format_problem_structure(
    core_question: str,
    key_variables: List[str] = None,
    boundary_in: List[str] = None,
    boundary_out: List[str] = None,
) -> str:
    """格式化问题结构输出"""
    lines = ["## 01 问题结构", f"- 核心问题：{core_question}"]
    if boundary_in:
        lines.append("- 边界条件：")
        lines.append(f"  - 范围内：{'、'.join(boundary_in)}")
    if boundary_out:
        lines.append(f"  - 范围外：{'、'.join(boundary_out)}")
    if key_variables:
        lines.append(f"- 关键变量：{'、'.join(key_variables)}")
    return "\n".join(lines)


@dataclass
class DeepThinkResult:
    """深度思考结果"""
    question: str
    conclusion: str
    confidence: int
    grade: str
    action_recommendation: str = ""
    support: str = ""
    counter_example: str = ""
    weakest_point: str = ""
    fatal_blow: str = ""
    unanswered: str = ""
    has_multi_agent: bool = False
    multi_agent_output: str = ""

    def format(self) -> str:
        """格式化输出"""
        lines = [
            format_problem_structure(self.question),
            "",
            format_confidence(self.confidence, self.support, self.counter_example),
            "",
            format_self_doubt(self.weakest_point, self.fatal_blow, self.unanswered),
            "",
            f"💡 **{self.conclusion}**",
        ]
        if self.action_recommendation:
            lines.append(f"\n🛠️ **行动建议：** {self.action_recommendation}")
        if self.has_multi_agent and self.multi_agent_output:
            lines.append(f"\n{self.multi_agent_output}")
        return "\n".join(lines)
