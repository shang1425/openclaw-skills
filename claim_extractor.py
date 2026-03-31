"""
claim_extractor.py - deepthink v6.0 声明提取模块

功能：从思考过程中自动提取可验证的声明（facts/claims）
输出：结构化的声明列表，包含：
  - 声明文本
  - 声明类型（事实/数据/观点/推论）
  - 置信度
  - 来源上下文
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ClaimType(Enum):
    """声明类型"""
    FACT = "fact"  # 客观事实
    DATA = "data"  # 数据/统计
    OPINION = "opinion"  # 观点/判断
    INFERENCE = "inference"  # 推论/结论


@dataclass
class Claim:
    """声明数据结构"""
    text: str  # 声明文本
    claim_type: ClaimType  # 声明类型
    confidence: float  # 置信度 0-1
    context: str  # 来源上下文
    line_number: int  # 在原文中的行号
    needs_verification: bool = True  # 是否需要验证


class ClaimExtractor:
    """声明提取器"""

    def __init__(self):
        # 事实标记词
        self.fact_markers = [
            r"根据.*?(?:显示|表明|证实|说明)",
            r"(?:已知|已证实|事实上|实际上)",
            r"(?:研究|调查|数据)(?:表明|显示|证实)",
        ]

        # 数据标记词
        self.data_markers = [
            r"\d+(?:%|个|人|次|倍|年|月|日)",
            r"(?:约|大约|超过|超|至少|最多)\s*\d+",
            r"(?:增长|下降|上升|下跌)\s*\d+",
        ]

        # 观点标记词
        self.opinion_markers = [
            r"(?:我认为|我觉得|我的看法|个人认为|似乎|可能|也许)",
            r"(?:应该|不应该|值得|不值得)",
            r"(?:好|坏|优|劣|强|弱)(?:的|点)",
        ]

        # 推论标记词
        self.inference_markers = [
            r"(?:因此|所以|由此|可以推断|可以得出)",
            r"(?:这意味着|这表明|这说明)",
            r"(?:结论是|总结为|可以说)",
        ]

        # 需要验证的关键词
        self.verification_keywords = [
            "声称", "据说", "报道", "宣称", "表示",
            "数据", "统计", "研究", "调查", "发现",
            "发生", "发生了", "出现", "出现了",
        ]

    def extract(self, text: str) -> List[Claim]:
        """
        从文本中提取声明

        Args:
            text: 输入文本（通常是 deepthink 的思考过程）

        Returns:
            声明列表
        """
        claims = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # 检测声明类型
            claim_type = self._detect_type(line)
            if claim_type is None:
                continue

            # 提取声明
            extracted_claims = self._extract_from_line(line, claim_type, line_num)
            claims.extend(extracted_claims)

        return claims

    def _detect_type(self, line: str) -> ClaimType:
        """检测行的声明类型"""
        line_lower = line.lower()

        # 按优先级检测
        if self._match_patterns(line_lower, self.inference_markers):
            return ClaimType.INFERENCE
        elif self._match_patterns(line_lower, self.opinion_markers):
            return ClaimType.OPINION
        elif self._match_patterns(line_lower, self.data_markers):
            return ClaimType.DATA
        elif self._match_patterns(line_lower, self.fact_markers):
            return ClaimType.FACT
        elif any(kw in line_lower for kw in self.verification_keywords):
            return ClaimType.FACT

        # 如果包含确定性词汇，也认为是事实
        certainty_words = ["确实", "肯定", "一定", "必然", "显然", "是"]
        if any(word in line_lower for word in certainty_words):
            return ClaimType.FACT

        return None

    def _match_patterns(self, text: str, patterns: List[str]) -> bool:
        """检查文本是否匹配任何模式"""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def _extract_from_line(
        self, line: str, claim_type: ClaimType, line_num: int
    ) -> List[Claim]:
        """从一行中提取声明"""
        claims = []

        # 简单的句子分割（按句号、感叹号、问号）
        sentences = re.split(r"[。！？\.\!\?]", line)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            # 计算置信度
            confidence = self._calculate_confidence(sentence, claim_type)

            # 判断是否需要验证
            needs_verification = self._needs_verification(sentence, claim_type)

            claim = Claim(
                text=sentence,
                claim_type=claim_type,
                confidence=confidence,
                context=line,
                line_number=line_num,
                needs_verification=needs_verification,
            )
            claims.append(claim)

        return claims

    def _calculate_confidence(self, text: str, claim_type: ClaimType) -> float:
        """计算声明的置信度"""
        confidence = 0.5  # 基础置信度

        # 根据类型调整
        if claim_type == ClaimType.FACT:
            confidence = 0.7
        elif claim_type == ClaimType.DATA:
            confidence = 0.8  # 数据通常更可信
        elif claim_type == ClaimType.OPINION:
            confidence = 0.4
        elif claim_type == ClaimType.INFERENCE:
            confidence = 0.6

        # 根据修饰词调整
        uncertainty_words = ["可能", "也许", "似乎", "大概", "据说"]
        for word in uncertainty_words:
            if word in text:
                confidence *= 0.8
                break

        certainty_words = ["确实", "肯定", "一定", "必然", "显然"]
        for word in certainty_words:
            if word in text:
                confidence = min(0.95, confidence * 1.3)
                break

        return min(1.0, max(0.0, confidence))

    def _needs_verification(self, text: str, claim_type: ClaimType) -> bool:
        """判断声明是否需要验证"""
        # 观点不需要验证
        if claim_type == ClaimType.OPINION:
            return False

        # 包含数据的声明需要验证
        if re.search(r"\d+", text):
            return True

        # 包含验证关键词的需要验证
        for kw in self.verification_keywords:
            if kw in text:
                return True

        return claim_type in [ClaimType.FACT, ClaimType.INFERENCE]

    def filter_by_confidence(
        self, claims: List[Claim], min_confidence: float = 0.5
    ) -> List[Claim]:
        """按置信度过滤声明"""
        return [c for c in claims if c.confidence >= min_confidence]

    def filter_by_type(self, claims: List[Claim], claim_type: ClaimType) -> List[Claim]:
        """按类型过滤声明"""
        return [c for c in claims if c.claim_type == claim_type]

    def get_verification_queue(self, claims: List[Claim]) -> List[Claim]:
        """获取需要验证的声明队列（按优先级排序）"""
        # 只返回需要验证的声明
        verification_claims = [c for c in claims if c.needs_verification]

        # 按优先级排序：低置信度 > 高置信度
        verification_claims.sort(key=lambda c: c.confidence)

        return verification_claims


# 测试
if __name__ == "__main__":
    extractor = ClaimExtractor()

    test_text = """
    根据最新研究表明，全球气温在过去十年上升了1.5度。
    这意味着气候变化正在加速。
    我认为我们需要采取更积极的行动。
    数据显示，2023年的碳排放量增长了5%。
    因此，可以推断出环保政策的效果还不够明显。
    """

    claims = extractor.extract(test_text)
    print(f"提取了 {len(claims)} 个声明：\n")

    for i, claim in enumerate(claims, 1):
        print(f"{i}. [{claim.claim_type.value}] {claim.text}")
        print(f"   置信度: {claim.confidence:.2f}")
        print(f"   需要验证: {claim.needs_verification}")
        print()

    # 获取需要验证的声明
    verification_queue = extractor.get_verification_queue(claims)
    print(f"\n需要验证的声明队列（{len(verification_queue)} 个）：")
    for claim in verification_queue:
        print(f"  - {claim.text}")
