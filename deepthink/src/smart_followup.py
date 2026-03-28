"""
deepthink — 智能追问模块
自动检测推理中缺失的关键信息，按优先级追问
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class MissingInfo:
    """缺失信息"""
    info_type: str          # 信息类型（收入、年龄、负债等）
    priority: str           # 高（阻塞）/ 中 / 低
    trigger_keywords: list  # 触发关键词
    question: str           # 追问问题
    reason: str             # 为什么需要这个信息


# 追问规则
FOLLOWUP_RULES = [
    MissingInfo(
        info_type="收入差距",
        priority="高",
        trigger_keywords=["工作", "跳槽", "职业", "offer"],
        question="你目前收入多少？目标岗位能拿多少？",
        reason="收入差距是职业选择的核心变量",
    ),
    MissingInfo(
        info_type="年龄",
        priority="高",
        trigger_keywords=["工作", "创业", "职业", "跳槽"],
        question="你多大年龄？",
        reason="年龄影响风险承受能力和机会成本",
    ),
    MissingInfo(
        info_type="家庭负债",
        priority="高",
        trigger_keywords=["家庭", "孩子", "媳妇", "老婆", "结婚"],
        question="有没有房贷或车贷？",
        reason="有负债时，决策权重完全不同",
    ),
    MissingInfo(
        info_type="老家机会",
        priority="高",
        trigger_keywords=["回去", "老家", "回老家"],
        question="老家在哪？回去能做什么工作？",
        reason="老家的就业机会决定了回流的可行性",
    ),
    MissingInfo(
        info_type="伴侣态度",
        priority="中",
        trigger_keywords=["家庭", "孩子", "结婚", "配偶"],
        question="你的伴侣/家人希望你怎么选？",
        reason="重大决定需要家庭成员的共识",
    ),
    MissingInfo(
        info_type="储蓄",
        priority="中",
        trigger_keywords=["创业", "辞职", "跳槽"],
        question="目前有多少存款？能支撑多久？",
        reason="经济缓冲期决定了选择的安全边际",
    ),
]


def detect_missing_info(question: str, context: str = "") -> List[dict]:
    """
    检测推理中缺失的关键信息

    Args:
        question: 用户问题
        context: 已有的上下文

    Returns:
        缺失信息列表
    """
    question_lower = question.lower()
    context_lower = context.lower()
    combined = question_lower + " " + context_lower

    missing = []
    for rule in FOLLOWUP_RULES:
        # 检查是否触发
        triggered = any(kw in combined for kw in rule.trigger_keywords)
        if triggered:
            # 检查上下文是否已经包含这个信息
            has_info = any(
                keyword in context_lower
                for keyword in [rule.info_type, rule.question[:4]]
            )
            if not has_info:
                missing.append({
                    "info_type": rule.info_type,
                    "priority": rule.priority,
                    "question": rule.question,
                    "reason": rule.reason,
                })

    return missing


def should_conclude(missing: List[dict]) -> Tuple[bool, str]:
    """
    判断是否可以给出结论

    Returns:
        (can_conclude, reason)
    """
    blocking = [m for m in missing if m["priority"] == "高"]

    if blocking:
        info_types = "、".join(m["info_type"] for m in blocking)
        return (
            False,
            f"缺少关键信息（{info_types}），结论可能不准确"
        )
    return True, "信息充足，可以给出结论"


def generate_followup(missing: List[dict]) -> str:
    """生成追问文本"""
    if not missing:
        return ""

    lines = ["---", "⬇️ 为了给出更准确的建议，需要补充几个信息：\n"]

    # 按优先级排序
    high = [m for m in missing if m["priority"] == "高"]
    medium = [m for m in missing if m["priority"] == "中"]

    for i, m in enumerate(high + medium, 1):
        lines.append(f"{i}. {m['question']}")
        lines.append(f"   （需要这个信息是因为：{m['reason']}）")

    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    # 测试1：信息不足
    print("=== 测试1：信息不足 ===")
    missing = detect_missing_info("要不要从上海回老家工作？")
    can, reason = should_conclude(missing)
    print(f"可否结论：{can}")
    print(f"原因：{reason}")
    print(f"缺失信息：{len(missing)} 个")
    for m in missing:
        print(f"  [{m['priority']}] {m['info_type']}: {m['question']}")

    # 测试2：信息充足
    print("\n=== 测试2：信息充足 ===")
    context = "我31岁，月薪1万，有房贷"
    missing2 = detect_missing_info("要不要跳槽？", context)
    can2, reason2 = should_conclude(missing2)
    print(f"可否结论：{can2}")
    print(f"缺失信息：{len(missing2)} 个")

    print("\n✅ 测试通过")
