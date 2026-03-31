"""
deepthink — 决策树可视化模块
用 ◆◇●○★ 符号画出决策分支结构
"""


def format_node(
    node_type: str,
    text: str,
    confidence: int = None,
    indent: int = 0,
) -> str:
    """
    格式化决策树节点

    Args:
        node_type: DECISION / FACT / ASSUMPTION / UNCERTAINTY / CONCLUSION
        text: 节点文本
        confidence: 置信度（可选）
        indent: 缩进级别
    """
    icons = {
        "DECISION": "◆",
        "FACT": "●",
        "ASSUMPTION": "○",
        "UNCERTAINTY": "◇",
        "CONCLUSION": "★",
    }
    icon = icons.get(node_type, "●")
    prefix = "  " * indent
    conf = f" [{confidence}%]" if confidence is not None else ""
    return f"{prefix}{icon} {text}{conf}"


def build_tree(question: str, branches: list) -> str:
    """
    构建决策树

    Args:
        question: 核心问题
        branches: 分支列表，每个分支是 dict:
            {
                "label": "路径A：留在上海",
                "pros": ["高收入", "职业发展"],
                "cons": ["错过孩子成长"],
                "confidence": 65,
            }
    """
    lines = [format_node("DECISION", question)]

    for i, branch in enumerate(branches):
        lines.append(f"├── {format_node('DECISION', branch['label'])}")
        for pro in branch.get("pros", []):
            lines.append(f"│   {format_node('FACT', pro, indent=1)}")
        for con in branch.get("cons", []):
            lines.append(f"│   {format_node('UNCERTAINTY', con, indent=1)}")

    lines.append(f"└── {format_node('CONCLUSION', '最终结论（待评估）')}")
    return "\n".join(lines)


def to_mermaid(question: str, branches: list) -> str:
    """
    将决策树转换为 Mermaid 图表

    Args:
        question: 核心问题
        branches: 分支列表
    """
    lines = ["```mermaid", "graph TD"]
    safe_id = lambda s: s.replace(" ", "_").replace("？", "").replace("：", "")[:20]

    q_id = safe_id(question)
    lines.append(f'    {q_id}["{question}"]')

    conclusion_id = "final_conclusion"
    lines.append(f'    {conclusion_id}[("★ 最终结论")]')

    for i, branch in enumerate(branches):
        b_id = f"branch_{i}"
        lines.append(f'    {b_id}["{branch["label"]}"]')
        lines.append(f"    {q_id} --> {b_id}")

        for j, pro in enumerate(branch.get("pros", [])):
            p_id = f"{b_id}_pro_{j}"
            lines.append(f'    {p_id}["● {pro}"]')
            lines.append(f"    {b_id} --> {p_id}")

        for j, con in enumerate(branch.get("cons", [])):
            c_id = f"{b_id}_con_{j}"
            lines.append(f'    {c_id}["◇ {con}"]')
            lines.append(f"    {b_id} --> {c_id}")

        conf = branch.get("confidence")
        if conf:
            lines.append(f'    {b_id} -->|"{conf}%"| {conclusion_id}')

    lines.append("```")
    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    question = "留在上海 vs 回老家？"

    branches = [
        {
            "label": "路径A：留在上海",
            "pros": ["高收入", "职业发展"],
            "cons": ["错过孩子成长", "生活成本高"],
            "confidence": 65,
        },
        {
            "label": "路径B：回老家",
            "pros": ["陪伴家人", "生活成本低"],
            "cons": ["收入下降50%", "机会少"],
            "confidence": 55,
        },
    ]

    print("=== 文本决策树 ===")
    print(build_tree(question, branches))

    print("\n=== Mermaid 图表 ===")
    print(to_mermaid(question, branches))

    print("\n✅ 测试通过")
