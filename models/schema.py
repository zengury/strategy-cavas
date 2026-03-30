"""
数据模型 — Strategic Canvas Live 核心对象定义。

对齐 PRD §9 数据模型：
  ConversationTurn   — 单轮对话
  SkillInvocation    — 技能调用记录
  ContextObject      — 多模态输入归一化对象
  CanvasState        — 7 区块战略画布状态
  CanvasNode         — 画布节点（可追溯、可锁定）
  DecisionCase       — 完整决策案例
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
    source_type: str = "text"        # "text" | "document" | "structured" | "audio"
    raw_content: str = ""
    normalized_payload: dict = field(default_factory=dict)
    confidence: float = 1.0
    has_conflict: bool = False


# ── 画布节点 ──────────────────────────────────────────────────

@dataclass
class CanvasNode:
    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    zone: str = ""
    content: str = ""
    source_turn_id: str = ""
    source_evidence: str = ""
    confidence: float = 0.8
    locked: bool = False
    status: str = "active"           # "active" | "invalidated" | "superseded"
    risk_level: str = "normal"       # "normal" | "warning" | "critical"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ── 画布增量 ──────────────────────────────────────────────────

@dataclass
class CanvasDiff:
    added: list[CanvasNode] = field(default_factory=list)
    modified: list[dict] = field(default_factory=list)
    invalidated: list[str] = field(default_factory=list)


# ── 画布状态（7 区块）──────────────────────────────────────────

CANVAS_ZONES = [
    "north_star",
    "context",
    "options",
    "tradeoffs",
    "assumptions",
    "signals",
    "next_moves",
]


@dataclass
class CanvasState:
    case_id: str = ""
    nodes: dict[str, list[CanvasNode]] = field(default_factory=lambda: {
        zone: [] for zone in CANVAS_ZONES
    })
    edges: list[dict] = field(default_factory=list)
    version: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_zone_nodes(self, zone: str) -> list[CanvasNode]:
        return [n for n in self.nodes.get(zone, []) if n.status == "active"]

    def apply_diff(self, diff: CanvasDiff):
        for node in diff.added:
            if node.zone in self.nodes:
                self.nodes[node.zone].append(node)

        node_map = {n.node_id: n for zone_nodes in self.nodes.values() for n in zone_nodes}
        for mod in diff.modified:
            node = node_map.get(mod["node_id"])
            if node and not node.locked:
                setattr(node, mod["field"], mod["new"])
                node.updated_at = datetime.now().isoformat()

        for node_id in diff.invalidated:
            node = node_map.get(node_id)
            if node and not node.locked:
                node.status = "invalidated"

        self.version += 1
        self.updated_at = datetime.now().isoformat()

    def to_summary(self) -> dict:
        summary = {}
        for zone in CANVAS_ZONES:
            active = self.get_zone_nodes(zone)
            summary[zone] = [{"id": n.node_id, "content": n.content,
                              "confidence": n.confidence, "locked": n.locked}
                             for n in active]
        return summary


# ── 决策案例 ──────────────────────────────────────────────────

@dataclass
class DecisionCase:
    case_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    stage: Stage = Stage.EXPLORE
    one_line_judgment: str = ""
    confidence: float = 0.0
    canvas: CanvasState = field(default_factory=CanvasState)
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
