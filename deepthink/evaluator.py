"""
Evaluator — 评估器模块
检查思考链质量，识别缺口，指导改进

新增 v3.0：
- 真实 LLM 评估（通过 llm_client）
- 支持混合模式：启发式评分 + AI 深度分析
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum
import json

if TYPE_CHECKING:
    from llm_client import LLMClient


class IssueType(Enum):
    """问题类型"""
    GAP = "gap"                    # 逻辑缺口
    BIAS = "bias"                  # 偏见/片面
    OVERCONFIDENCE = "overconfidence"  # 过度自信
    INCONSISTENCY = "inconsistency"    # 自相矛盾
    VAGUENESS = "vagueness"        # 模糊不清


class Severity(Enum):
    """严重程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(Enum):
    """置信度等级"""
    A = "A"  # 高度确信
    B = "B"  # 中等确信
    C = "C"  # 低度确信
    D = "D"  # 很低确信
    F = "F"  # 无法确信


@dataclass
class ThoughtStep:
    """思考步骤"""
    step: int
    thinking: str
    confidence: str  # A/B/C/D/F
    evidence: str
    assumptions: List[str] = field(default_factory=list)


@dataclass
class Issue:
    """问题记录"""
    type: IssueType
    location: str  # "step N" 或 "overall"
    description: str
    severity: Severity
    suggestion: str = ""  # 改进建议


@dataclass
class EvaluationScores:
    """评估分数"""
    completeness: int  # 0-10，是否覆盖所有子问题
    rigor: int         # 0-10，推理是否有逻辑缺口
    honesty: int       # 0-10，不确定性是否充分标记
    actionability: int # 0-10，结论是否可执行


@dataclass
class EvaluationResult:
    """评估结果"""
    scores: EvaluationScores
    issues: List[Issue]
    overall_verdict: str  # "pass" / "needs_improvement" / "critical"
    improvement_focus: List[str]  # 改进重点
    confidence_analysis: Dict[str, int]  # 各置信度等级的步骤数


# ========== 评估逻辑 ==========

def evaluate_completeness(
    thought_chain: List[ThoughtStep],
    subproblem_count: int,
) -> int:
    """
    评估完整性
    - 是否覆盖了所有子问题？
    - 是否有遗漏的关键视角？
    """
    score = 10
    
    # 检查步骤数是否足够
    if len(thought_chain) < subproblem_count:
        score -= (subproblem_count - len(thought_chain)) * 2
    
    # 检查是否有过度简化
    avg_thinking_length = sum(len(step.thinking) for step in thought_chain) / len(thought_chain)
    if avg_thinking_length < 50:  # 平均每步少于50字
        score -= 2
    
    # 检查是否有自相矛盾
    confidences = [step.confidence for step in thought_chain]
    if confidences.count("F") > len(thought_chain) * 0.3:  # 超过30%是F级
        score -= 3
    
    return max(0, min(10, score))


def evaluate_rigor(thought_chain: List[ThoughtStep]) -> int:
    """
    评估严谨性
    - 推理是否有逻辑缺口？
    - 假设是否明确？
    - 证据是否充分？
    """
    score = 10
    
    for step in thought_chain:
        # 检查证据充分性
        if not step.evidence or len(step.evidence) < 20:
            score -= 1
        
        # 检查假设是否明确
        if not step.assumptions:
            score -= 0.5
        
        # 检查低置信度是否有解释
        if step.confidence in ["D", "F"] and len(step.evidence) < 30:
            score -= 1
    
    # 检查步骤间的逻辑连贯性
    if len(thought_chain) > 1:
        # 简单启发式：如果置信度波动太大，可能有逻辑问题
        confidences = [ord(step.confidence) for step in thought_chain]
        if max(confidences) - min(confidences) > 3:  # 波动超过3个等级
            score -= 2
    
    return max(0, min(10, score))


def evaluate_honesty(thought_chain: List[ThoughtStep]) -> int:
    """
    评估诚实性
    - 不确定性是否充分标记？
    - 是否过度自信？
    - 是否承认知识边界？
    """
    score = 10
    
    # 统计置信度分布
    confidence_dist = {}
    for step in thought_chain:
        confidence_dist[step.confidence] = confidence_dist.get(step.confidence, 0) + 1
    
    # 如果全是A/B级，可能过度自信
    high_confidence_ratio = (confidence_dist.get("A", 0) + confidence_dist.get("B", 0)) / len(thought_chain)
    if high_confidence_ratio > 0.8:
        score -= 3
    
    # 如果全是D/F级，可能过度谨慎（但这不是坏事）
    low_confidence_ratio = (confidence_dist.get("D", 0) + confidence_dist.get("F", 0)) / len(thought_chain)
    if low_confidence_ratio > 0.7:
        score -= 1  # 轻微扣分
    
    # 检查是否有自我质疑
    # （这里假设 thought_chain 中包含了自我质疑的步骤）
    has_self_critique = any("质疑" in step.thinking or "不确定" in step.thinking for step in thought_chain)
    if not has_self_critique:
        score -= 2
    
    return max(0, min(10, score))


def evaluate_actionability(thought_chain: List[ThoughtStep]) -> int:
    """
    评估可操作性
    - 结论是否清晰？
    - 是否给出了具体建议？
    - 是否可以指导行动？
    """
    score = 10
    
    # 检查最后一步是否有明确结论
    if thought_chain:
        last_step = thought_chain[-1]
        
        # 检查是否有行动词
        action_words = ["建议", "应该", "可以", "需要", "必须", "推荐", "方案", "步骤"]
        has_action = any(word in last_step.thinking for word in action_words)
        if not has_action:
            score -= 3
        
        # 检查最后一步的置信度
        if last_step.confidence in ["D", "F"]:
            score -= 2
    
    # 检查是否有具体的下一步
    has_next_steps = any("下一步" in step.thinking or "接下来" in step.thinking for step in thought_chain)
    if not has_next_steps:
        score -= 1
    
    return max(0, min(10, score))


def identify_issues(
    thought_chain: List[ThoughtStep],
    scores: EvaluationScores,
) -> List[Issue]:
    """
    识别具体问题
    """
    issues = []
    
    # 1. 完整性问题
    if scores.completeness < 6:
        issues.append(Issue(
            type=IssueType.GAP,
            location="overall",
            description="思考链覆盖不全，可能遗漏了关键视角",
            severity=Severity.HIGH,
            suggestion="检查是否遗漏了某个子问题，补充相关分析",
        ))
    
    # 2. 严谨性问题
    if scores.rigor < 6:
        # 找出证据不足的步骤
        for step in thought_chain:
            if not step.evidence or len(step.evidence) < 20:
                issues.append(Issue(
                    type=IssueType.GAP,
                    location=f"step {step.step}",
                    description=f"证据不足：{step.thinking[:30]}...",
                    severity=Severity.MEDIUM,
                    suggestion="补充更多证据或数据支撑",
                ))
                break  # 只报告第一个
    
    # 3. 诚实性问题
    if scores.honesty < 6:
        confidence_dist = {}
        for step in thought_chain:
            confidence_dist[step.confidence] = confidence_dist.get(step.confidence, 0) + 1
        
        high_confidence_ratio = (confidence_dist.get("A", 0) + confidence_dist.get("B", 0)) / len(thought_chain)
        if high_confidence_ratio > 0.8:
            issues.append(Issue(
                type=IssueType.OVERCONFIDENCE,
                location="overall",
                description="过度自信：大部分步骤置信度过高",
                severity=Severity.MEDIUM,
                suggestion="降低某些步骤的置信度评估，更诚实地标记不确定性",
            ))
    
    # 4. 可操作性问题
    if scores.actionability < 6:
        issues.append(Issue(
            type=IssueType.VAGUENESS,
            location="overall",
            description="结论不够具体，难以指导行动",
            severity=Severity.MEDIUM,
            suggestion="补充具体的建议或行动步骤",
        ))
    
    # 5. 自相矛盾检测
    if len(thought_chain) > 1:
        for i in range(len(thought_chain) - 1):
            curr = thought_chain[i]
            next_step = thought_chain[i + 1]
            
            # 简单启发式：如果置信度大幅下降，可能有矛盾
            if ord(curr.confidence) - ord(next_step.confidence) > 2:
                issues.append(Issue(
                    type=IssueType.INCONSISTENCY,
                    location=f"step {curr.step}-{next_step.step}",
                    description=f"置信度大幅下降（{curr.confidence}→{next_step.confidence}），可能有逻辑矛盾",
                    severity=Severity.LOW,
                    suggestion="检查两个步骤之间的逻辑关系",
                ))
                break  # 只报告第一个
    
    return issues


def determine_verdict(scores: EvaluationScores) -> str:
    """
    判定总体评估结果
    """
    avg_score = (scores.completeness + scores.rigor + scores.honesty + scores.actionability) / 4
    
    if avg_score >= 7:
        return "pass"
    elif avg_score >= 5:
        return "needs_improvement"
    else:
        return "critical"


# ========== AI 驱动的评估（新增）============

EVALUATOR_SYSTEM = """你是一个批判性思维评估专家。从四维度评分（0-10），输出JSON：
{"scores":{"completeness":0-10,"rigor":0-10,"honesty":0-10,"actionability":0-10},"avg_score":0.0,"issues":[{"type":"gap/bias/overconfidence/inconsistency/vagueness","location":"step N或overall","description":"描述","severity":"high/medium/low","suggestion":"改进建议"}],"verdict":"pass/needs_improvement/critical","improvement_focus":["重点"],"confidence_analysis":{"A":0,"B":0,"C":0,"D":0,"F":0}}

判定：avg≥7=pass, 5≤avg<7=needs_improvement, avg<5=critical。只输出JSON。
"""


def evaluate_with_llm(
    thought_chain: List[ThoughtStep],
    subproblem_count: int,
    client: "LLMClient" = None,
) -> EvaluationResult:
    """
    使用 LLM 进行真实评估

    Args:
        thought_chain: 思考链
        subproblem_count: 子问题数量（用于评估完整性）
        client: LLM 客户端

    Returns:
        EvaluationResult: 评估结果
    """
    # 构建思考链描述（精简版，每个step一行）
    chain_text = " | ".join(
        f"步骤{ts.step}[{ts.confidence}]{ts.thinking[:80]}"
        for ts in thought_chain
    )

    prompt = f"""评估思考链（四维度0-10），输出JSON：
{chain_text}
步数={len(thought_chain)}，子问题数={subproblem_count}
注意：完整性看覆盖度，严谨性看证据，诚实性看置信度合理性，可操作性看结论清晰度。avg≥7=pass。
"""

    print(f"\n  [Evaluator] LLM 评估中...")
    raw = client.chat_once(
        system=EVALUATOR_SYSTEM,
        prompt=prompt,
        temperature=0.2,
        max_tokens=1024,
        timeout=120,
    )

    data = _extract_eval_json(raw)

    # 构建结果
    scores_data = data.get("scores", {})
    scores = EvaluationScores(
        completeness=scores_data.get("completeness", 5),
        rigor=scores_data.get("rigor", 5),
        honesty=scores_data.get("honesty", 5),
        actionability=scores_data.get("actionability", 5),
    )

    issues = []
    for iss in data.get("issues", []):
        try:
            issue_type = IssueType(iss.get("type", "gap"))
        except ValueError:
            issue_type = IssueType.GAP
        try:
            severity = Severity(iss.get("severity", "medium"))
        except ValueError:
            severity = Severity.MEDIUM
        issues.append(Issue(
            type=issue_type,
            location=iss.get("location", "overall"),
            description=iss.get("description", ""),
            severity=severity,
            suggestion=iss.get("suggestion", ""),
        ))

    return EvaluationResult(
        scores=scores,
        issues=issues,
        overall_verdict=data.get("verdict", "needs_improvement"),
        improvement_focus=data.get("improvement_focus", []),
        confidence_analysis=data.get("confidence_analysis", {}),
    )


def _extract_eval_json(raw: str) -> dict:
    """提取评估器的 JSON 输出"""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        text = text.rstrip("`").rstrip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"scores": {}, "issues": [], "verdict": "needs_improvement", "improvement_focus": [], "confidence_analysis": {}}


# ========== 核心函数 ==========

def evaluate(
    thought_chain: List[ThoughtStep],
    subproblem_count: int = 4,
    client: "LLMClient" = None,
    use_heuristic: bool = False,
) -> EvaluationResult:
    """
    评估器主函数
    
    Args:
        thought_chain: 思考链
        subproblem_count: 子问题数量（用于评估完整性）
    
    Returns:
        EvaluationResult: 评估结果
    
    Notes:
        - 若传入 client，则使用 LLM 评估
        - use_heuristic=True 时，同时运行启发式评估（用于对比参考）
        - 不传 client 且 use_heuristic=False 时，仅使用启发式评估
    """
    # 有 LLM 客户端时优先使用 AI 评估
    if client is not None:
        result = evaluate_with_llm(thought_chain, subproblem_count, client)
        if use_heuristic:
            # 同时跑启发式作为参考（不替换 AI 结果）
            heur_result = _evaluate_heuristic(thought_chain, subproblem_count)
            print(f"  [Evaluator 启发式参考] avg={heur_result.scores.completeness:.1f}/10, verdict={heur_result.overall_verdict}")
        return result
    
    # 纯启发式评估
    return _evaluate_heuristic(thought_chain, subproblem_count)


def _evaluate_heuristic(
    thought_chain: List[ThoughtStep],
    subproblem_count: int,
) -> EvaluationResult:
    """启发式评估（原有逻辑，抽取为独立函数）"""
    # 1. 计算各维度分数
    scores = EvaluationScores(
        completeness=evaluate_completeness(thought_chain, subproblem_count),
        rigor=evaluate_rigor(thought_chain),
        honesty=evaluate_honesty(thought_chain),
        actionability=evaluate_actionability(thought_chain),
    )
    
    # 2. 识别具体问题
    issues = identify_issues(thought_chain, scores)
    
    # 3. 判定总体结果
    verdict = determine_verdict(scores)
    
    # 4. 确定改进重点
    improvement_focus = []
    if scores.completeness < 7:
        improvement_focus.append("补充遗漏的分析视角")
    if scores.rigor < 7:
        improvement_focus.append("加强证据支撑")
    if scores.honesty < 7:
        improvement_focus.append("更诚实地标记不确定性")
    if scores.actionability < 7:
        improvement_focus.append("给出更具体的建议")
    
    # 5. 统计置信度分布
    confidence_dist = {}
    for step in thought_chain:
        confidence_dist[step.confidence] = confidence_dist.get(step.confidence, 0) + 1
    
    return EvaluationResult(
        scores=scores,
        issues=issues,
        overall_verdict=verdict,
        improvement_focus=improvement_focus,
        confidence_analysis=confidence_dist,
    )


# ========== 格式化输出 ==========

def format_evaluation(result: EvaluationResult) -> str:
    """格式化评估结果"""
    lines = [
        "## 🔍 Evaluator 评估结果",
        "",
        "### 📊 四维度评分",
    ]
    
    # 评分卡
    scores_dict = {
        "完整性 (Completeness)": result.scores.completeness,
        "严谨性 (Rigor)": result.scores.rigor,
        "诚实性 (Honesty)": result.scores.honesty,
        "可操作性 (Actionability)": result.scores.actionability,
    }
    
    for name, score in scores_dict.items():
        bar = "█" * (score // 2) + "░" * (5 - score // 2)
        status = "✅" if score >= 7 else "⚠️" if score >= 5 else "❌"
        lines.append(f"- {name}: {bar} {score}/10 {status}")
    
    avg_score = sum(scores_dict.values()) / len(scores_dict)
    lines.append(f"\n**平均分：** {avg_score:.1f}/10")
    
    # 总体判定
    verdict_emoji = {"pass": "✅", "needs_improvement": "⚠️", "critical": "❌"}
    verdict_text = {"pass": "通过", "needs_improvement": "需要改进", "critical": "严重问题"}
    lines.append(f"\n**总体判定：** {verdict_emoji[result.overall_verdict]} {verdict_text[result.overall_verdict]}")
    
    # 问题列表
    if result.issues:
        lines.append("\n### 🚨 识别的问题")
        for issue in result.issues:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            lines.append(f"\n**{issue.type.value.upper()}** {severity_emoji[issue.severity.value]}")
            lines.append(f"- 位置：{issue.location}")
            lines.append(f"- 描述：{issue.description}")
            if issue.suggestion:
                lines.append(f"- 建议：{issue.suggestion}")
    
    # 改进重点
    if result.improvement_focus:
        lines.append("\n### 🎯 改进重点")
        for focus in result.improvement_focus:
            lines.append(f"- {focus}")
    
    # 置信度分布
    if result.confidence_analysis:
        lines.append("\n### 📈 置信度分布")
        for level in ["A", "B", "C", "D", "F"]:
            count = result.confidence_analysis.get(level, 0)
            if count > 0:
                lines.append(f"- {level}级：{count}步")
    
    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    import sys
    import io
    # Windows 控制台编码修复
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 构造测试数据
    thought_chain = [
        ThoughtStep(
            step=1,
            thinking="分析这只股票的基本面，查看财务报表和行业地位",
            confidence="B",
            evidence="基于一般投资原则，但缺乏具体数据",
            assumptions=["用户提供的信息准确"],
        ),
        ThoughtStep(
            step=2,
            thinking="评估用户的风险承受能力和财务状况",
            confidence="C",
            evidence="仅凭用户描述推断，缺乏详细财务数据",
            assumptions=["用户对自己的财务状况有准确认识"],
        ),
        ThoughtStep(
            step=3,
            thinking="考虑市场环境和宏观经济因素",
            confidence="D",
            evidence="缺乏实时市场数据",
            assumptions=["市场环境相对稳定"],
        ),
        ThoughtStep(
            step=4,
            thinking="综合以上分析，给出投资建议",
            confidence="C",
            evidence="基于前三步的分析，但整体不确定性较高",
            assumptions=["用户的目标是长期投资"],
        ),
    ]
    
    # 运行评估
    result = evaluate(thought_chain, subproblem_count=4)
    print(format_evaluation(result))
