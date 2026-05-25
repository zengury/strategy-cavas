"""
核心领域对象 — 画布图、对话轮次、技能调用等数据类

从 models/schema.py 拆分，v2 重构。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.enums import Stage, SkillStatus, NodeType, EdgeType
from models.graph_config import NODE_COLORS, EDGE_COLORS


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
        nodes_data = [n.to_dict() for n in self.active_nodes()]
        edges_data = [e.to_dict() for e in self.active_edges()]
        return {"nodes": nodes_data, "links": edges_data}

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
