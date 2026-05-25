"""
engine — Strategic Canvas 核心引擎包

模块：
  skill_registry  — 技能 .md 文件加载与元数据管理
  skill_router    — 双通道技能路由（规则 + LLM）
  context_bus     — 多模态上下文总线
  canvas_state    — 3D 图状态管理
  conversation    — 对话编排引擎
"""

from engine.skill_registry import SkillRegistry
from engine.skill_router import SkillRouter
from engine.context_bus import ContextBus
from engine.canvas_state import CanvasStateManager
from engine.conversation import ConversationEngine
from engine.llm_client import LLMClient
from engine.response_parser import parse_json_response, parse_router_response
from engine.config import get_config, Config

__all__ = [
    "SkillRegistry",
    "SkillRouter",
    "ContextBus",
    "CanvasStateManager",
    "ConversationEngine",
    "LLMClient",
    "parse_json_response",
    "parse_router_response",
    "get_config",
    "Config",
]
