"""
models — Strategic Canvas 数据模型包

从单个 schema.py 重构为模块化结构：
  enums.py      — Stage, SkillStatus, NodeType, EdgeType
  domain.py     — 所有 dataclass 领域对象
  graph_config.py — 可视化常量
  compat.py     — v1 向后兼容别名
  schema.py     — 保留为兼容性 re-export（逐步废弃）
"""

from models.enums import Stage, SkillStatus, NodeType, EdgeType
from models.domain import (
    ConversationTurn,
    SkillInvocation,
    ContextObject,
    GraphNode,
    GraphEdge,
    GraphDiff,
    CanvasGraph,
    DecisionCase,
    SkillMeta,
)
from models.graph_config import (
    NODE_SPATIAL_BIAS,
    NODE_COLORS,
    EDGE_COLORS,
    CANVAS_ZONES,
    NODE_TYPE_TO_ZONE,
)
from models.compat import CanvasState

__all__ = [
    # Enums
    "Stage", "SkillStatus", "NodeType", "EdgeType",
    # Domain objects
    "ConversationTurn", "SkillInvocation", "ContextObject",
    "GraphNode", "GraphEdge", "GraphDiff", "CanvasGraph",
    "DecisionCase", "SkillMeta",
    # Config
    "NODE_SPATIAL_BIAS", "NODE_COLORS", "EDGE_COLORS",
    "CANVAS_ZONES", "NODE_TYPE_TO_ZONE",
    # Compat
    "CanvasState",
]
