"""
deepthink — 结构化深度思考框架 v5.0

让 AI 的思考过程显式化、结构化、可追溯。

用法：
    from deepthink import DeepThinkEngine
    engine = DeepThinkEngine()
    result = engine.think("要不要跳槽？")
"""

from deepthink.deepthink import DeepThinkResult
from deepthink.multi_agent import (
    AgentRole,
    MultiAgentResult,
    decompose_question,
    get_active_roles,
    get_role_system_prompt,
    format_multi_agent_result,
)

__version__ = "5.0.0"
__author__ = "xuebi (雪碧 · 有灵龙虾)"

__all__ = [
    "DeepThinkResult",
    "AgentRole",
    "MultiAgentResult",
    "decompose_question",
    "get_active_roles",
    "get_role_system_prompt",
    "format_multi_agent_result",
]
