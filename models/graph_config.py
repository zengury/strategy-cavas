"""
图可视化配置 — 节点空间偏置、颜色映射、区块映射

从 models/schema.py 拆分，v2 重构。与数据模型解耦，可独立调整可视化参数。
"""

from __future__ import annotations

from models.enums import NodeType, EdgeType


# ── 节点类型的 3D 空间倾向 ──────────────────────────────────────
# (x_bias, y_bias, z_bias) 范围 [-1, 1]
# X: 时间 (左近/右远), Y: 确定性 (下低/上高), Z: 中心性 (前核心/后外围)

NODE_SPATIAL_BIAS: dict[NodeType, tuple[float, float, float]] = {
    NodeType.GOAL:        ( 0.8,  0.3,  0.0),   # 远期, 中确定, 核心
    NodeType.POSITION:    ( 0.2,  0.2,  0.0),   # 中期, 中确定, 核心
    NodeType.OPTION:      ( 0.3,  0.0,  0.1),   # 中期, 中等, 近核心
    NodeType.RESOURCE:    (-0.2,  0.3,  0.2),   # 近期, 中高确定, 近核心
    NodeType.CONSTRAINT:  (-0.2, -0.2,  0.5),   # 近期, 中低确定, 外围
    NodeType.TENSION:     ( 0.0, -0.4,  0.0),   # 当下, 低确定, 核心
    NodeType.ASSUMPTION:  ( 0.1, -0.6,  0.3),   # 中期, 低确定, 中外
    NodeType.RISK:        ( 0.2, -0.5,  0.2),   # 中期, 低确定, 中外
    NodeType.SIGNAL:      (-0.4,  0.5,  0.2),   # 近期, 高确定, 近核心
    NodeType.STAKEHOLDER: ( 0.0,  0.0,  0.7),   # 当下, 中等, 外围
    NodeType.MECHANISM:   ( 0.0,  0.1,  0.1),   # 当下, 中等, 近核心
    NodeType.EVIDENCE:    (-0.5,  0.6,  0.4),   # 近期, 高确定, 中外
    NodeType.PATTERN:     ( 0.5,  0.5,  0.3),   # 远期, 高确定, 中外
    NodeType.ACTION:      (-0.7,  0.1,  0.1),   # 即时, 中等, 近核心
}

# ── 节点类型的视觉属性 ──────────────────────────────────────────

NODE_COLORS: dict[NodeType, str] = {
    NodeType.GOAL:        "#FFD700",  # 金色
    NodeType.POSITION:    "#4A90D9",  # 钢蓝
    NodeType.OPTION:      "#50C878",  # 翡翠绿
    NodeType.RESOURCE:    "#9B59B6",  # 紫色
    NodeType.CONSTRAINT:  "#E74C3C",  # 红色
    NodeType.TENSION:     "#FF6B35",  # 橙红
    NodeType.ASSUMPTION:  "#F39C12",  # 琥珀
    NodeType.RISK:        "#C0392B",  # 深红
    NodeType.SIGNAL:      "#00BCD4",  # 青色
    NodeType.STAKEHOLDER: "#8D6E63",  # 棕色
    NodeType.MECHANISM:   "#7E57C2",  # 深紫
    NodeType.EVIDENCE:    "#26A69A",  # 青绿
    NodeType.PATTERN:     "#EC407A",  # 粉色
    NodeType.ACTION:      "#66BB6A",  # 浅绿
}

EDGE_COLORS: dict[EdgeType, str] = {
    EdgeType.SUPPORTS:      "#4CAF50",  # 绿
    EdgeType.CONTRADICTS:   "#F44336",  # 红
    EdgeType.ENABLES:       "#2196F3",  # 蓝
    EdgeType.BLOCKS:        "#FF5722",  # 深橙
    EdgeType.DEPENDS_ON:    "#9E9E9E",  # 灰
    EdgeType.VALIDATES:     "#00BCD4",  # 青
    EdgeType.EVOLVES_FROM:  "#AB47BC",  # 紫
    EdgeType.TRADEOFF:      "#FF9800",  # 橙
    EdgeType.MITIGATES:     "#8BC34A",  # 浅绿
    EdgeType.AMPLIFIES:     "#E91E63",  # 粉红
    EdgeType.FITS:          "#3F51B5",  # 靛蓝
    EdgeType.COMPETES_WITH: "#FF5252",  # 亮红
    EdgeType.LEVERAGES:     "#7C4DFF",  # 亮紫
    EdgeType.SCOPES:        "#607D8B",  # 蓝灰
}

# ── 画布区块映射（v1 遗留，用于 rule-based 路由的缺口检测）────

CANVAS_ZONES = [
    "north_star", "context", "options",
    "tradeoffs", "assumptions", "signals", "next_moves",
]

# NodeType → zone 的映射（让 rule 路由能从图节点推断 zone 覆盖）
NODE_TYPE_TO_ZONE: dict[NodeType, str] = {
    NodeType.GOAL:        "north_star",
    NodeType.POSITION:    "context",
    NodeType.OPTION:      "options",
    NodeType.RESOURCE:    "context",
    NodeType.CONSTRAINT:  "context",
    NodeType.TENSION:     "tradeoffs",
    NodeType.ASSUMPTION:  "assumptions",
    NodeType.RISK:        "signals",
    NodeType.SIGNAL:      "signals",
    NodeType.STAKEHOLDER: "context",
    NodeType.MECHANISM:   "options",
    NodeType.EVIDENCE:    "context",
    NodeType.PATTERN:     "context",
    NodeType.ACTION:      "next_moves",
}
