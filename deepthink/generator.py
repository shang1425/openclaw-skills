"""
Generator — 生成器模块
按 sprint_contract 产出思考链，标记置信度和自我质疑

新增 v3.0：
- 真实 LLM 推理（通过 llm_client）
- Self-Reflection Loop（反思链）：生成 → 反思 → 改进 → 再反思
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum
import json
import re

if TYPE_CHECKING:
    from llm_client import LLMClient


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
    note: str = ""  # 额外说明


@dataclass
class SelfCritique:
    """自我质疑"""
    critique_points: List[str]  # 质疑点列表
    missing_perspectives: List[str]  # 遗漏的视角
    knowledge_gaps: List[str]  # 知识缺口


@dataclass
class GeneratorResult:
    """生成结果"""
    thought_chain: List[ThoughtStep]
    self_critique: SelfCritique
    final_conclusion: str
    confidence_summary: str  # 总体置信度评估


# ========== 置信度判断逻辑 ==========

def assess_confidence(
    thinking: str,
    evidence: str,
    assumptions: List[str],
) -> str:
    """
    评估置信度
    
    启发式规则：
    - 有充分证据 + 假设少 → A/B
    - 证据一般 + 假设中等 → B/C
    - 证据不足 + 假设多 → C/D
    - 无证据 + 假设多 → D/F
    """
    
    # 计算证据充分度
    evidence_score = 0
    if evidence and len(evidence) > 100:
        evidence_score = 3
    elif evidence and len(evidence) > 50:
        evidence_score = 2
    elif evidence:
        evidence_score = 1
    else:
        evidence_score = 0
    
    # 计算假设数量
    assumption_count = len(assumptions)
    
    # 计算思考深度
    thinking_depth = len(thinking) // 20  # 每20字算一个深度单位
    
    # 综合评分
    total_score = evidence_score * 2 + (3 - min(assumption_count, 3)) + min(thinking_depth, 2)
    
    # 映射到置信度
    if total_score >= 8:
        return "A"
    elif total_score >= 6:
        return "B"
    elif total_score >= 4:
        return "C"
    elif total_score >= 2:
        return "D"
    else:
        return "F"


# ========== 自我质疑逻辑 ==========

def generate_self_critique(thought_chain: List[ThoughtStep]) -> SelfCritique:
    """
    生成自我质疑
    """
    critique_points = []
    missing_perspectives = []
    knowledge_gaps = []
    
    # 1. 检查低置信度步骤
    for step in thought_chain:
        if step.confidence in ["D", "F"]:
            critique_points.append(f"第{step.step}步置信度很低（{step.confidence}级），可能需要更多信息")
    
    # 2. 检查假设数量
    total_assumptions = sum(len(step.assumptions) for step in thought_chain)
    if total_assumptions > len(thought_chain) * 2:
        critique_points.append(f"假设过多（{total_assumptions}个），可能过度依赖假设")
    
    # 3. 检查是否有相反的视角
    has_devil_advocate = any("反面" in step.thinking or "但是" in step.thinking or "然而" in step.thinking 
                             for step in thought_chain)
    if not has_devil_advocate:
        missing_perspectives.append("缺少反面视角（魔鬼代言人）")
    
    # 4. 检查是否考虑了长期影响
    has_long_term = any("长期" in step.thinking or "未来" in step.thinking or "趋势" in step.thinking 
                        for step in thought_chain)
    if not has_long_term:
        missing_perspectives.append("缺少长期视角")
    
    # 5. 检查是否考虑了实操性
    has_practical = any("实施" in step.thinking or "执行" in step.thinking or "可行" in step.thinking 
                        for step in thought_chain)
    if not has_practical:
        missing_perspectives.append("缺少实操性考虑")
    
    # 6. 识别知识缺口
    for step in thought_chain:
        if "不知道" in step.thinking or "缺乏" in step.thinking or "无法确定" in step.thinking:
            knowledge_gaps.append(f"第{step.step}步：{step.thinking[:50]}")
    
    return SelfCritique(
        critique_points=critique_points,
        missing_perspectives=missing_perspectives,
        knowledge_gaps=knowledge_gaps,
    )


# ========== AI 驱动的生成（新增）============

GENERATOR_SYSTEM = """你是一个深度思考生成器。给定子问题，用XML标签直接输出结构化内容（不需要YAML格式）：

<result>
<thought_chain>
<step index="1">
<thinking>第一步的推理过程，中文，50-100字</thinking>
<confidence>A</confidence>
<evidence>证据</evidence>
<assumptions>假设1;假设2</assumptions>
<note>备注</note>
</step>
</thought_chain>
<self_critique>
<critique_points>质疑点1;质疑点2</critique_points>
<missing_perspectives>遗漏视角1;遗漏视角2</missing_perspectives>
<knowledge_gaps>知识缺口1;知识缺口2</knowledge_gaps>
</self_critique>
<final_conclusion>最终结论，中文，80字以内</final_conclusion>
<confidence_summary>一句话总结</confidence_summary>
</result>

置信度：A=高度确信 B=中等确信 C=低确信 D=很低 F=无法确信。
只输出XML标签内容，不要其他文字。
"""


REFLECTION_SYSTEM = """你是一个批判性思维专家。分析以下思考链，输出YAML：
```yaml
issues:
  - 逻辑漏洞描述
missing_angles:
  - 遗漏视角
needs_regeneration: true
improvement_hints:
  - 改进建议
```

needs_regeneration: true=需要重新生成, false=已足够好。只输出YAML。
"""


def generate_with_llm(
    subproblems: List[dict],
    sprint_contract: dict,
    context: str = "",
    client: "LLMClient" = None,
    reflection_loops: int = 2,
) -> "GeneratorResult":
    """
    使用 LLM 进行真实思考生成，支持 self-reflection loop

    Args:
        subproblems: 子问题列表
        sprint_contract: 短跑合约
        context: 额外上下文
        client: LLM 客户端
        reflection_loops: 反思轮数（默认2轮）

    Returns:
        GeneratorResult: 生成结果
    """
    # 构建提示
    subproblems_text = "\n".join(
        f"[{sp.get('id', f'sp{i}')}] {sp.get('question', sp.get('title', ''))} "
        f"({sp.get('assigned_role', '')}, 不确定性: {sp.get('uncertainty', 'medium')})"
        for i, sp in enumerate(subproblems)
    )

    context_section = f"\n\n额外上下文：\n{context}" if context else ""

    first_prompt = f"""{sprint_contract.get('goal', '')}

子问题：
{subproblems_text}
{context_section}

请对每个子问题进行深度推理，输出 JSON。"""

    # 第1轮：生成初始思考链
    print(f"\n  [Generator] 第 1 轮生成中...")
    raw1 = client.chat_once(
        system=GENERATOR_SYSTEM,
        prompt=first_prompt,
        temperature=0.6,
        max_tokens=1500,
        timeout=180,
    )
    data1 = _extract_gen_yaml_or_json(raw1)

    thought_chain = [
        ThoughtStep(
            step=ts["step"],
            thinking=ts["thinking"],
            confidence=ts.get("confidence", "C"),
            evidence=ts.get("evidence", ""),
            assumptions=ts.get("assumptions", []),
            note=ts.get("note", ""),
        )
        for ts in data1.get("thought_chain", [])
    ]

    # Self-Reflection Loop
    for loop in range(2, reflection_loops + 1):
        print(f"\n  [Generator] 第 {loop} 轮反思中...")

        # 格式化当前思考链
        chain_text = "\n".join(
            f"步骤{ts.step} [{ts.confidence}] {ts.thinking}\n  证据：{ts.evidence}\n  假设：{', '.join(ts.assumptions)}"
            for ts in thought_chain
        )

        reflect_prompt = f"当前思考链：\n{chain_text}\n\n请指出问题并给出改进建议，输出 JSON："
        raw_reflect = client.chat_once(
            system=REFLECTION_SYSTEM,
            prompt=reflect_prompt,
            temperature=0.3,
            max_tokens=1500,
            timeout=180,
        )

        reflect_data = _extract_reflect_json(raw_reflect)
        needs_regen = reflect_data.get("needs_regeneration", False)

        if needs_regen:
            print(f"  ⚠️ 需要改进：{', '.join(reflect_data.get('issues', [])[:2])}")
            # 第2+轮：基于反思改进生成
            improvement = "\n".join(reflect_data.get("improvement_hints", []))
            improved_prompt = f"""基于以下反思意见，改进你的思考：

反思问题：{', '.join(reflect_data.get('issues', []))}
遗漏视角：{', '.join(reflect_data.get('missing_angles', []))}
改进提示：{improvement}

原思考链：
{chain_text}

请输出改进后的完整思考链（JSON）：
"""
            raw2 = client.chat_once(
                system=GENERATOR_SYSTEM,
                prompt=improved_prompt,
                temperature=0.5,
                max_tokens=1500,
                timeout=180,
            )
            data2 = _extract_gen_yaml_or_json(raw2)
            thought_chain = [
                ThoughtStep(
                    step=ts["step"],
                    thinking=ts["thinking"],
                    confidence=ts.get("confidence", "C"),
                    evidence=ts.get("evidence", ""),
                    assumptions=ts.get("assumptions", []),
                    note=ts.get("note", ""),
                )
                for ts in data2.get("thought_chain", [])
            ]
        else:
            print(f"  ✅ 无需改进，继续")
            break

    # 生成自我质疑
    self_critique_data = data1.get("self_critique", {})
    self_critique = SelfCritique(
        critique_points=self_critique_data.get("critique_points", []),
        missing_perspectives=self_critique_data.get("missing_perspectives", []),
        knowledge_gaps=self_critique_data.get("knowledge_gaps", []),
    )

    # 置信度统计
    confidence_dist = {}
    for step in thought_chain:
        confidence_dist[step.confidence] = confidence_dist.get(step.confidence, 0) + 1

    confidence_summary = "置信度分布：" + "，".join(
        f"{level}级{count}步" for level, count in sorted(confidence_dist.items())
    )

    final_conclusion = data1.get(
        "final_conclusion",
        "\n".join(f"**{sp.get('question','')}**\n思考完成" for sp in subproblems)
    )

    return GeneratorResult(
        thought_chain=thought_chain,
        self_critique=self_critique,
        final_conclusion=final_conclusion,
        confidence_summary=confidence_summary,
    )


def _strip_thinking(text: str) -> str:
    """去掉 <think> 思考标签"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _extract_xml(text: str) -> dict:
    """从 XML 标签中提取结构化内容"""
    text = _strip_thinking(text)

    def get(tag: str) -> str:
        # 匹配 <tag>...</tag>（支持跨行）
        m = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    def get_list(parent_tag: str, item_tag: str) -> list:
        m = re.search(rf"<{parent_tag}>\s*(.*?)\s*</{parent_tag}>", text, re.DOTALL)
        if not m:
            return []
        content = m.group(1)
        items = re.findall(rf"<{item_tag}[^>]*>(.*?)</{item_tag}>", content, re.DOTALL)
        return [it.strip() for it in items if it.strip()]

    def get_steps(parent_tag: str) -> list:
        m = re.search(rf"<{parent_tag}>\s*(.*?)\s*</{parent_tag}>", text, re.DOTALL)
        if not m:
            return []
        content = m.group(1)
        # 匹配 <step>...</step>（支持 index 属性）
        step_blocks = re.findall(r"<step\b[^>]*>(.*?)</step>", content, re.DOTALL)
        result = []
        for i, step_xml in enumerate(step_blocks):
            step = {
                "step": i + 1,
                "thinking": get_in_step(step_xml, "thinking"),
                "confidence": get_in_step(step_xml, "confidence") or "C",
                "evidence": get_in_step(step_xml, "evidence"),
                "assumptions": _split_list(get_in_step(step_xml, "assumptions")),
                "note": get_in_step(step_xml, "note"),
            }
            result.append(step)
        return result

    def get_in_step(xml: str, tag: str) -> str:
        m = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", xml, re.DOTALL)
        return m.group(1).strip() if m else ""

    def _split_list(text: str) -> list:
        if not text:
            return []
        return [s.strip() for s in re.split(r"[;；,，\n]", text) if s.strip()]

    # 解析 critique 部分
    critique_m = re.search(r"<self_critique>\s*(.*?)\s*</self_critique>", text, re.DOTALL)
    if critique_m:
        critique_text = critique_m.group(1)
        critique_points = _split_list(get_in_step(critique_text, "critique_points"))
        missing = _split_list(get_in_step(critique_text, "missing_perspectives"))
        gaps = _split_list(get_in_step(critique_text, "knowledge_gaps"))
    else:
        critique_points, missing, gaps = [], [], []

    result = {
        "thought_chain": get_steps("thought_chain"),
        "self_critique": {
            "critique_points": critique_points,
            "missing_perspectives": missing,
            "knowledge_gaps": gaps,
        },
        "final_conclusion": get("final_conclusion") or get("conclusion") or "",
        "confidence_summary": get("confidence_summary") or "",
    }

    # 如果 XML 解析失败，回退：尝试 YAML/JSON
    if not result["thought_chain"]:
        result = _extract_yaml_fallback(text)

    return result


def _extract_yaml_fallback(text: str) -> dict:
    """YAML/JSON 回退解析器"""
    # 去掉 markdown
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        text = text.rstrip("`").rstrip()

    # 试 JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return {"thought_chain": [], "self_critique": {}, "final_conclusion": "", "confidence_summary": ""}


def _strip_markdown(text: str) -> str:
    """去掉 markdown 代码块"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        text = text.rstrip("`").rstrip()
    return text


def _parse_yaml(text: str) -> dict:
    """
    轻量 YAML 解析器（支持子集）
    - key: value
    - key: |  多行
    - - item（列表）
    - 嵌套缩进
    """
    lines = text.split("\n")
    result = {}
    stack = [(None, result, 0)]  # (parent_key, dict_or_list, indent)

    i = 0
    while i < len(lines):
        line = lines[i]

        # 计算缩进
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        is_list = stripped.startswith("- ")
        if is_list:
            key_indent = indent
            item_val = stripped[2:].strip()
        else:
            # 找冒号位置
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            rest = stripped[colon_idx + 1:].strip()
            key_indent = indent

        # 弹出栈直到栈顶缩进小于当前
        while len(stack) > 1 and stack[-1][2] >= key_indent:
            stack.pop()

        parent_dict_or_list = stack[-1][1]

        if is_list:
            if isinstance(parent_dict_or_list, dict):
                # 列表项作为父dict的最后一个key的值
                if not parent_dict_or_list:
                    pass  # 空dict，跳过
                else:
                    last_key = list(parent_dict_or_list.keys())[-1]
                    val = parent_dict_or_list[last_key]
                    if isinstance(val, list):
                        # 解析列表项值
                        parsed_val = _parse_yaml_value(item_val, lines, i + 1)
                        val.append(parsed_val)
                        if isinstance(parsed_val, dict):
                            stack.append((last_key, parsed_val, key_indent + 2))
            elif isinstance(parent_dict_or_list, list):
                parsed_val = _parse_yaml_value(item_val, lines, i + 1)
                parent_dict_or_list.append(parsed_val)
                if isinstance(parsed_val, dict):
                    stack.append((None, parsed_val, key_indent + 2))
        else:
            # 解析值
            if "|" in rest or rest == "":
                # 多行块
                val, consumed = _parse_yaml_block(rest, lines, i + 1)
                i += consumed
                parent_dict_or_list[key] = val
            else:
                parsed = _parse_yaml_scalar(rest)
                parent_dict_or_list[key] = parsed

        i += 1

    return result


def _parse_yaml_block(rest: str, lines: list, start: int):
    """解析 YAML 块标量（|格式）"""
    if rest == "|" or rest == "|-":
        # 等待后续缩进行
        block_lines = []
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                break
            # 块内容：去掉缩进
            content = line.strip()
            block_lines.append(content)
            i += 1
        return "\n".join(block_lines), i - start
    elif rest.startswith("|"):
        #  inline after |
        first = rest[1:].strip()
        return first, 0
    else:
        return _parse_yaml_scalar(rest), 0


def _parse_yaml_scalar(val: str) -> Any:
    """解析标量值"""
    val = val.strip()
    if not val:
        return ""
    # 布尔/数字
    if val in ("true", "True", "yes", "yes"):
        return True
    if val in ("false", "False", "no", "no"):
        return False
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def _parse_yaml_value(item_val: str, lines: list, next_idx: int) -> Any:
    """解析列表项的值"""
    # 如果后续行是缩进的dict，继续解析
    if next_idx < len(lines):
        next_line = lines[next_idx]
        if next_line.strip().startswith("-"):
            # 还是列表项
            return item_val
        elif next_line.strip() and not next_line.strip().startswith("#"):
            # 检查是否是内联dict
            if any(k in next_line for k in [": "]):
                return item_val  # 标量
        if item_val and item_val.strip():
            return item_val.strip()
    return item_val.strip() if item_val else ""


def _extract_gen_yaml_or_json(raw: str) -> dict:
    """智能提取生成器输出（优先XML，回退YAML/JSON）"""
    # 先去掉 <think> 标签
    text = _strip_thinking(raw)
    # 再去掉 markdown
    text = _strip_markdown(text)

    # 优先：XML 解析（modelroute 模型的输出格式）
    try:
        data = _extract_xml(text)
        if data.get("thought_chain"):
            return data
    except Exception:
        pass

    # 回退：JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # 回退：YAML
    try:
        data = _parse_yaml(text)
        if data.get("thought_chain"):
            return {
                "thought_chain": data.get("thought_chain", []),
                "self_critique": data.get("self_critique", {}),
                "final_conclusion": data.get("final_conclusion", raw[:200]),
                "confidence_summary": data.get("confidence_summary", ""),
            }
    except Exception:
        pass

    # 最后的回退：把原始文本塞进 final_conclusion
    return {
        "thought_chain": [],
        "self_critique": {},
        "final_conclusion": raw[:500],
        "confidence_summary": "",
    }


def _extract_reflect_json(raw: str) -> dict:
    """提取反思器的 JSON 输出"""
    text = _strip_markdown(raw)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {"needs_regeneration": False, "issues": [], "missing_angles": [], "improvement_hints": []}


# ========== 核心函数（原有，保持兼容）==========

def generate(
    subproblems: List[dict],
    sprint_contract: dict,
    context: str = "",
    max_iterations: int = 1,
    client: "LLMClient" = None,
    reflection_loops: int = 2,
) -> GeneratorResult:
    """
    生成器主函数
    
    Args:
        subproblems: 子问题列表
        sprint_contract: 短跑合约
        context: 额外上下文
        max_iterations: 最大迭代次数
    
    Returns:
        GeneratorResult: 生成结果
    
    Notes:
        - 若传入 client，则使用 LLM 真实生成 + self-reflection loop
        - 若不传 client，回退到启发式模拟（兼容旧代码）
    """
    # 有 LLM 客户端时使用 AI 生成 + 反思链
    if client is not None:
        return generate_with_llm(
            subproblems,
            sprint_contract,
            context,
            client,
            reflection_loops=reflection_loops,
        )
    
    # 回退：启发式模拟生成（原有逻辑）
    thought_chain = []
    
    # 1. 为每个子问题生成思考步骤
    for i, sp in enumerate(subproblems):
        step = ThoughtStep(
            step=i + 1,
            thinking=f"分析：{sp.get('question', '')}",
            confidence="C",  # 默认中等置信度
            evidence=f"基于{sp.get('assigned_role', '分析')}的视角",
            assumptions=["信息准确", "逻辑合理"],
            note=f"不确定性：{sp.get('uncertainty', 'medium')}",
        )
        
        # 根据不确定性调整置信度
        if sp.get('uncertainty') == 'high':
            step.confidence = "D"
        elif sp.get('uncertainty') == 'low':
            step.confidence = "B"
        
        thought_chain.append(step)
    
    # 2. 生成自我质疑
    self_critique = generate_self_critique(thought_chain)
    
    # 3. 生成最终结论
    final_conclusion = f"""
基于以上分析，关于「{sprint_contract.get('goal', '')}」的结论：

**关键发现：**
{chr(10).join(f"- {sp.get('question', '')}" for sp in subproblems[:3])}

**置信度评估：**
- 高度确信（A级）：{sum(1 for s in thought_chain if s.confidence == 'A')}步
- 中等确信（B级）：{sum(1 for s in thought_chain if s.confidence == 'B')}步
- 低度确信（C级）：{sum(1 for s in thought_chain if s.confidence == 'C')}步
- 很低确信（D级）：{sum(1 for s in thought_chain if s.confidence == 'D')}步
- 无法确信（F级）：{sum(1 for s in thought_chain if s.confidence == 'F')}步

**不确定性标记：**
{chr(10).join(f"- {gap}" for gap in self_critique.knowledge_gaps[:3]) if self_critique.knowledge_gaps else "- 整体不确定性在可控范围内"}

**建议：**
{sprint_contract.get('quality_bar', '按质量标准执行')}
"""
    
    # 4. 生成置信度总结
    confidence_dist = {}
    for step in thought_chain:
        confidence_dist[step.confidence] = confidence_dist.get(step.confidence, 0) + 1
    
    confidence_summary = "置信度分布：" + "，".join(
        f"{level}级{count}步" for level, count in sorted(confidence_dist.items())
    )
    
    return GeneratorResult(
        thought_chain=thought_chain,
        self_critique=self_critique,
        final_conclusion=final_conclusion,
        confidence_summary=confidence_summary,
    )


# ========== 格式化输出 ==========

def format_generation(result: GeneratorResult) -> str:
    """格式化生成结果"""
    lines = [
        "## 🧠 Generator 生成结果",
        "",
        "### 💭 思考链",
    ]
    
    for step in result.thought_chain:
        confidence_emoji = {
            "A": "🟢",
            "B": "🟡",
            "C": "🟠",
            "D": "🔴",
            "F": "⚫",
        }
        lines.append(f"\n**步骤 {step.step}** {confidence_emoji[step.confidence]} {step.confidence}级")
        lines.append(f"- 思考：{step.thinking}")
        lines.append(f"- 证据：{step.evidence}")
        if step.assumptions:
            lines.append(f"- 假设：{', '.join(step.assumptions[:2])}")
        if step.note:
            lines.append(f"- 备注：{step.note}")
    
    # 自我质疑
    lines.append("\n### 🤔 自我质疑")
    if result.self_critique.critique_points:
        lines.append("\n**质疑点：**")
        for point in result.self_critique.critique_points[:3]:
            lines.append(f"- {point}")
    
    if result.self_critique.missing_perspectives:
        lines.append("\n**遗漏的视角：**")
        for perspective in result.self_critique.missing_perspectives:
            lines.append(f"- {perspective}")
    
    if result.self_critique.knowledge_gaps:
        lines.append("\n**知识缺口：**")
        for gap in result.self_critique.knowledge_gaps[:3]:
            lines.append(f"- {gap}")
    
    # 最终结论
    lines.append("\n### 📝 最终结论")
    lines.append(result.final_conclusion)
    
    # 置信度总结
    lines.append(f"\n**{result.confidence_summary}**")
    
    return "\n".join(lines)


# ========== 单元测试 ==========

if __name__ == "__main__":
    import sys
    import io
    # Windows 控制台编码修复
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 构造测试数据
    subproblems = [
        {
            "id": "sp1",
            "question": "这只股票的基本面如何？",
            "assigned_role": "分析师",
            "uncertainty": "high",
        },
        {
            "id": "sp2",
            "question": "我的风险承受能力如何？",
            "assigned_role": "实用主义者",
            "uncertainty": "medium",
        },
        {
            "id": "sp3",
            "question": "市场环境如何？",
            "assigned_role": "远见者",
            "uncertainty": "high",
        },
    ]
    
    sprint_contract = {
        "goal": "给出投资决策建议",
        "deliverables": ["风险分析", "收益预期", "最终建议"],
        "quality_bar": "必须明确标记不确定性",
    }
    
    # 运行生成
    result = generate(subproblems, sprint_contract)
    print(format_generation(result))
