"""
deepthink v2.0 调用示例
展示如何在实际项目中使用 deepthink
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========== 示例1：完整流程（推荐） ==========

def example_complete_flow():
    """使用完整的 Harness 流程"""
    print("\n" + "="*70)
    print("示例1：完整流程（推荐）")
    print("="*70)
    
    from harness import run_harness, format_harness_result, HarnessConfig
    
    # 配置
    config = HarnessConfig(
        max_iterations=3,
        quality_threshold=7,
        enable_sprint=True,
    )
    
    # 运行
    result = run_harness(
        problem="是否应该辞职创业？",
        context="我有10年工作经验，存款100万，有一个创业想法",
        config=config,
    )
    
    # 输出
    print(format_harness_result(result))
    
    return result


# ========== 示例2：分步调用 ==========

def example_step_by_step():
    """分步调用各个模块"""
    print("\n" + "="*70)
    print("示例2：分步调用")
    print("="*70)
    
    from planner import plan, format_plan
    from generator import generate, format_generation
    from evaluator import evaluate, format_evaluation
    
    question = "如何从零开始学习编程？"
    context = "没有任何编程基础，想成为全栈工程师"
    
    # 第1步：Planner
    print("\n【第1步】Planner 规划")
    plan_result = plan(question, context)
    print(format_plan(plan_result))
    
    # 第2步：Generator
    print("\n【第2步】Generator 生成")
    subproblems = [
        {
            "id": sp.id,
            "question": sp.question,
            "assigned_role": sp.assigned_role,
            "uncertainty": sp.uncertainty.value,
        }
        for sp in plan_result.subproblems
    ]
    sprint_contract = {
        "goal": plan_result.sprint_contract.goal,
        "deliverables": plan_result.sprint_contract.deliverables,
        "quality_bar": plan_result.sprint_contract.quality_bar,
    }
    
    gen_result = generate(subproblems, sprint_contract, context)
    print(format_generation(gen_result))
    
    # 第3步：Evaluator
    print("\n【第3步】Evaluator 评估")
    eval_result = evaluate(gen_result.thought_chain, len(subproblems))
    print(format_evaluation(eval_result))
    
    return eval_result


# ========== 示例3：自定义问题 ==========

def example_custom_problem():
    """处理自定义问题"""
    print("\n" + "="*70)
    print("示例3：自定义问题")
    print("="*70)
    
    from harness import run_harness, format_harness_result
    
    # 你可以输入任何问题
    problems = [
        {
            "question": "AI 行业未来3年会怎样发展？",
            "context": "考虑到大模型、AGI、监管等因素",
        },
        {
            "question": "为什么项目失败了？",
            "context": "项目投入200万，最后没有产生预期收益",
        },
        {
            "question": "应该选择哪个工作机会？",
            "context": "A公司：大厂，稳定，年薪80万；B公司：创业，风险，年薪120万",
        },
    ]
    
    for i, prob in enumerate(problems, 1):
        print(f"\n【问题{i}】{prob['question']}")
        result = run_harness(prob['question'], prob['context'])
        print(f"最终结论：{result.final_conclusion[:200]}...")


# ========== 示例4：获取详细信息 ==========

def example_detailed_info():
    """获取详细的迭代信息"""
    print("\n" + "="*70)
    print("示例4：获取详细信息")
    print("="*70)
    
    from harness import run_harness
    
    result = run_harness(
        "是否应该买房？",
        "现在房价很高，但我有首付"
    )
    
    print(f"\n总迭代次数：{result.total_iterations}")
    print(f"是否通过：{result.success}")
    print(f"\n最终评分：")
    print(f"  完整性：{result.quality_scores['completeness']}/10")
    print(f"  严谨性：{result.quality_scores['rigor']}/10")
    print(f"  诚实性：{result.quality_scores['honesty']}/10")
    print(f"  可操作性：{result.quality_scores['actionability']}/10")
    
    print(f"\n迭代历史：")
    for i, iteration in enumerate(result.iterations, 1):
        print(f"\n  迭代{i}：")
        print(f"    子问题数：{len(iteration.planner_output['subproblems'])}")
        print(f"    思考步骤：{len(iteration.generator_output['thought_chain'])}")
        print(f"    平均评分：{iteration.evaluator_output['avg_score']:.1f}/10")
        print(f"    状态：{iteration.verdict}")


# ========== 示例5：处理低置信度 ==========

def example_low_confidence():
    """处理低置信度的情况"""
    print("\n" + "="*70)
    print("示例5：处理低置信度")
    print("="*70)
    
    from harness import run_harness
    
    # 这个问题可能会产生低置信度
    result = run_harness(
        "2050年人类会怎样？",
        "考虑技术、气候、社会等因素"
    )
    
    print(f"\n最终状态：{'通过' if result.success else '未通过'}")
    print(f"迭代次数：{result.total_iterations}")
    
    # 查看最后一轮的置信度分布
    last_iteration = result.iterations[-1]
    confidence_dist = last_iteration.evaluator_output['confidence_analysis']
    
    print(f"\n置信度分布：")
    for level in ['A', 'B', 'C', 'D', 'F']:
        count = confidence_dist.get(level, 0)
        if count > 0:
            print(f"  {level}级：{count}步")


# ========== 主函数 ==========

if __name__ == "__main__":
    print("\n🦞 deepthink v2.0 调用示例")
    print("="*70)
    
    # 运行示例
    try:
        # 示例1：完整流程
        example_complete_flow()
        
        # 示例2：分步调用
        # example_step_by_step()
        
        # 示例3：自定义问题
        # example_custom_problem()
        
        # 示例4：获取详细信息
        # example_detailed_info()
        
        # 示例5：处理低置信度
        # example_low_confidence()
        
        print("\n" + "="*70)
        print("✅ 示例运行完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
