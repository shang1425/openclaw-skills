"""
Planner — 规划器模块
将复杂问题拆解为子问题，定义成功标准（Sprint Contract）
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from llm_client import LLMClient


class UncertaintyLevel(Enum):
    """不确定性等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SubProblem:
    """子问题"""
    id: str                      # sp1, sp2, ...
    question: str                # 子问题内容
    success_criteria: List[str]  # 成功标准
    uncertainty: UncertaintyLevel
    priority: int = 1            # 1=高, 2=中, 3=低
    assigned_role: str = ""      # 分配的角色（分析师/魔鬼代言人/实用主义者/远见者）


@dataclass
class SprintContract:
    """短跑合约 — 本次思考的目标和交付标准"""
    goal: str                    # 目标
    deliverables: List[str]      # 交付物
    quality_bar: str             # 质量标准
    time_limit: Optional[str] = None  # 时间限制


@dataclass
class PlanResult:
    """规划结果"""
    original_problem: str
    subproblems: List[SubProblem]
    sprint_contract: SprintContract
    context_needed: List[str] = field(default_factory=list)  # 需要的额外上下文
    assumptions: List[str] = field(default_factory=list)     # 初始假设


# ========== 问题分解策略 ==========

def detect_problem_type(question: str) -> str:
    """检测问题类型"""
    question_lower = question.lower()
    
    # 决策类
    if any(kw in question_lower for kw in ["是否", "应该", "要不要", "值得", "选择"]):
        return "decision"
    
    # 预测类
    if any(kw in question_lower for kw in ["会怎样", "未来", "趋势", "预测", "前景"]):
        return "prediction"
    
    # 分析类
    if any(kw in question_lower for kw in ["为什么", "原因", "分析", "怎么做到"]):
        return "analysis"
    
    # 规划类
    if any(kw in question_lower for kw in ["如何", "怎么", "计划", "方案"]):
        return "planning"
    
    # 默认
    return "general"


def get_decomposition_template(problem_type: str) -> List[str]:
    """根据问题类型返回分解模板"""
    templates = {
        "decision": [
            "可行性分析",
            "风险评估",
            "收益预期",
            "替代方案",
        ],
        "prediction": [
            "现状分析",
            "关键变量识别",
            "趋势推演",
            "不确定性来源",
        ],
        "analysis": [
            "现象描述",
            "直接原因",
            "深层原因",
            "相关因素",
        ],
        "planning": [
            "目标明确",
            "资源评估",
            "路径设计",
            "风险预案",
        ],
        "general": [
            "核心要素",
            "关键关系",
            "不确定性",
            "行动方向",
        ],
    }
    return templates.get(problem_type, templates["general"])


def assign_role_to_subproblem(subproblem_title: str, index: int) -> str:
    """为子问题分配角色"""
    # 根据子问题内容智能分配角色
    title_lower = subproblem_title.lower()
    
    if any(kw in title_lower for kw in ["风险", "质疑", "反面", "问题"]):
        return "😈 魔鬼代言人"
    
    if any(kw in title_lower for kw in ["可行", "资源", "执行", "方案", "路径"]):
        return "🎯 实用主义者"
    
    if any(kw in title_lower for kw in ["趋势", "未来", "前景", "长期"]):
        return "🔮 远见者"
    
    if any(kw in title_lower for kw in ["收益", "成本", "数据", "分析"]):
        return "🧠 分析师"
    
    # 轮询分配
    roles = ["🧠 分析师", "😈 魔鬼代言人", "🎯 实用主义者", "🔮 远见者"]
    return roles[index % len(roles)]


# ========== AI 驱动的规划（新增）============

PLANNER_SYSTEM = """你是一个思维分析框架规划师。给定用户问题，输出严格JSON：
{
  "problem_type": "decision/prediction/analysis/planning/general",
  "subproblems": [
    {
      "id": "sp1",
      "question": "具体问题",
      "assigned_role": "🧠分析师 / 😈魔鬼代言人 / 🎯实用主义者 / 🔮远见者",
      "uncertainty": "high/medium/low",
      "priority": 1,
      "success_criteria": ["标准"]
    }
  ],
  "sprint_contract": {
    "goal": "目标",
    "deliverables": ["交付物"],
    "quality_bar": "质量标准"
  },
  "context_needed": [],
  "assumptions": []
}
只输出JSON。
"""


def plan_with_llm(question: str, context: str, client: "LLMClient", max_subproblems: int = 4) -> PlanResult:
    """
    使用 LLM 进行真实规划
    
    Args:
        question: 用户问题
        context: 额外上下文
        client: LLM 客户端
        max_subproblems: 最大子问题数
    
    Returns:
        PlanResult: 规划结果
    """
    context_section = f"\n\n额外上下文：\n{context}" if context else ""
    prompt = f"""请分析以下问题，输出严格的 JSON：

问题：{question}
{context_section}
子问题数量上限：{max_subproblems}

注意：
- 每个子问题的 question 字段要具体、可回答，不要太泛
- uncertainty 要根据问题本身的复杂度和信息量判断
- 只输出 JSON，不要其他内容"""

    raw = client.chat_once(
        system=PLANNER_SYSTEM,
        prompt=prompt,
        temperature=0.3,
        max_tokens=2048,
        timeout=120,
    )

    # 尝试提取 JSON
    data = _extract_json(raw)

    # 构建结果
    subproblems = []
    for sp_data in data.get("subproblems", []):
        uncertainty_str = sp_data.get("uncertainty", "medium")
        try:
            uncertainty = UncertaintyLevel(uncertainty_str)
        except ValueError:
            uncertainty = UncertaintyLevel.MEDIUM

        subproblems.append(SubProblem(
            id=sp_data.get("id", f"sp{len(subproblems)+1}"),
            question=sp_data.get("question", sp_data.get("title", "")),
            success_criteria=sp_data.get("success_criteria", [f"回答了 {sp_data.get('title', '')}"]),
            uncertainty=uncertainty,
            priority=sp_data.get("priority", 1),
            assigned_role=sp_data.get("assigned_role", "🧠 分析师"),
        ))

    sprint_data = data.get("sprint_contract", {})
    sprint = SprintContract(
        goal=sprint_data.get("goal", f"分析：{question[:40]}"),
        deliverables=sprint_data.get("deliverables", ["分析结论"]),
        quality_bar=sprint_data.get("quality_bar", "置信度 ≥ B级"),
    )

    return PlanResult(
        original_problem=question,
        subproblems=subproblems,
        sprint_contract=sprint,
        context_needed=data.get("context_needed", []),
        assumptions=data.get("assumptions", []),
    )


def _extract_json(raw: str) -> dict:
    """从 LLM 输出中提取 JSON"""
    # 去掉 markdown 代码块
    text = raw.strip()
    if text.startswith("```"):
        # 去掉 ```json 或 ```\n
        lines = text.split("\n")
        text = "\n".join(lines[1:])  # 去掉第一行
        text = text.rstrip("`").rstrip()  # 去掉结尾的 ```

    # 找第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析失败，使用回退逻辑：{e}")
        # 回退到启发式
        ptype = detect_problem_type(text)
        template = get_decomposition_template(ptype)
        return {
            "problem_type": ptype,
            "subproblems": [{"id": f"sp{i+1}", "title": t, "question": t, "uncertainty": "medium", "priority": 1, "assigned_role": "🧠 分析师", "success_criteria": ["回答了该问题"]} for i, t in enumerate(template[:4])],
            "sprint_contract": {"goal": f"分析：{text[:40]}", "deliverables": [], "quality_bar": ""},
            "context_needed": [],
            "assumptions": [],
        }


# ========== 核心函数 ==========

def plan(
    question: str,
    context: str = "",
    max_subproblems: int = 4,
    client: "LLMClient" = None,
) -> PlanResult:
    """
    规划器主函数
    
    Args:
        question: 用户问题
        context: 额外上下文
        max_subproblems: 最大子问题数
    
    Returns:
        PlanResult: 规划结果
    
    Notes:
        - 若传入 client，则使用 LLM 真实规划（推荐）
        - 若不传 client，回退到启发式规则（兼容旧代码）
    """
    # 有 LLM 客户端时使用 AI 规划
    if client is not None:
        return plan_with_llm(question, context, client, max_subproblems)
    
    # 回退：启发式规则规划（原有逻辑）
    # 1. 检测问题类型
    problem_type = detect_problem_type(question)
    
    # 2. 获取分解模板
    template = get_decomposition_template(problem_type)[:max_subproblems]
    
    # 3. 构建子问题
    subproblems = []
    for i, title in enumerate(template):
        sp = SubProblem(
            id=f"sp{i+1}",
            question=f"{title}：针对「{question[:30]}{'...' if len(question) > 30 else ''}」",
            success_criteria=[
                f"明确回答了{title}相关问题",
                "给出置信度评估",
                "标记不确定性",
            ],
            uncertainty=UncertaintyLevel.MEDIUM,
            priority=1 if i < 2 else 2,
            assigned_role=assign_role_to_subproblem(title, i),
        )
        subproblems.append(sp)
    
    # 4. 构建短跑合约
    sprint = SprintContract(
        goal=f"对「{question[:40]}{'...' if len(question) > 40 else ''}」给出结构化分析",
        deliverables=[
            "每个子问题的推理结论",
            "置信度评估",
            "不确定性标记",
            "最终综合结论",
        ],
        quality_bar="所有子问题置信度 ≥ B级，不确定性充分标记",
    )
    
    # 5. 识别需要的上下文
    context_needed = []
    if "收入" in question or "钱" in question or "投资" in question:
        context_needed.append("财务相关数据")
    if "职业" in question or "工作" in question:
        context_needed.append("职业背景信息")
    if "家庭" in question or "媳妇" in question or "孩子" in question:
        context_needed.append("家庭状况")
    
    # 6. 构建结果
    return PlanResult(
        original_problem=question,
        subproblems=subproblems,
        sprint_contract=sprint,
        context_needed=context_needed,
        assumptions=["用户提供的信息准确"] if not context else [],
    )


# ========== 格式化输出 ==========

def format_plan(p: PlanResult) -> str:
    """格式化规划结果"""
    lines = [
        "## 📋 Planner 规划结果",
        "",
        f"**问题类型：** {detect_problem_type(p.original_problem)}",
        f"**原始问题：** {p.original_problem}",
        "",
        "### 📦 子问题分解",
    ]
    
    for sp in p.subproblems:
        uncertainty_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[sp.uncertainty.value]
        lines.append(f"\n**{sp.id}** {sp.assigned_role}")
        lines.append(f"- 问题：{sp.question}")
        lines.append(f"- 成功标准：{', '.join(sp.success_criteria[:2])}")
        lines.append(f"- 不确定性：{uncertainty_icon} {sp.uncertainty.value}")
    
    lines.extend([
        "",
        "### 🎯 Sprint Contract",
        f"- **目标：** {p.sprint_contract.goal}",
        f"- **交付物：** {', '.join(p.sprint_contract.deliverables[:3])}",
        f"- **质量标准：** {p.sprint_contract.quality_bar}",
    ])
    
    if p.context_needed:
        lines.extend([
            "",
            "### 📌 需要的上下文",
        ])
        for ctx in p.context_needed:
            lines.append(f"- {ctx}")
    
    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    import sys
    import io
    # Windows 控制台编码修复
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 测试1：决策类问题
    print("=" * 50)
    print("测试1：决策类问题")
    print("=" * 50)
    p1 = plan("是否应该辞职回老家接手饭店？")
    print(format_plan(p1))
    
    # 测试2：预测类问题
    print("\n" + "=" * 50)
    print("测试2：预测类问题")
    print("=" * 50)
    p2 = plan("AI行业未来3年会怎样发展？")
    print(format_plan(p2))
    
    # 测试3：规划类问题
    print("\n" + "=" * 50)
    print("测试3：规划类问题")
    print("=" * 50)
    p3 = plan("如何从零开始学习编程？")
    print(format_plan(p3))