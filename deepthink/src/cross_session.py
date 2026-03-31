"""
deepthink — 跨 session 结论追踪模块
重要结论存档，下次对话自动引用
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime


DEFAULT_HISTORY_FILE = "reasoning_history.json"


def _load_history(filepath: str) -> dict:
    """加载历史结论"""
    if not os.path.exists(filepath):
        return {"conclusions": [], "version": "2.0"}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_history(filepath: str, data: dict):
    """保存历史结论"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def archive_conclusion(
    question: str,
    tags: List[str],
    one_liner: str,
    confidence_score: int,
    confidence_grade: str,
    key_reasoning: str = "",
    key_uncertainty: str = "",
    self_doubt: str = "",
    history_file: str = None,
) -> str:
    """
    存档一条结论

    Returns:
        结论 ID（如 r001）
    """
    if history_file is None:
        history_file = DEFAULT_HISTORY_FILE

    data = _load_history(history_file)
    conclusions = data["conclusions"]

    # 生成 ID
    cid = f"r{len(conclusions) + 1:03d}"

    entry = {
        "id": cid,
        "question": question,
        "tags": tags,
        "one_liner": one_liner,
        "confidence_score": confidence_score,
        "confidence_grade": confidence_grade,
        "key_reasoning": key_reasoning,
        "key_uncertainty": key_uncertainty,
        "self_doubt": self_doubt,
        "archived_at": datetime.now().isoformat(),
        "status": "active",  # active / superseded / invalidated
    }

    conclusions.append(entry)
    _save_history(history_file, data)
    return cid


def find_related(question: str, history_file: str = None, top_n: int = 3) -> List[dict]:
    """查找与当前问题相关的历史结论"""
    if history_file is None:
        history_file = DEFAULT_HISTORY_FILE

    data = _load_history(history_file)
    active = [c for c in data["conclusions"] if c["status"] == "active"]

    if not active:
        return []

    # 简单关键词匹配
    q_words = set(question.lower().split())
    scored = []
    for c in active:
        tag_words = set(w.lower() for t in c.get("tags", []) for w in t.split())
        overlap = q_words & tag_words
        if overlap:
            scored.append((c, len(overlap)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:top_n]]


def get_summary(history_file: str = None) -> str:
    """获取历史结论摘要"""
    if history_file is None:
        history_file = DEFAULT_HISTORY_FILE

    data = _load_history(history_file)
    active = [c for c in data["conclusions"] if c["status"] == "active"]

    if not active:
        return "📦 暂无存档结论"

    lines = [f"📦 已存档 {len(active)} 条结论\n"]
    for c in active[-5:]:  # 最近 5 条
        lines.append(
            f"- [{c['id']}] {c['one_liner']} "
            f"（{c['confidence_grade']}级，{c['confidence_score']}%）"
        )
        lines.append(f"  关键词：{'、'.join(c.get('tags', []))}")

    return "\n".join(lines)


def invalidate(cid: str, reason: str = "", history_file: str = None):
    """标记结论为已失效"""
    if history_file is None:
        history_file = DEFAULT_HISTORY_FILE

    data = _load_history(history_file)
    for c in data["conclusions"]:
        if c["id"] == cid:
            c["status"] = "invalidated"
            c["invalidate_reason"] = reason
            c["invalidated_at"] = datetime.now().isoformat()
            break
    _save_history(history_file, data)


# ========== 单元测试 ==========

if __name__ == "__main__":
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write('{"conclusions": [], "version": "2.0"}')
        tmp = f.name

    # 测试存档
    cid = archive_conclusion(
        question="要不要从上海回老家？",
        tags=["职业选择", "回老家"],
        one_liner="不建议回去，收入差距太大且有负债",
        confidence_score=72,
        confidence_grade="B",
        history_file=tmp,
    )
    print(f"存档 ID: {cid}")

    # 测试查找
    related = find_related("职业选择的问题", history_file=tmp)
    print(f"找到 {len(related)} 条相关结论")

    # 测试摘要
    print(get_summary(tmp))

    os.unlink(tmp)
    print("✅ 测试通过")
