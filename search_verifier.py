"""
search_verifier.py - deepthink v6.0 搜索验证模块

功能：通过 web_search 验证声明的真实性
输出：验证结果，包含：
  - 验证状态（已验证/部分验证/无法验证/已反驳）
  - 支持证据
  - 反对证据
  - 置信度调整
"""

import json
import sys
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 添加父目录到路径以导入 claim_extractor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claim_extractor import Claim, ClaimType


class VerificationStatus(Enum):
    """验证状态"""
    VERIFIED = "verified"  # 已验证
    PARTIALLY_VERIFIED = "partially_verified"  # 部分验证
    UNVERIFIABLE = "unverifiable"  # 无法验证
    REFUTED = "refuted"  # 已反驳


@dataclass
class Evidence:
    """证据数据结构"""
    source: str  # 来源（URL/标题）
    snippet: str  # 摘要
    supports: bool  # 是否支持声明
    relevance: float  # 相关度 0-1
    credibility: float  # 可信度 0-1


@dataclass
class VerificationResult:
    """验证结果"""
    claim: Claim  # 原声明
    status: VerificationStatus  # 验证状态
    confidence_before: float  # 验证前置信度
    confidence_after: float  # 验证后置信度
    supporting_evidence: List[Evidence]  # 支持证据
    opposing_evidence: List[Evidence]  # 反对证据
    summary: str  # 验证总结
    search_queries: List[str]  # 使用的搜索查询


class SearchVerifier:
    """搜索验证器"""

    def __init__(self, use_mock: bool = False):
        """
        初始化验证器

        Args:
            use_mock: 是否使用模拟搜索（用于测试）
        """
        self.use_mock = use_mock
        self.max_results_per_query = 3

        # 可信域名权重
        self.credible_domains = {
            "wikipedia.org": 0.9,
            "nature.com": 0.95,
            "science.org": 0.95,
            "reuters.com": 0.85,
            "bbc.com": 0.85,
            "apnews.com": 0.85,
            "gov.cn": 0.9,
            "edu.cn": 0.85,
            "who.int": 0.95,
            "un.org": 0.9,
        }

        # 低可信域名
        self.low_credibility_domains = {
            "blogspot.com": 0.3,
            "wordpress.com": 0.4,
            "medium.com": 0.5,
            "zhihu.com": 0.6,
            "tieba.baidu.com": 0.4,
        }

    async def verify(self, claim: Claim) -> VerificationResult:
        """
        验证单个声明

        Args:
            claim: 要验证的声明

        Returns:
            验证结果
        """
        # 如果不需要验证，直接返回
        if not claim.needs_verification:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.UNVERIFIABLE,
                confidence_before=claim.confidence,
                confidence_after=claim.confidence,
                supporting_evidence=[],
                opposing_evidence=[],
                summary="声明不需要验证",
                search_queries=[],
            )

        # 生成搜索查询
        queries = self._generate_queries(claim)

        # 执行搜索
        all_results = []
        for query in queries:
            results = await self._search(query)
            all_results.extend(results)

        # 分析搜索结果
        supporting = []
        opposing = []

        for result in all_results:
            evidence = self._analyze_result(result, claim)
            if evidence.supports:
                supporting.append(evidence)
            else:
                opposing.append(evidence)

        # 计算验证状态
        status = self._determine_status(supporting, opposing)

        # 调整置信度
        confidence_after = self._adjust_confidence(
            claim.confidence, status, supporting, opposing
        )

        # 生成总结
        summary = self._generate_summary(status, supporting, opposing)

        return VerificationResult(
            claim=claim,
            status=status,
            confidence_before=claim.confidence,
            confidence_after=confidence_after,
            supporting_evidence=supporting,
            opposing_evidence=opposing,
            summary=summary,
            search_queries=queries,
        )

    def _generate_queries(self, claim: Claim) -> List[str]:
        """生成搜索查询"""
        queries = []

        # 直接查询声明文本
        queries.append(claim.text)

        # 根据声明类型添加特定查询
        if claim.claim_type == ClaimType.DATA:
            # 提取数字和关键词
            import re
            numbers = re.findall(r"\d+(?:\.\d+)?", claim.text)
            keywords = re.findall(r"[\u4e00-\u9fa5]{2,}", claim.text)
            if numbers and keywords:
                queries.append(f"{keywords[0]} {numbers[0]}")

        elif claim.claim_type == ClaimType.FACT:
            # 添加"是真的吗"或"验证"
            queries.append(f"{claim.text} 验证")
            queries.append(f"{claim.text[:50]} 真的吗")

        return queries[:3]  # 最多3个查询

    async def _search(self, query: str) -> List[Dict]:
        """
        执行搜索

        在实际实现中，这里会调用 web_search 工具
        当前使用模拟数据用于测试
        """
        if self.use_mock:
            return self._mock_search(query)

        # 真实搜索实现
        try:
            # 这里会调用 OpenClaw 的 web_search 工具
            # 由于我们在 Python 模块中，需要通过其他方式调用
            # 暂时返回模拟数据
            return self._mock_search(query)
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def _mock_search(self, query: str) -> List[Dict]:
        """模拟搜索结果（用于测试）"""
        # 这里返回一些模拟数据
        return [
            {
                "title": f"关于'{query[:20]}...'的研究报告",
                "url": "https://example.com/research",
                "snippet": f"研究表明{query[:30]}...这个说法有一定道理，但需要更多证据支持。",
            }
        ]

    def _analyze_result(self, result: Dict, claim: Claim) -> Evidence:
        """分析搜索结果是否支持声明"""
        snippet = result.get("snippet", "")
        url = result.get("url", "")

        # 计算相关度
        relevance = self._calculate_relevance(snippet, claim.text)

        # 计算可信度
        credibility = self._calculate_credibility(url)

        # 简单的支持/反对判断
        # 在实际实现中，这里会用 NLP 或 LLM 来判断
        supports = self._determine_support(snippet, claim.text)

        return Evidence(
            source=url,
            snippet=snippet,
            supports=supports,
            relevance=relevance,
            credibility=credibility,
        )

    def _calculate_relevance(self, snippet: str, claim_text: str) -> float:
        """计算相关度"""
        # 简单的关键词匹配
        claim_words = set(claim_text)
        snippet_words = set(snippet)

        if not claim_words:
            return 0.0

        overlap = len(claim_words & snippet_words)
        return min(1.0, overlap / len(claim_words) * 2)

    def _calculate_credibility(self, url: str) -> float:
        """计算来源可信度"""
        # 检查高可信域名
        for domain, cred in self.credible_domains.items():
            if domain in url:
                return cred

        # 检查低可信域名
        for domain, cred in self.low_credibility_domains.items():
            if domain in url:
                return cred

        # 默认中等可信度
        return 0.6

    def _determine_support(self, snippet: str, claim_text: str) -> bool:
        """判断是否支持声明"""
        # 简单的关键词判断
        # 在实际实现中，这里会用 NLP 或 LLM
        negative_words = ["错误", "虚假", "不实", "误导", "否认", "辟谣"]

        for word in negative_words:
            if word in snippet:
                return False

        return True  # 默认支持

    def _determine_status(
        self, supporting: List[Evidence], opposing: List[Evidence]
    ) -> VerificationStatus:
        """确定验证状态"""
        if not supporting and not opposing:
            return VerificationStatus.UNVERIFIABLE

        support_weight = sum(e.relevance * e.credibility for e in supporting)
        oppose_weight = sum(e.relevance * e.credibility for e in opposing)

        if support_weight > 0.7 and oppose_weight < 0.3:
            return VerificationStatus.VERIFIED
        elif oppose_weight > support_weight * 1.5:
            return VerificationStatus.REFUTED
        elif support_weight > 0 or oppose_weight > 0:
            return VerificationStatus.PARTIALLY_VERIFIED
        else:
            return VerificationStatus.UNVERIFIABLE

    def _adjust_confidence(
        self,
        original: float,
        status: VerificationStatus,
        supporting: List[Evidence],
        opposing: List[Evidence],
    ) -> float:
        """调整置信度"""
        if status == VerificationStatus.VERIFIED:
            return min(0.95, original * 1.2)
        elif status == VerificationStatus.REFUTED:
            return max(0.1, original * 0.3)
        elif status == VerificationStatus.PARTIALLY_VERIFIED:
            support_weight = sum(e.relevance * e.credibility for e in supporting)
            oppose_weight = sum(e.relevance * e.credibility for e in opposing)
            adjustment = 1.0 + (support_weight - oppose_weight) * 0.2
            return min(0.9, max(0.2, original * adjustment))
        else:
            return original

    def _generate_summary(
        self,
        status: VerificationStatus,
        supporting: List[Evidence],
        opposing: List[Evidence],
    ) -> str:
        """生成验证总结"""
        status_text = {
            VerificationStatus.VERIFIED: "✅ 已验证",
            VerificationStatus.PARTIALLY_VERIFIED: "⚠️ 部分验证",
            VerificationStatus.UNVERIFIABLE: "❓ 无法验证",
            VerificationStatus.REFUTED: "❌ 已反驳",
        }

        summary = f"{status_text[status]}\n"

        if supporting:
            summary += f"支持证据: {len(supporting)} 条\n"
        if opposing:
            summary += f"反对证据: {len(opposing)} 条\n"

        return summary


# 测试
if __name__ == "__main__":
    import asyncio

    async def test():
        verifier = SearchVerifier(use_mock=True)

        # 创建测试声明
        test_claim = Claim(
            text="全球气温在过去十年上升了1.5度",
            claim_type=ClaimType.DATA,
            confidence=0.7,
            context="根据最新研究表明，全球气温在过去十年上升了1.5度。",
            line_number=1,
            needs_verification=True,
        )

        result = await verifier.verify(test_claim)

        print("验证结果:")
        print(f"  声明: {result.claim.text}")
        print(f"  状态: {result.status.value}")
        print(f"  置信度: {result.confidence_before:.2f} → {result.confidence_after:.2f}")
        print(f"  总结: {result.summary}")
        print(f"  搜索查询: {result.search_queries}")

    asyncio.run(test())
