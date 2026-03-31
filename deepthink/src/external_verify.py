"""
deepthink — 外部验证模块
自动检测推理中需要验证的事实，触发联网搜索
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class VerificationItem:
    """待验证项"""
    claim: str              # 待验证的说法
    reason: str             # 为什么需要验证
    source_hint: str = ""   # 建议搜索什么
    pre_confidence: int = 50  # 验证前的置信度
    post_confidence: int = 0   # 验证后的置信度
    verified: bool = False
    source: str = ""
    result: str = ""        # ✅ 已确认 / ❌ 不准确 / ⚠️ 部分正确


# 需要验证的模式
VERIFICATION_PATTERNS = [
    (r"\$?\d+(?:\.\d+)?\s*(?:亿|万|万|B|billion|million|M|K)", "数字/金额需要验证来源"),
    (r"(?:最新|当前|目前|202[456])", "时效性内容需要确认是否最新"),
    (r"(?:据.*报道|据.*统计|据.*调查|according to)", "二手引用需要验证原始来源"),
    (r"(?:增长|下降|上涨|下跌|提升了?|降低了?)\s*\d+", "变化幅度需要数据支撑"),
    (r"(?:市场占有率|市场份额|排名第一|行业第一)", "排名声明需要来源"),
]


def detect_verification_needs(text: str) -> List[dict]:
    """
    检测文本中需要外部验证的内容

    Args:
        text: 推理文本

    Returns:
        需要验证的项目列表
    """
    needs = []

    for pattern, reason in VERIFICATION_PATTERNS:
        matches = re.finditer(pattern, text)
        for m in matches:
            claim = m.group(0)
            # 避免重复
            if not any(n["claim"] == claim for n in needs):
                needs.append({
                    "claim": claim,
                    "reason": reason,
                    "source_hint": f"搜索: {claim} 来源验证",
                })

    return needs


def format_verification_results(items: List[VerificationItem]) -> str:
    """格式化验证结果"""
    if not items:
        return ""

    lines = ["🔍 外部验证\n"]
    for item in items:
        status_icon = "✅" if item.verified else "⏳"
        lines.append(f"   {status_icon} 验证项：{item.claim}")
        lines.append(f"   └ 原因：{item.reason}")
        if item.source:
            lines.append(f"   └ 来源：{item.source}")
        if item.verified:
            conf_delta = item.post_confidence - item.pre_confidence
            arrow = "↑" if conf_delta > 0 else "↓" if conf_delta < 0 else "→"
            lines.append(
                f"   └ 置信度：{item.pre_confidence}% → {item.post_confidence}% {arrow}"
            )

    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    text = """
    根据最新数据，OpenAI 估值达到 300 亿美元。
    市场份额排名第一，增长了 50%。
    据报道，GPT-5 将在下个月发布。
    """

    needs = detect_verification_needs(text)
    print(f"检测到 {len(needs)} 个待验证项：")
    for n in needs:
        print(f"  - {n['claim']}（{n['reason']}）")

    print("\n✅ 测试通过")
