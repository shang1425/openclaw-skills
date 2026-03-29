"""
Harness — 迭代循环主模块
协调 Planner、Generator、Evaluator 的三智能体架构

v3.0 更新：
- 三个核心函数全部接入真实 LLM
- 新增 LLMConfig 配置项
- Self-Reflection Loop 集成
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING
from enum import Enum

# 导入真实模块
from planner import plan, format_plan, PlanResult
from generator import generate, format_generation, GeneratorResult
from evaluator import evaluate, format_evaluation, EvaluationResult, ThoughtStep

if TYPE_CHECKING:
    from llm_client import LLMClient


@dataclass
class HarnessConfig:
    """Harness 配置"""
    max_iterations: int = 3
    quality_threshold: int = 7  # 所有维度 ≥ 此值才通过
    enable_sprint: bool = True

    # 模型配置（新增 v3.0）
    # provider: "qclaw" | "openai" | "deepseek"
    model_provider: str = "qclaw"
    model: str = "modelroute"
    temperature_planner: float = 0.3
    temperature_generator: float = 0.6
    temperature_evaluator: float = 0.2
    max_tokens_planner: int = 2048
    max_tokens_generator: int = 4096
    max_tokens_evaluator: int = 2048

    # 反思链配置
    reflection_loops: int = 2  # Generator 反思轮数

    # 评估器严格度
    evaluator_strictness: str = "medium"  # low/medium/high


@dataclass
class IterationRecord:
    """迭代记录"""
    iteration: int
    planner_output: dict
    generator_output: dict
    evaluator_output: dict
    verdict: str  # "pass" / "needs_improvement" / "critical"
    improvement_focus: List[str] = field(default_factory=list)


@dataclass
class HarnessResult:
    """Harness 最终结果"""
    original_problem: str
    iterations: List[IterationRecord]
    final_conclusion: str
    total_iterations: int
    success: bool  # 是否通过评估
    quality_scores: Dict[str, int]  # 最终的四维度评分


# ========== 迭代循环 ==========

def run_harness(
    problem: str,
    context: str = "",
    config: Optional[HarnessConfig] = None,
    llm_client: "LLMClient" = None,
) -> HarnessResult:
    """
    Harness 主函数 — 运行完整的三智能体迭代循环

    Args:
        problem: 用户问题
        context: 额外上下文
        config: Harness 配置
        llm_client: LLM 客户端（不传则使用启发式模拟）

    Returns:
        HarnessResult: 最终结果
    """

    if config is None:
        config = HarnessConfig()

    iterations = []
    current_problem = problem
    current_context = context

    # 迭代循环
    for iteration_num in range(1, config.max_iterations + 1):
        print(f"\n{'='*60}")
        print(f"迭代 {iteration_num}/{config.max_iterations}")
        print(f"{'='*60}")

        # 1. Planner 阶段
        print("\n[1/3] Planner 规划中...")
        plan_result = plan(
            question=current_problem,
            context=current_context,
            max_subproblems=4,
            client=llm_client,
        )
        print(f"✓ 拆解为 {len(plan_result.subproblems)} 个子问题")

        # 2. Generator 阶段（带 Self-Reflection Loop）
        print("\n[2/3] Generator 生成中...")
        subproblems_as_dict = [
            {
                "id": sp.id,
                "question": sp.question,
                "assigned_role": sp.assigned_role,
                "uncertainty": sp.uncertainty.value,
            }
            for sp in plan_result.subproblems
        ]
        sprint_as_dict = {
            "goal": plan_result.sprint_contract.goal,
            "deliverables": plan_result.sprint_contract.deliverables,
            "quality_bar": plan_result.sprint_contract.quality_bar,
        }
        gen_result = generate(
            subproblems=subproblems_as_dict,
            sprint_contract=sprint_as_dict,
            context=current_context,
            client=llm_client,
            reflection_loops=config.reflection_loops,
        )
        print(f"✓ 生成思考链，{len(gen_result.thought_chain)} 步")

        # 3. Evaluator 阶段
        print("\n[3/3] Evaluator 评估中...")
        eval_result = evaluate(
            thought_chain=gen_result.thought_chain,
            subproblem_count=len(plan_result.subproblems),
            client=llm_client,
        )
        avg = (eval_result.scores.completeness + eval_result.scores.rigor +
               eval_result.scores.honesty + eval_result.scores.actionability) / 4
        print(f"✓ 评估完成，平均分 {avg:.1f}/10 ({eval_result.overall_verdict})")

        # 记录本次迭代
        record = IterationRecord(
            iteration=iteration_num,
            planner_output={
                "original_problem": plan_result.original_problem,
                "subproblems": subproblems_as_dict,
                "sprint_contract": sprint_as_dict,
            },
            generator_output={
                "thought_chain": [
                    {"step": ts.step, "thinking": ts.thinking, "confidence": ts.confidence,
                     "evidence": ts.evidence, "assumptions": ts.assumptions}
                    for ts in gen_result.thought_chain
                ],
                "self_critique": {
                    "critique_points": gen_result.self_critique.critique_points,
                    "missing_perspectives": gen_result.self_critique.missing_perspectives,
                    "knowledge_gaps": gen_result.self_critique.knowledge_gaps,
                },
                "final_conclusion": gen_result.final_conclusion,
            },
            evaluator_output={
                "scores": {
                    "completeness": eval_result.scores.completeness,
                    "rigor": eval_result.scores.rigor,
                    "honesty": eval_result.scores.honesty,
                    "actionability": eval_result.scores.actionability,
                },
                "avg_score": avg,
                "issues": [
                    {"type": iss.type.value, "description": iss.description, "severity": iss.severity.value}
                    for iss in eval_result.issues
                ],
                "verdict": eval_result.overall_verdict,
                "improvement_focus": eval_result.improvement_focus,
                "confidence_analysis": eval_result.confidence_analysis,
            },
            verdict=eval_result.overall_verdict,
            improvement_focus=eval_result.improvement_focus,
        )
        iterations.append(record)

        # 判定是否通过
        if eval_result.overall_verdict == "pass":
            print(f"\n✅ 第 {iteration_num} 次迭代通过！")
            break
        else:
            print(f"\n⚠️ 第 {iteration_num} 次迭代需要改进")
            if iteration_num < config.max_iterations:
                # 准备下一轮迭代
                current_context = _prepare_next_iteration(
                    record.generator_output,
                    record.evaluator_output,
                    current_context,
                )

    # 构建最终结果
    final_record = iterations[-1]
    success = final_record.verdict == "pass"

    result = HarnessResult(
        original_problem=problem,
        iterations=iterations,
        final_conclusion=final_record.generator_output['final_conclusion'],
        total_iterations=len(iterations),
        success=success,
        quality_scores=final_record.evaluator_output['scores'],
    )

    return result


# ========== 辅助函数 ==========

def _prepare_next_iteration(
    generator_output: dict,
    evaluator_output: dict,
    current_context: str,
) -> str:
    """准备下一轮迭代的上下文"""
    # 将评估反馈融入到下一轮的上下文中
    feedback = f"""
前一轮反馈：
- 改进重点：{', '.join(evaluator_output['improvement_focus'])}
- 问题：{len(evaluator_output['issues'])}个
- 知识缺口：{', '.join(generator_output['self_critique']['knowledge_gaps'][:2])}

请在下一轮迭代中重点关注这些问题。
"""
    return current_context + "\n" + feedback


# ========== 格式化输出 ==========

def format_harness_result(result: HarnessResult) -> str:
    """格式化 Harness 最终结果"""
    lines = [
        "=" * 70,
        "🦞 DEEPTHINK HARNESS — 最终结果",
        "=" * 70,
        "",
        f"**问题：** {result.original_problem}",
        f"**迭代次数：** {result.total_iterations}/{3}",
        f"**最终状态：** {'✅ 通过' if result.success else '⚠️ 需要改进'}",
        "",
        "### 📊 最终评分",
    ]
    
    for dimension, score in result.quality_scores.items():
        bar = "█" * (score // 2) + "░" * (5 - score // 2)
        lines.append(f"- {dimension}: {bar} {score}/10")
    
    lines.extend([
        "",
        "### 📝 最终结论",
        result.final_conclusion,
        "",
        "### 📋 迭代历史",
    ])
    
    for record in result.iterations:
        status_emoji = {"pass": "✅", "needs_improvement": "⚠️", "critical": "❌"}
        lines.append(f"\n**迭代 {record.iteration}** {status_emoji[record.verdict]}")
        lines.append(f"- 子问题数：{len(record.planner_output['subproblems'])}")
        lines.append(f"- 思考步骤：{len(record.generator_output['thought_chain'])}")
        lines.append(f"- 平均评分：{record.evaluator_output['avg_score']:.1f}/10")
        if record.improvement_focus:
            lines.append(f"- 改进重点：{', '.join(record.improvement_focus[:2])}")
    
    lines.append("\n" + "=" * 70)
    
    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    import sys
    import io
    # Windows 控制台编码修复
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 导入 LLM 客户端
    from llm_client import get_client

    # 测试：使用真实 LLM
    print("\n🦞 deepthink v3.0 — 真实 LLM 集成测试")
    print("=" * 60)

    client = get_client()
    print(f"LLM Client: {client}")

    config = HarnessConfig(
        max_iterations=2,
        reflection_loops=2,
    )

    result = run_harness(
        problem="是否应该辞职回老家接手饭店？",
        context="我在一线城市工作5年，年薪30万，父亲想让我回老家接手饭店",
        config=config,
        llm_client=client,
    )

    print(format_harness_result(result))
