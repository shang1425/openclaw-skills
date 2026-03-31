"""
taskflow.engine
任务拆解引擎 - 把 deepthink 的推理结论拆成结构化任务
"""

import json
import re
from typing import Optional

from .schema import Task, TaskProject, TaskStatus, Priority


# API 配置（通过环境变量注入，不要硬编码）
# BASE_URL = os.environ.get("TASKFLOW_API_BASE", "")
# API_KEY = os.environ.get("TASKFLOW_API_KEY", "")


# ── 优先级推断规则 ──────────────────────────────────────────

PRIORITY_KEYWORDS = {
    Priority.A: [
        "立刻", "马上", "立即", "紧急", "critical", "urgent", "blocker",
        "阻塞", "无法", "致命", "拦路虎", "必须先", "依赖",
    ],
    Priority.B: [
        "重要", "本周", "尽快", "尽快", "优先", "高优",
        "应该", "需要", "最好", "建议",
    ],
    Priority.C: [
        "可以", "可选", "后续", "将来", "也许", "考虑",
        "优化", "改进", "锦上添花", "nice to have",
    ],
    Priority.D: [
        "选做", "低优", "次要", "延后", "随意", "随便", "随意",
    ],
}

# 时间预估（分钟）- 按关键词推断
TIME_KEYWORDS = {
    range(1, 16): ["快速", "简单", "5分钟", "10分钟", "小修改", "微调", "fix", "quick"],
    range(15, 61): ["中等", "30分钟", "1小时", "改一下", "实现", "写"],
    range(60, 181): ["较大", "2小时", "3小时", "复杂", "重构", "全面"],
    range(180, 481): ["大", "半天", "6小时", "8小时", "全面改造"],
    range(480, 1441): ["巨大", "一天", "几天", "长时间", "重构"],
}

DEPRECATION_PATTERNS = [
    re.compile(r"[（(].*?停用.*?[）)]"),
    re.compile(r"[（(].*?废弃.*?[）)]"),
    re.compile(r"[（(].*?deprecated.*?[）)]", re.I),
]


def estimate_minutes(text: str) -> Optional[int]:
    # 第一步：正则提取数字+单位
    val_m = re.search(r"(\d+)\s*(min|分钟|hour|小时|个小时|h)", text, re.I)
    if val_m:
        val, unit = int(val_m.group(1)), val_m.group(2).lower()
        if unit in ("hour", "小时", "个小时", "h"):
            return val * 60
        return val
    # 第二步：关键词推断
    for rng, kws in TIME_KEYWORDS.items():
        if any(k in text for k in kws):
            return rng.start
    return None


def infer_priority(text: str) -> Priority:
    """从文本推断优先级"""
    text_lower = text.lower()
    for pri, kws in PRIORITY_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in text_lower:
                return pri
    return Priority.C


def extract_labels(text: str) -> list[str]:
    """从文本中提取标签（#tag 或方括号内容）"""
    tags = re.findall(r"#(\w+)", text)
    brackets = re.findall(r"\[([^\]]+)\]", text)
    combined = tags + brackets
    # 过滤通用词
    stop = {"a", "b", "c", "d", "e", "f", "todo", "task", "item", "note"}
    return [t for t in combined if t.lower() not in stop]


def split_into_lines(text: str) -> list[str]:
    """按行或句号拆分文本，返回有意义的内容块"""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 去掉常见前缀
        line = re.sub(r"^\d+[．.、]\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"^\[[ABCDEF]\]?\s*", "", line)
        line = re.sub(r"^[【\[][ABCDEF][】\]]\s*", "", line)
        if len(line) < 4:
            continue
        lines.append(line)
    return lines


ACTION_VERBS = [
    "设计", "开发", "实现", "测试", "修复", "优化", "重构",
    "完成", "整理", "分析", "评估", "规划", "部署", "上线",
    "写", "做", "搞", "建立", "构建", "集成", "验证", "发布",
]

# 高优先级意图词（配合时间标记如"立刻"/"本周"使用时）
INTENT_PATTERNS = [
    re.compile(r"^[立刻马上立即尽快本周本周]?\s*[：:]\s*(.+)"),
    re.compile(r"^\[[ABCD]\]\s*"),
]


def parse_duration_in_text(text: str) -> Optional[int]:
    """从文本中解析时间信息"""
    hours = re.search(r"(\d+)\s*(小时|个小时|h)", text)
    mins = re.search(r"(\d+)\s*(分钟|min)", text)
    if hours:
        return int(hours.group(1)) * 60
    if mins:
        return int(mins.group(1))
    return estimate_minutes(text)


def is_deprecated(text: str) -> bool:
    return any(p.search(text) for p in DEPRECATION_PATTERNS)


# ── 简单规则拆解 ──────────────────────────────────────────────

def _extract_task_title(line: str) -> str:
    """从一行文本中提取任务标题"""
    # 去掉「立刻：」「本周：」等时间意图前缀（精确匹配词，非字符集）
    line = re.sub(r"^(立刻|马上|立即|尽快|本周|重要|可选|选做|建议|考虑)\s*[：:]\s*", "", line)
    # 去掉优先级标记
    line = re.sub(r"^[【\[][ABCD][】\]]?\s*", "", line)
    line = re.sub(r"^\[[ABCDEF]\]?\s*", "", line)
    return clean_title(line)


def rule_based_split(text: str, source: str = "") -> TaskProject:
    """
    基于规则的简单拆解：
    1. 识别优先级块（【A】立刻: / [B] 本周:）并提取意图信息
    2. 按时序/步骤拆分（第一步、第二步...）
    3. 提取关键动作（设计、开发、测试、发布...）
    4. 推断依赖关系
    """
    project = TaskProject(
        id=f"PRJ{gen_id()}",
        name=source or "TaskFlow Project",
        source=source,
    )

    lines = split_into_lines(text)
    tasks_by_title: dict[str, Task] = {}
    task_order: list[str] = []
    current_main_task: Optional[Task] = None

    # 时序步骤检测
    seq_markers = re.compile(r"^第[一二三四五六七八九十\d]+步")

    for line in lines:
        if is_deprecated(line):
            continue

        # 提取原始文本用于推断（保留意图词）
        raw_line = line
        title = _extract_task_title(line)

        # 时序步骤标题（第一步... 第二步...）
        if seq_markers.match(title):
            clean = seq_markers.sub("", title).strip()
            clean = re.sub(r"^[：:]\s*", "", clean)  # 去掉「第X步」后的冒号
            clean = clean_title(clean)
            task = project.add_task(title=clean)
            tasks_by_title[clean] = task
            task_order.append(clean)
            current_main_task = task
            task.priority = infer_priority(raw_line)
            task.estimated_minutes = parse_duration_in_text(raw_line) or estimate_minutes(raw_line)
            task.labels = extract_labels(raw_line)
            continue

        # 动作动词开头（作为任务标题，clean_title 会清理标点，不影响判断）
        if len(title) >= 4 and any(title.startswith(v) for v in ACTION_VERBS):
            task = project.add_task(title=title)
            tasks_by_title[title] = task
            task_order.append(title)
            current_main_task = task
            task.priority = infer_priority(raw_line)
            task.estimated_minutes = parse_duration_in_text(raw_line) or estimate_minutes(raw_line)
            task.labels = extract_labels(raw_line)
            continue

        # 「立刻: 」「本周: 」「可选: 」「选做: 」等格式 → 识别为任务
        intent_match = re.match(r"^(立刻|马上|立即|尽快|本周|重要|可选|选做|建议|考虑)\s*[：:]\s*(.+)", title)
        if intent_match:
            task_text = intent_match.group(2).strip()
            if len(task_text) >= 4:
                task = project.add_task(title=task_text)
                tasks_by_title[task_text] = task
                task_order.append(task_text)
                current_main_task = task
                task.priority = infer_priority(raw_line)
                task.estimated_minutes = parse_duration_in_text(raw_line) or estimate_minutes(raw_line)
                task.labels = extract_labels(raw_line)
                continue

        # 子任务/描述（较长行，或有明确的列表标记）
        is_subtask = (
            (current_main_task and len(title) >= 10) or
            re.match(r"^\s*[-*#]\s+\S", line) or
            re.match(r"^\s*\d+[.、)）]", line)
        )
        if is_subtask and current_main_task:
            existing = current_main_task.description
            sep = "\n" if existing else ""
            current_main_task.description += f"{sep}- {line}"

    # 推断依赖关系（按任务顺序）
    ordered_tasks = [tasks_by_title[k] for k in task_order if k in tasks_by_title]
    for i, task in enumerate(ordered_tasks):
        if i > 0:
            prev = ordered_tasks[i - 1]
            if prev.id != task.id and prev.id not in task.depends_on:
                task.depends_on.append(prev.id)

    # 兜底：标题行拆不出任务时，用段落逐段拆
    if not project.tasks and lines:
        for i, para in enumerate(lines):
            if is_deprecated(para):
                continue
            task = project.add_task(title=clean_title(para[:50]), description=para)
            task.priority = infer_priority(para)
            task.estimated_minutes = estimate_minutes(para)
            task.labels = extract_labels(para)
            if i > 0 and project.tasks:
                task.depends_on.append(project.tasks[i - 1].id)

    return project


def clean_title(text: str) -> str:
    """清理标题"""
    text = re.sub(r"^\d+[．.、]\s*", "", text)
    text = re.sub(r"^[-*]\s*", "", text)
    text = re.sub(r"^[：:]\s*", "", text)  # 去掉开头的冒号（第一步：「xxx」）
    text = text.strip("，。：:、.")
    return text[:100]


def gen_id() -> str:
    return str(Task.gen_id())


# ── LLM 智能拆解 ──────────────────────────────────────────────

LLM_PROMPT = """你是一个任务拆解专家。把下面的「思考结论」拆成结构化任务列表。

要求：
1. 每个任务有：标题（简洁动宾短语）、优先级[A/B/C/D]、预估分钟数
2. 优先级：A=立刻做，B=本周做，C=可延期，D=选做
3. 分析任务之间的依赖关系（depends_on 用任务序号）
4. 提取关键标签（labels，如 "design"、"core"、"testing"）
5. 忽略停用/废弃/已完成的项

输出格式（严格 JSON）：
{{
  "project_name": "项目名称",
  "description": "项目一句话描述",
  "tasks": [
    {{
      "id": "T1",
      "title": "任务标题",
      "description": "任务详细描述（可选）",
      "priority": "B",
      "depends_on": [],
      "estimated_minutes": 60,
      "labels": ["design"]
    }}
  ]
}}

下方是思考结论：
{content}
"""


async def llm_split(text: str, name: str = "LLM Project") -> TaskProject:
    """
    调用 LLM 进行智能拆解
    需要环境变量 DEEPSEEK_API_KEY 或 OPENAI_API_KEY
    """
    api_key = (
        "sk-abcd1234"  # TODO: 支持多 API 源
    )
    # 这里预留接口，具体实现依赖外部 API
    # 暂时用规则版本作为 fallback
    raise NotImplementedError(
        "LLM 拆解需要配置 API Key，当前请用 rule_based_split()"
    )


# ── 主入口 ────────────────────────────────────────────────────

def decompose(text: str, source: str = "", use_llm: bool = False) -> TaskProject:
    """
    任务拆解主入口

    Args:
        text: 输入文本（deepthink 结论、思考过程、需求描述等）
        source: 来源标识（如 "deepthink-v4.1"）
        use_llm: 是否强制使用 LLM 拆解（暂不支持）

    Returns:
        TaskProject: 结构化任务项目
    """
    project = rule_based_split(text, source=source)

    # 保证至少有任务
    if not project.tasks:
        project.add_task(
            title="处理输入内容",
            description=text[:500],
            priority=Priority.C,
        )

    return project


def decompose_and_save(text: str, source: str = "", output_path: str = "") -> TaskProject:
    """
    拆解并保存为 JSON 文件
    """
    import os
    project = decompose(text, source=source)

    if not output_path:
        import hashlib
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w]", "_", source or "taskflow")[:30]
        output_path = os.path.join(
            os.path.dirname(__file__) or ".",
            "..", "outputs",
            f"{safe_name}_{ts}.json"
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    return project
