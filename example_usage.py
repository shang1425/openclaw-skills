"""
example_usage.py - deepthink v6.0 使用示例

展示如何使用 deepthink v6.0 进行结构化深度思考和验证
"""

import asyncio
from deepthink_v6 import DeepthinkV6


async def example_basic():
    """基础示例：处理思考过程"""
    print("\n" + "=" * 70)
    print("示例 1: 基础使用 - 处理思考过程")
    print("=" * 70 + "\n")

    deepthink = DeepthinkV6(use_mock_search=True)

    thinking_text = """
    根据最新研究表明，全球气温在过去十年上升了1.5度。
    这意味着气候变化正在加速。
    我认为我们需要采取更积极的行动。
    数据显示，2023年的碳排放量增长了5%。
    因此，可以推断出环保政策的效果还不够明显。
    """

    print("📝 输入思考过程:")
    print(thinking_text)

    print("\n🚀 开始处理...\n")
    report = await deepthink.process(thinking_text)

    print(report.summary)

    # 导出报告
    deepthink.export_json(report, "example_report.json")
    deepthink.export_markdown(report, "example_report.md")

    print("✅ 报告已导出:")
    print("  - example_report.json")
    print("  - example_report.md")


async def example_detailed_analysis():
    """详细分析示例：逐个查看声明和验证结果"""
    print("\n" + "=" * 70)
    print("示例 2: 详细分析 - 逐个查看声明和验证结果")
    print("=" * 70 + "\n")

    deepthink = DeepthinkV6(use_mock_search=True)

    thinking_text = """
    根据 WHO 的数据，全球有超过 10 亿人患有肥胖症。
    这个数字在过去 20 年增长了 3 倍。
    我认为这是一个严重的公共卫生问题。
    因此，我们需要推行更严格的食品监管政策。
    """

    report = await deepthink.process(thinking_text)

    print(f"📊 总共提取了 {report.total_claims} 个声明\n")

    print("🔍 详细分析:\n")
    for i, result in enumerate(report.verification_results, 1):
        print(f"{i}. 声明: {result['claim']}")
        print(f"   类型: {result['status']}")
        print(f"   置信度: {result['confidence_before']:.2f} → {result['confidence_after']:.2f}")

        if result["supporting_evidence"]:
            print(f"   ✅ 支持证据: {len(result['supporting_evidence'])} 条")

        if result["opposing_evidence"]:
            print(f"   ❌ 反对证据: {len(result['opposing_evidence'])} 条")

        print()


async def example_filter_and_queue():
    """过滤和队列示例：按置信度过滤和获取验证队列"""
    print("\n" + "=" * 70)
    print("示例 3: 过滤和队列 - 按置信度过滤和获取验证队列")
    print("=" * 70 + "\n")

    from claim_extractor import ClaimExtractor, ClaimType

    extractor = ClaimExtractor()

    thinking_text = """
    根据研究表明，地球是圆的。
    我认为这很重要。
    数据显示，2023年的增长率是 5%。
    也许气候变化会影响农业。
    因此，我们需要采取行动。
    """

    claims = extractor.extract(thinking_text)

    print(f"📊 提取了 {len(claims)} 个声明:\n")

    for i, claim in enumerate(claims, 1):
        print(f"{i}. [{claim.claim_type.value}] {claim.text}")
        print(f"   置信度: {claim.confidence:.2f}")
        print(f"   需要验证: {claim.needs_verification}")
        print()

    # 按置信度过滤
    print("\n🔍 按置信度过滤 (≥ 0.6):\n")
    high_confidence = extractor.filter_by_confidence(claims, min_confidence=0.6)
    for claim in high_confidence:
        print(f"  - [{claim.claim_type.value}] {claim.text} ({claim.confidence:.2f})")

    # 获取验证队列
    print("\n📋 需要验证的声明队列:\n")
    queue = extractor.get_verification_queue(claims)
    for i, claim in enumerate(queue, 1):
        print(f"{i}. {claim.text}")
        print(f"   置信度: {claim.confidence:.2f}")
        print()


async def example_claim_types():
    """声明类型示例：展示不同类型的声明"""
    print("\n" + "=" * 70)
    print("示例 4: 声明类型 - 展示不同类型的声明")
    print("=" * 70 + "\n")

    from claim_extractor import ClaimExtractor, ClaimType

    extractor = ClaimExtractor()

    examples = {
        "事实 (FACT)": "根据研究表明，地球是圆的。",
        "数据 (DATA)": "2023年的增长率达到了 5%。",
        "观点 (OPINION)": "我认为这个方案很不错。",
        "推论 (INFERENCE)": "因此，可以推断出这个结论是正确的。",
    }

    for claim_type, text in examples.items():
        claims = extractor.extract(text)
        if claims:
            claim = claims[0]
            print(f"📌 {claim_type}")
            print(f"   文本: {claim.text}")
            print(f"   置信度: {claim.confidence:.2f}")
            print(f"   需要验证: {claim.needs_verification}")
            print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("deepthink v6.0 使用示例")
    print("=" * 70)

    await example_basic()
    await example_detailed_analysis()
    await example_filter_and_queue()
    await example_claim_types()

    print("\n" + "=" * 70)
    print("✅ 所有示例完成！")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
