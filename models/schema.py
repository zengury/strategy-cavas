"""
数据模型 — Strategic Canvas Live 核心对象定义。

v2: 从固定 7 区块模型迁移到自由图模型。
  - GraphNode: 14 种语义标签，带 3D 坐标
  - GraphEdge: 14 种关系类型
  - CanvasGraph: 节点 + 边的自由图，替代固定 zone
  - 保留: ConversationTurn, SkillInvocation, DecisionCase, SkillMeta
"""

from __future__ import annotations

import uuid
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── 决策阶段状态机 ────────────────────────────────────────────

class Stage(str, Enum):
    EXPLORE = "explore"
    CONVERGE = "converge"
    STRESS_TEST = "stress_test"
    COMMIT = "commit"
    REVIEW = "review"


# ── 技能状态 ──────────────────────────────────────────────────

class SkillStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING = "pending"


# ── 节点类型（14 种，从 30 个 skills 的分析框架提炼）─────────────

class NodeType(str, Enum):
    GOAL = "goal"                # 战略意图/愿景/北极星
    POSITION = "position"        # 竞争定位/战略姿态
    OPTION = "option"            # 可选路径/战略方案
    RESOURCE = "resource"        # 能力/资产/核心competence
    CONSTRAINT = "constraint"    # 环境约束/结构性限制
    TENSION = "tension"          # 矛盾/两难/悖论
    ASSUMPTION = "assumption"    # 隐含假设/未验证前提
    RISK = "risk"                # 失败轨迹/威胁
    SIGNAL = "signal"            # 验证信号/早期指标
    STAKEHOLDER = "stakeholder"  # 利益相关方/外部势力
    MECHANISM = "mechanism"      # 战略机制/杠杆手段
    EVIDENCE = "evidence"        # 数据/事实/对话证据
    PATTERN = "pattern"          # 战略模式/类型
    ACTION = "action"            # 具体下一步/实验/战术


# ── 边类型（14 种，从 skills 的关系逻辑提炼）──────────────────

class EdgeType(str, Enum):
    SUPPORTS = "supports"             # A 为 B 提供支撑
    CONTRADICTS = "contradicts"       # A 与 B 矛盾
    ENABLES = "enables"               # A 使 B 成为可能
    BLOCKS = "blocks"                 # A 阻碍 B
    DEPENDS_ON = "depends_on"         # A 的成立依赖 B
    VALIDATES = "validates"           # A 能验证 B 是否成立
    EVOLVES_FROM = "evolves_from"     # A 由 B 演化而来
    TRADEOFF = "tradeoff"             # A 和 B 互斥取舍
    MITIGATES = "mitigates"           # A 能缓解 B
    AMPLIFIES = "amplifies"           # A 会加剧 B
    FITS = "fits"                     # A 与 B 匹配/consonance
    COMPETES_WITH = "competes_with"   # A 与 B 竞争同一资源
    LEVERAGES = "leverages"           # A 放大 B 的效果
    SCOPES = "scopes"                 # A 限定 B 的适用范围


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


# ── 对话轮次 ─────────────────────────────────────────────────

@dataclass
class ConversationTurn:
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    speaker: str = "user"           # "user" | "assistant"
    text: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    stage: Stage = Stage.EXPLORE


# ── 技能调用记录 ──────────────────────────────────────────────

@dataclass
class SkillInvocation:
    invocation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    turn_id: str = ""
    skill_id: str = ""
    skill_version: str = "1.0"
    reason: str = ""
    outcome: Optional[str] = None
    latency_ms: Optional[float] = None
    success: bool = True


# ── 多模态上下文对象 ──────────────────────────────────────────

@dataclass
class ContextObject:
    context_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_type: str = "text"
    raw_content: str = ""
    normalized_payload: dict = field(default_factory=dict)
    confidence: float = 1.0
    has_conflict: bool = False


# ── 图节点 ───────────────────────────────────────────────────

@dataclass
class GraphNode:
    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    node_type: NodeType = NodeType.EVIDENCE
    label: str = ""                    # 简短标签（显示在节点上）
    content: str = ""                  # 完整描述
    source_turn_id: str = ""           # 来源对话轮次
    source_evidence: str = ""          # 来源证据
    source_skill: str = ""             # 生成此节点的 skill
    confidence: float = 0.8
    weight: float = 1.0                # 重要性权重 0~2（影响节点大小和排序）
    locked: bool = False
    status: str = "active"             # "active" | "invalidated" | "superseded"
    # 3D 坐标（由空间引擎计算）
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "content": self.content,
            "source_turn_id": self.source_turn_id,
            "source_evidence": self.source_evidence,
            "source_skill": self.source_skill,
            "confidence": self.confidence,
            "locked": self.locked,
            "status": self.status,
            "x": self.x, "y": self.y, "z": self.z,
            "weight": self.weight,
            "color": NODE_COLORS.get(self.node_type, "#999999"),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── 图边 ─────────────────────────────────────────────────────

@dataclass
class GraphEdge:
    edge_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    edge_type: EdgeType = EdgeType.SUPPORTS
    source_id: str = ""                # 起始节点 ID
    target_id: str = ""                # 目标节点 ID
    label: str = ""                    # 关系描述
    strength: float = 1.0              # 关系强度 0~1
    source_turn_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.edge_id,
            "edge_type": self.edge_type.value,
            "source": self.source_id,
            "target": self.target_id,
            "label": self.label,
            "strength": self.strength,
            "color": EDGE_COLORS.get(self.edge_type, "#999999"),
        }


# ── 图增量 ───────────────────────────────────────────────────

@dataclass
class GraphDiff:
    added_nodes: list[GraphNode] = field(default_factory=list)
    added_edges: list[GraphEdge] = field(default_factory=list)
    modified_nodes: list[dict] = field(default_factory=list)
    invalidated_node_ids: list[str] = field(default_factory=list)


# ── 画布图状态 ────────────────────────────────────────────────

@dataclass
class CanvasGraph:
    case_id: str = ""
    nodes: dict[str, GraphNode] = field(default_factory=dict)   # node_id → GraphNode
    edges: dict[str, GraphEdge] = field(default_factory=dict)   # edge_id → GraphEdge
    version: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def active_nodes(self) -> list[GraphNode]:
        return [n for n in self.nodes.values() if n.status == "active"]

    def active_edges(self) -> list[GraphEdge]:
        active_ids = {n.node_id for n in self.active_nodes()}
        return [e for e in self.edges.values()
                if e.source_id in active_ids and e.target_id in active_ids]

    def apply_diff(self, diff: GraphDiff):
        for node in diff.added_nodes:
            self.nodes[node.node_id] = node
        for edge in diff.added_edges:
            self.edges[edge.edge_id] = edge
        for mod in diff.modified_nodes:
            node = self.nodes.get(mod["node_id"])
            if node and not node.locked:
                setattr(node, mod["field"], mod["new"])
                node.updated_at = datetime.now().isoformat()
        for node_id in diff.invalidated_node_ids:
            node = self.nodes.get(node_id)
            if node and not node.locked:
                node.status = "invalidated"
        self.version += 1
        self.updated_at = datetime.now().isoformat()

    def to_vis_data(self) -> dict:
        """输出 react-force-graph-3d 兼容的 JSON 格式。"""
        nodes = [n.to_dict() for n in self.active_nodes()]
        edges = [e.to_dict() for e in self.active_edges()]
        return {"nodes": nodes, "links": edges}

    def to_summary(self) -> dict:
        by_type: dict[str, list] = {}
        for n in self.active_nodes():
            by_type.setdefault(n.node_type.value, []).append({
                "id": n.node_id, "label": n.label,
                "confidence": n.confidence, "locked": n.locked,
            })
        return by_type


# ── 决策案例 ──────────────────────────────────────────────────

@dataclass
class DecisionCase:
    case_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    stage: Stage = Stage.EXPLORE
    one_line_judgment: str = ""
    confidence: float = 0.0
    canvas: CanvasGraph = field(default_factory=CanvasGraph)
    history: list[ConversationTurn] = field(default_factory=list)
    invocations: list[SkillInvocation] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ── 技能元数据 ────────────────────────────────────────────────

@dataclass
class SkillMeta:
    skill_id: str = ""
    name: str = ""
    version: str = "1.0"
    description: str = ""
    applicable_when: str = ""
    status: SkillStatus = SkillStatus.ACTIVE
    quality_score: float = 1.0
    hit_count: int = 0
    fail_count: int = 0
    satisfaction_contribution: float = 0.0
    definition_path: str = ""


# ── 兼容别名 ────────────────────────────────────────────────────
# v1 用 CanvasState + 固定 zone，v2 改为 CanvasGraph 自由图
# 保留别名避免 import 报错
CanvasState = CanvasGraph

# 画布区块名（v1 遗留，用于 rule-based 路由的缺口检测）
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
