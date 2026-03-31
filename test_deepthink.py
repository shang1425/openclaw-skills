"""
test_deepthink.py - deepthink v6.0 测试套件

运行所有测试：
  python -m pytest test_deepthink.py -v
  
或直接运行：
  python test_deepthink.py
"""

import asyncio
import json
from pathlib import Path

from claim_extractor import ClaimExtractor, ClaimType, Claim
from search_verifier import SearchVerifier, VerificationStatus
from deepthink_v6 import DeepthinkV6


class TestClaimExtractor:
    """声明提取器测试"""

    def __init__(self):
        self.extractor = ClaimExtractor()

    def test_extract_facts(self):
        """测试事实提取"""
        text = "根据研究表明，地球是圆的。"
        claims = self.extractor.extract(text)

        assert len(claims) > 0, "应该提取到至少一个声明"
        assert any(c.claim_type == ClaimType.FACT for c in claims), "应该识别为事实"
        print("✅ test_extract_facts 通过")

    def test_extract_data(self):
        """测试数据提取"""
        text = "2023年的增长率达到了5%。"
        claims = self.extractor.extract(text)

        assert len(claims) > 0, "应该提取到至少一个声明"
        assert any(c.claim_type == ClaimType.DATA for c in claims), "应该识别为数据"
        print("✅ test_extract_data 通过")

    def test_extract_opinion(self):
        """测试观点提取"""
        text = "我认为这个方案很不错。"
        claims = self.extractor.extract(text)

        assert len(claims) > 0, "应该提取到至少一个声明"
        assert any(c.claim_type == ClaimType.OPINION for c in claims), "应该识别为观点"
        print("✅ test_extract_opinion 通过")

    def test_extract_inference(self):
        """测试推论提取"""
        text = "因此，可以推断出这个结论是正确的。"
        claims = self.extractor.extract(text)

        assert len(claims) > 0, "应该提取到至少一个声明"
        assert any(
            c.claim_type == ClaimType.INFERENCE for c in claims
        ), "应该识别为推论"
        print("✅ test_extract_inference 通过")

    def test_confidence_calculation(self):
        """测试置信度计算"""
        text = "确实，地球是圆的。"
        claims = self.extractor.extract(text)

        assert len(claims) > 0
        # 包含"确实"应该提高置信度
        assert claims[0].confidence > 0.5, "置信度应该大于 0.5"
        print("✅ test_confidence_calculation 通过")

    def test_filter_by_confidence(self):
        """测试按置信度过滤"""
        text = """
        根据研究表明，地球是圆的。
        我认为这很重要。
        """
        claims = self.extractor.extract(text)
        high_confidence = self.extractor.filter_by_confidence(claims, min_confidence=0.6)

        assert len(high_confidence) <= len(claims), "过滤后数量应该减少或相同"
        print("✅ test_filter_by_confidence 通过")

    def test_get_verification_queue(self):
        """测试获取验证队列"""
        text = """
        根据研究表明，地球是圆的。
        我认为这很重要。
        """
        claims = self.extractor.extract(text)
        queue = self.extractor.get_verification_queue(claims)

        # 观点不应该在验证队列中
        assert not any(
            c.claim_type == ClaimType.OPINION for c in queue
        ), "观点不应该在验证队列中"
        print("✅ test_get_verification_queue 通过")

    def run_all(self):
        """运行所有测试"""
        print("\n🧪 运行声明提取器测试...\n")
        self.test_extract_facts()
        self.test_extract_data()
        self.test_extract_opinion()
        self.test_extract_inference()
        self.test_confidence_calculation()
        self.test_filter_by_confidence()
        self.test_get_verification_queue()
        print("\n✅ 所有声明提取器测试通过！\n")


class TestSearchVerifier:
    """搜索验证器测试"""

    def __init__(self):
        self.verifier = SearchVerifier(use_mock=True)

    async def test_verify_claim(self):
        """测试验证声明"""
        claim = Claim(
            text="全球气温在过去十年上升了1.5度",
            claim_type=ClaimType.DATA,
            confidence=0.7,
            context="根据最新研究表明，全球气温在过去十年上升了1.5度。",
            line_number=1,
            needs_verification=True,
        )

        result = await self.verifier.verify(claim)

        assert result.claim == claim, "结果应该包含原声明"
        assert result.status in VerificationStatus, "应该有验证状态"
        assert (
            result.confidence_after >= 0 and result.confidence_after <= 1
        ), "置信度应该在 0-1 之间"
        print("✅ test_verify_claim 通过")

    async def test_generate_queries(self):
        """测试查询生成"""
        claim = Claim(
            text="全球气温在过去十年上升了1.5度",
            claim_type=ClaimType.DATA,
            confidence=0.7,
            context="",
            line_number=1,
            needs_verification=True,
        )

        queries = self.verifier._generate_queries(claim)

        assert len(queries) > 0, "应该生成至少一个查询"
        assert len(queries) <= 3, "最多生成 3 个查询"
        print("✅ test_generate_queries 通过")

    async def test_calculate_credibility(self):
        """测试可信度计算"""
        # 高可信域名
        cred1 = self.verifier._calculate_credibility("https://wikipedia.org/article")
        assert cred1 > 0.8, "Wikipedia 应该有高可信度"

        # 低可信域名
        cred2 = self.verifier._calculate_credibility("https://blogspot.com/post")
        assert cred2 < 0.5, "Blogspot 应该有低可信度"

        # 未知域名
        cred3 = self.verifier._calculate_credibility("https://example.com/page")
        assert 0.5 <= cred3 <= 0.7, "未知域名应该有中等可信度"

        print("✅ test_calculate_credibility 通过")

    async def run_all(self):
        """运行所有测试"""
        print("\n🧪 运行搜索验证器测试...\n")
        await self.test_verify_claim()
        await self.test_generate_queries()
        await self.test_calculate_credibility()
        print("\n✅ 所有搜索验证器测试通过！\n")


class TestDeepthinkV6:
    """deepthink v6.0 集成测试"""

    def __init__(self):
        self.deepthink = DeepthinkV6(use_mock_search=True)

    async def test_process(self):
        """测试完整处理流程"""
        thinking_text = """
        根据最新研究表明，全球气温在过去十年上升了1.5度。
        这意味着气候变化正在加速。
        我认为我们需要采取更积极的行动。
        数据显示，2023年的碳排放量增长了5%。
        因此，可以推断出环保政策的效果还不够明显。
        """

        report = await self.deepthink.process(thinking_text)

        assert report.total_claims > 0, "应该提取到声明"
        assert (
            report.verified_claims
            + report.partially_verified_claims
            + report.unverifiable_claims
            + report.refuted_claims
            == report.total_claims
        ), "验证结果统计应该正确"
        print("✅ test_process 通过")

    async def test_export_json(self):
        """测试 JSON 导出"""
        thinking_text = "根据研究表明，地球是圆的。"
        report = await self.deepthink.process(thinking_text)

        output_path = "test_report.json"
        self.deepthink.export_json(report, output_path)

        # 验证文件存在且有效
        assert Path(output_path).exists(), "JSON 文件应该被创建"

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "total_claims" in data, "JSON 应该包含 total_claims"

        # 清理
        Path(output_path).unlink()
        print("✅ test_export_json 通过")

    async def test_export_markdown(self):
        """测试 Markdown 导出"""
        thinking_text = "根据研究表明，地球是圆的。"
        report = await self.deepthink.process(thinking_text)

        output_path = "test_report.md"
        self.deepthink.export_markdown(report, output_path)

        # 验证文件存在
        assert Path(output_path).exists(), "Markdown 文件应该被创建"

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "deepthink v6.0" in content, "Markdown 应该包含标题"

        # 清理
        Path(output_path).unlink()
        print("✅ test_export_markdown 通过")

    async def run_all(self):
        """运行所有测试"""
        print("\n🧪 运行 deepthink v6.0 集成测试...\n")
        await self.test_process()
        await self.test_export_json()
        await self.test_export_markdown()
        print("\n✅ 所有集成测试通过！\n")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("deepthink v6.0 测试套件")
    print("=" * 60)

    # 声明提取器测试
    extractor_tests = TestClaimExtractor()
    extractor_tests.run_all()

    # 搜索验证器测试
    verifier_tests = TestSearchVerifier()
    await verifier_tests.run_all()

    # 集成测试
    integration_tests = TestDeepthinkV6()
    await integration_tests.run_all()

    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
