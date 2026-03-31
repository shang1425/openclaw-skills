"""
deepthink_v6.py - deepthink v6.0 主框架

集成声明提取和搜索验证，实现完整的结构化深度思考流程：
1. 输入思考过程
2. 提取声明
3. 搜索验证
4. 输出验证报告
"""

import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from claim_extractor import ClaimExtractor, Claim, ClaimType
from search_verifier import SearchVerifier, VerificationResult, VerificationStatus


@dataclass
class DeepthinkReport:
    """deepthink 报告"""
    timestamp: str
    thinking_text: str
    total_claims: int
    verified_claims: int
    partially_verified_claims: int
    unverifiable_claims: int
    refuted_claims: int
    claims: List[Dict]
    verification_results: List[Dict]
    summary: str


class DeepthinkV6:
    """deepthink v6.0 主框架"""

    def __init__(self, use_mock_search: bool = False):
        """
        初始化 deepthink v6.0

        Args:
            use_mock_search: 是否使用模拟搜索（用于测试）
        """
        self.extractor = ClaimExtractor()
        self.verifier = SearchVerifier(use_mock=use_mock_search)

    async def process(self, thinking_text: str) -> DeepthinkReport:
        """
        处理思考过程

        Args:
            thinking_text: 思考过程文本

        Returns:
            deepthink 报告
        """
        # 第一步：提取声明
        claims = self.extractor.extract(thinking_text)

        # 第二步：验证声明
        verification_results = []
        for claim in claims:
            result = await self.verifier.verify(claim)
            verification_results.append(result)

        # 第三步：统计结果
        stats = self._calculate_stats(verification_results)

        # 第四步：生成报告
        report = DeepthinkReport(
            timestamp=datetime.now().isoformat(),
            thinking_text=thinking_text,
            total_claims=len(claims),
            verified_claims=stats["verified"],
            partially_verified_claims=stats["partially_verified"],
            unverifiable_claims=stats["unverifiable"],
            refuted_claims=stats["refuted"],
            claims=[self._claim_to_dict(c) for c in claims],
            verification_results=[
                self._result_to_dict(r) for r in verification_results
            ],
            summary=self._generate_summary(stats, len(claims)),
        )

        return report

    def _calculate_stats(self, results: List[VerificationResult]) -> Dict[str, int]:
        """计算统计数据"""
        stats = {
            "verified": 0,
            "partially_verified": 0,
            "unverifiable": 0,
            "refuted": 0,
        }

        for result in results:
            if result.status == VerificationStatus.VERIFIED:
                stats["verified"] += 1
            elif result.status == VerificationStatus.PARTIALLY_VERIFIED:
                stats["partially_verified"] += 1
            elif result.status == VerificationStatus.UNVERIFIABLE:
                stats["unverifiable"] += 1
            elif result.status == VerificationStatus.REFUTED:
                stats["refuted"] += 1

        return stats

    def _claim_to_dict(self, claim: Claim) -> Dict:
        """将声明转换为字典"""
        return {
            "text": claim.text,
            "type": claim.claim_type.value,
            "confidence": claim.confidence,
            "context": claim.context,
            "line_number": claim.line_number,
            "needs_verification": claim.needs_verification,
        }

    def _result_to_dict(self, result: VerificationResult) -> Dict:
        """将验证结果转换为字典"""
        return {
            "claim": result.claim.text,
            "status": result.status.value,
            "confidence_before": result.confidence_before,
            "confidence_after": result.confidence_after,
            "supporting_evidence": [
                {
                    "source": e.source,
                    "snippet": e.snippet,
                    "relevance": e.relevance,
                    "credibility": e.credibility,
                }
                for e in result.supporting_evidence
            ],
            "opposing_evidence": [
                {
                    "source": e.source,
                    "snippet": e.snippet,
                    "relevance": e.relevance,
                    "credibility": e.credibility,
                }
                for e in result.opposing_evidence
            ],
            "summary": result.summary,
            "search_queries": result.search_queries,
        }

    def _generate_summary(self, stats: Dict[str, int], total: int) -> str:
        """生成报告总结"""
        if total == 0:
            return "未提取到任何声明"

        verified_rate = (stats["verified"] / total * 100) if total > 0 else 0
        refuted_rate = (stats["refuted"] / total * 100) if total > 0 else 0

        summary = f"""
deepthink v6.0 验证报告总结
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 统计数据
  • 总声明数: {total}
  • ✅ 已验证: {stats['verified']} ({verified_rate:.1f}%)
  • ⚠️ 部分验证: {stats['partially_verified']} ({stats['partially_verified']/total*100:.1f}%)
  • ❓ 无法验证: {stats['unverifiable']} ({stats['unverifiable']/total*100:.1f}%)
  • ❌ 已反驳: {stats['refuted']} ({refuted_rate:.1f}%)

🎯 可信度评估
  • 高可信度 (已验证): {verified_rate:.1f}%
  • 低可信度 (已反驳): {refuted_rate:.1f}%
  • 需要进一步审查: {(stats['partially_verified']+stats['unverifiable'])/total*100:.1f}%

💡 建议
  • 优先审查已反驳的声明
  • 对部分验证的声明进行深入研究
  • 对无法验证的声明补充更多信息来源
"""
        return summary

    def export_json(self, report: DeepthinkReport, filepath: str) -> None:
        """导出 JSON 报告"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    def export_markdown(self, report: DeepthinkReport, filepath: str) -> None:
        """导出 Markdown 报告"""
        md_content = f"""# deepthink v6.0 验证报告

**生成时间**: {report.timestamp}

## 📊 统计概览

| 指标 | 数量 | 比例 |
|------|------|------|
| 总声明数 | {report.total_claims} | 100% |
| ✅ 已验证 | {report.verified_claims} | {report.verified_claims/report.total_claims*100:.1f}% |
| ⚠️ 部分验证 | {report.partially_verified_claims} | {report.partially_verified_claims/report.total_claims*100:.1f}% |
| ❓ 无法验证 | {report.unverifiable_claims} | {report.unverifiable_claims/report.total_claims*100:.1f}% |
| ❌ 已反驳 | {report.refuted_claims} | {report.refuted_claims/report.total_claims*100:.1f}% |

## 🔍 详细验证结果

"""
        for i, result in enumerate(report.verification_results, 1):
            md_content += f"""### {i}. {result['claim']}

**验证状态**: {result['status']}  
**置信度变化**: {result['confidence_before']:.2f} → {result['confidence_after']:.2f}  
**搜索查询**: {', '.join(result['search_queries'])}

"""
            if result["supporting_evidence"]:
                md_content += "**支持证据**:\n"
                for evidence in result["supporting_evidence"]:
                    md_content += f"- [{evidence['source']}] {evidence['snippet']}\n"
                md_content += "\n"

            if result["opposing_evidence"]:
                md_content += "**反对证据**:\n"
                for evidence in result["opposing_evidence"]:
                    md_content += f"- [{evidence['source']}] {evidence['snippet']}\n"
                md_content += "\n"

        md_content += f"""
## 📝 原始思考过程

```
{report.thinking_text}
```

## 💡 总结

{report.summary}
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)


# 测试
async def test():
    """测试 deepthink v6.0"""
    deepthink = DeepthinkV6(use_mock_search=True)

    test_thinking = """
    根据最新研究表明，全球气温在过去十年上升了1.5度。
    这意味着气候变化正在加速。
    我认为我们需要采取更积极的行动。
    数据显示，2023年的碳排放量增长了5%。
    因此，可以推断出环保政策的效果还不够明显。
    """

    print("🚀 开始处理思考过程...\n")
    report = await deepthink.process(test_thinking)

    print(report.summary)

    # 导出报告
    deepthink.export_json(report, "deepthink_report.json")
    deepthink.export_markdown(report, "deepthink_report.md")

    print("\n✅ 报告已导出:")
    print("  - deepthink_report.json")
    print("  - deepthink_report.md")


if __name__ == "__main__":
    asyncio.run(test())
