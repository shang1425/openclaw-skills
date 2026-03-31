"""
search_verifier_real.py - 真实搜索验证器

集成 OpenClaw 的 web_search 工具，实现真实的搜索验证功能
"""

import json
import sys
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claim_extractor import Claim, ClaimType
from search_verifier import (
    SearchVerifier,
    Evidence,
    VerificationResult,
    VerificationStatus,
)


class RealSearchVerifier(SearchVerifier):
    """真实搜索验证器 - 集成 OpenClaw web_search"""

    def __init__(self):
        super().__init__(use_mock=False)
        self.search_results_cache = {}

    async def _search(self, query: str) -> List[Dict]:
        """
        执行真实搜索

        这个方法需要在 OpenClaw 环境中运行，
        通过调用 web_search 工具获取搜索结果
        """
        # 检查缓存
        if query in self.search_results_cache:
            return self.search_results_cache[query]

        try:
            # 在 OpenClaw 环境中，这里会通过 RPC 调用 web_search 工具
            # 由于我们在 Python 模块中，需要通过其他方式集成
            # 这里提供一个接口，由调用者注入搜索函数

            # 暂时返回空列表，由调用者通过 set_search_function 注入
            return []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def set_search_function(self, search_fn):
        """
        设置搜索函数

        Args:
            search_fn: 异步搜索函数，签名为 async def search(query: str) -> List[Dict]
        """
        self._search_fn = search_fn

    async def _search(self, query: str) -> List[Dict]:
        """执行搜索"""
        if query in self.search_results_cache:
            return self.search_results_cache[query]

        try:
            if hasattr(self, "_search_fn"):
                results = await self._search_fn(query)
            else:
                results = []

            self.search_results_cache[query] = results
            return results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []


class DeepthinkV6WithRealSearch:
    """deepthink v6.0 - 真实搜索版本"""

    def __init__(self, search_function=None):
        """
        初始化

        Args:
            search_function: 搜索函数，签名为 async def search(query: str) -> List[Dict]
        """
        from claim_extractor import ClaimExtractor

        self.extractor = ClaimExtractor()
        self.verifier = RealSearchVerifier()

        if search_function:
            self.verifier.set_search_function(search_function)

    async def process(self, thinking_text: str):
        """处理思考过程"""
        # 提取声明
        claims = self.extractor.extract(thinking_text)

        # 验证声明
        verification_results = []
        for claim in claims:
            result = await self.verifier.verify(claim)
            verification_results.append(result)

        return {
            "claims": claims,
            "verification_results": verification_results,
        }


# 使用示例
async def example_with_openclaw_search():
    """
    在 OpenClaw 环境中使用的示例

    需要在 OpenClaw 的 Python 环境中运行，
    并通过 web_search 工具注入搜索函数
    """

    # 这是一个示例，展示如何在 OpenClaw 中集成
    # 实际使用时需要通过 OpenClaw 的工具系统调用

    async def mock_search(query: str) -> List[Dict]:
        """模拟搜索函数"""
        return [
            {
                "title": f"关于 {query} 的搜索结果",
                "url": "https://example.com",
                "snippet": f"这是关于 {query} 的搜索结果摘要",
            }
        ]

    deepthink = DeepthinkV6WithRealSearch(search_function=mock_search)

    test_thinking = """
    根据最新研究表明，全球气温在过去十年上升了1.5度。
    """

    result = await deepthink.process(test_thinking)
    print(f"提取了 {len(result['claims'])} 个声明")
    print(f"验证了 {len(result['verification_results'])} 个声明")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_with_openclaw_search())
