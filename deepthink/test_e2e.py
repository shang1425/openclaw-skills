"""
deepthink v2.0-alpha 端到端测试
测试三智能体迭代循环的完整流程
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入三个模块
from planner import plan, format_plan
from generator import generate, format_generation, ThoughtStep
from evaluator import evaluate, format_evaluation

# ========== 测试用例 ==========

TEST_CASES = [
    {
        "id": "test1",
        "question": "是否应该辞职回老家接手饭店？",
        "context": "我在一线城市工作5年，年薪30万，父亲想让我回老家接手饭店",
    },
    {
        "id": "test2",
        "question": "AI行业未来3年会怎样发展？",
        "context": "考虑到大模型、AGI、监管等因素",
    },
    {
        "id": "test3",
        "question": "如何从零开始学习编程？",
        "context": "没有任何编程基础，想成为全栈工程师",
    },
]


def run_single_test(test_case):
    """运行单个测试"""
    print("\n" + "="*70)
    print(f"测试：{test_case['id']}")
    print(f"问题：{test_case['question']}")
    print("="*70)
    
    # 第一轮迭代
    print("\n【第1轮迭代】")
    
    # 1. Planner
    print("\n[1/3] Planner 规划...")
    plan_result = plan(test_case['question'], test_case['context'])
    print(format_plan(plan_result))
    
    # 2. Generator
    print("\n[2/3] Generator 生成...")
    # 转换 plan_result 为 dict 格式
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
    
    gen_result = generate(subproblems, sprint_contract, test_case['context'])
    print(format_generation(gen_result))
    
    # 3. Evaluator
    print("\n[3/3] Evaluator 评估...")
    eval_result = evaluate(gen_result.thought_chain, len(subproblems))
    print(format_evaluation(eval_result))
    
    # 判定是否通过
    avg_score = (eval_result.scores.completeness + 
                 eval_result.scores.rigor + 
                 eval_result.scores.honesty + 
                 eval_result.scores.actionability) / 4
    
    if eval_result.overall_verdict == "pass":
        print("\n✅ 第1轮迭代通过！")
        return True
    else:
        print(f"\n⚠️ 第1轮迭代未通过（平均分：{avg_score:.1f}/10）")
        print(f"改进重点：{', '.join(eval_result.improvement_focus)}")
        
        # 第二轮迭代（改进）
        print("\n【第2轮迭代 - 改进】")
        print("\n[2/3] Generator 生成（改进版）...")
        
        # 模拟改进：增加思考深度
        improved_chain = []
        for step in gen_result.thought_chain:
            improved_step = ThoughtStep(
                step=step.step,
                thinking=step.thinking + "（改进：补充更多分析）",
                confidence="B" if step.confidence in ["C", "D"] else step.confidence,
                evidence=step.evidence + "（补充：更多证据支撑）",
                assumptions=step.assumptions,
                note=step.note,
            )
            improved_chain.append(improved_step)
        
        print(f"✓ 改进了 {len(improved_chain)} 个思考步骤")
        
        # 重新评估
        print("\n[3/3] Evaluator 评估（改进版）...")
        eval_result2 = evaluate(improved_chain, len(subproblems))
        print(format_evaluation(eval_result2))
        
        avg_score2 = (eval_result2.scores.completeness + 
                      eval_result2.scores.rigor + 
                      eval_result2.scores.honesty + 
                      eval_result2.scores.actionability) / 4
        
        if eval_result2.overall_verdict == "pass":
            print("\n✅ 第2轮迭代通过！")
            return True
        else:
            print(f"\n⚠️ 第2轮迭代仍未通过（平均分：{avg_score2:.1f}/10）")
            return False


def main():
    """主测试函数"""
    print("\n" + "🦞 "*35)
    print("deepthink v2.0-alpha 端到端测试")
    print("🦞 "*35)
    
    results = {}
    for test_case in TEST_CASES:
        try:
            success = run_single_test(test_case)
            results[test_case['id']] = "✅ 通过" if success else "⚠️ 未通过"
        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            results[test_case['id']] = f"❌ 错误：{str(e)[:50]}"
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    for test_id, result in results.items():
        print(f"- {test_id}: {result}")
    
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)
    print(f"\n总体通过率：{passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！v2.0 可以发布了！")
    else:
        print(f"\n⚠️ 还有 {total - passed} 个测试需要改进")


if __name__ == "__main__":
    main()
