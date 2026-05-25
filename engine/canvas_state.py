"""
CanvasStateManager v2 — 自由图状态管理器。

职责：
  - 管理 CanvasGraph（节点 + 边的自由图）
  - 3D 空间定位：基于节点类型的语义偏置 + 力导向微调
  - 增量 diff 更新
  - 节点锁定
  - 导出 JSON（兼容 react-force-graph-3d）
"""

import json
import logging
import random
from pathlib import Path
from datetime import datetime

from models.schema import (
    CanvasGraph, GraphNode, GraphEdge, GraphDiff,
    NodeType, EdgeType, NODE_SPATIAL_BIAS,
)
from engine.config import get_config

log = logging.getLogger("canvas_state")


class CanvasStateManager:

    def __init__(self, store_path: str = "store", config_dir: str = "config"):
        self.store_dir = Path(store_path) / "cases"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._graph = CanvasGraph()
        self._cfg = get_config(config_dir)

    @property
    def graph(self) -> CanvasGraph:
        return self._graph

    # ── 核心操作 ─────────────────────────────────────────────

    def add_node(self, node: GraphNode) -> GraphNode:
        """添加节点并计算 3D 坐标。"""
        self._assign_position(node)
        self._graph.nodes[node.node_id] = node
        self._graph.version += 1
        self._graph.updated_at = datetime.now().isoformat()
        log.info(f"Node added: [{node.node_type.value}] {node.label}")
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """添加边（验证两端节点存在）。"""
        if edge.source_id not in self._graph.nodes:
            log.warning(f"Edge source {edge.source_id} not found")
            return edge
        if edge.target_id not in self._graph.nodes:
            log.warning(f"Edge target {edge.target_id} not found")
            return edge
        self._graph.edges[edge.edge_id] = edge
        log.info(f"Edge added: {edge.source_id} --{edge.edge_type.value}--> {edge.target_id}")
        return edge

    def apply_diff(self, diff: GraphDiff) -> CanvasGraph:
        """应用增量更新。"""
        for node in diff.added_nodes:
            self.add_node(node)
        for edge in diff.added_edges:
            self.add_edge(edge)
        for mod in diff.modified_nodes:
            node = self._graph.nodes.get(mod["node_id"])
            if node and not node.locked:
                setattr(node, mod["field"], mod["new"])
                node.updated_at = datetime.now().isoformat()
        for node_id in diff.invalidated_node_ids:
            node = self._graph.nodes.get(node_id)
            if node and not node.locked:
                node.status = "invalidated"

        self._graph.version += 1
        self._graph.updated_at = datetime.now().isoformat()
        log.info(f"Graph updated: v{self._graph.version} "
                 f"(+{len(diff.added_nodes)} nodes, +{len(diff.added_edges)} edges)")
        return self._graph

    def lock_node(self, node_id: str) -> bool:
        node = self._graph.nodes.get(node_id)
        if node:
            node.locked = True
            return True
        return False

    def unlock_node(self, node_id: str) -> bool:
        node = self._graph.nodes.get(node_id)
        if node:
            node.locked = False
            return True
        return False

    # ── 3D 空间定位 ──────────────────────────────────────────

    def _assign_position(self, node: GraphNode):
        """基于节点类型的语义偏置分配 3D 坐标。"""
        bias = NODE_SPATIAL_BIAS.get(node.node_type, (0, 0, 0))
        scale = self._cfg.space_scale
        jitter = self._cfg.jitter
        node.x = bias[0] * scale + random.uniform(-jitter, jitter)
        node.y = bias[1] * scale + random.uniform(-jitter, jitter)
        node.z = bias[2] * scale + random.uniform(-jitter, jitter)

    def parse_llm_canvas_output(self, parsed: dict, turn_id: str) -> GraphDiff:
        """从 LLM JSON 输出解析画布增量。"""
        diff = GraphDiff()
        updates = parsed.get("canvas_updates", {})

        # NodeType 名称 → zone 的反向映射
        zone_to_types = {
            "north_star": [NodeType.GOAL],
            "context":    [NodeType.POSITION, NodeType.RESOURCE, NodeType.CONSTRAINT,
                           NodeType.STAKEHOLDER, NodeType.EVIDENCE, NodeType.PATTERN],
            "options":    [NodeType.OPTION, NodeType.MECHANISM],
            "tradeoffs":  [NodeType.TENSION],
            "assumptions":[NodeType.ASSUMPTION],
            "signals":    [NodeType.SIGNAL, NodeType.RISK],
            "next_moves": [NodeType.ACTION],
        }

        for zone, items in updates.items():
            if not isinstance(items, list):
                continue
            # 该 zone 对应的默认 NodeType
            default_type = zone_to_types.get(zone, [NodeType.EVIDENCE])
            node_type = default_type[0] if default_type else NodeType.EVIDENCE

            for item in items:
                if not isinstance(item, dict):
                    continue

                action = item.get("action", "add")

                if action == "invalidate":
                    node_id = item.get("node_id", "")
                    if node_id:
                        diff.invalidated_node_ids.append(node_id)
                elif action == "modify":
                    node_id = item.get("node_id", "")
                    content = item.get("content", "")
                    if node_id and content:
                        diff.modified_nodes.append({
                            "node_id": node_id,
                            "field": "content",
                            "new": content,
                        })
                else:
                    # 新增节点
                    content = item.get("content", "")
                    if not content:
                        continue
                    node = GraphNode(
                        node_type=node_type,
                        label=content[:40],
                        content=content,
                        source_turn_id=turn_id,
                        source_evidence=item.get("evidence", ""),
                        confidence=item.get("confidence", 0.8),
                    )
                    diff.added_nodes.append(node)

        return diff

    # ── 查询 ─────────────────────────────────────────────────

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        return [n for n in self._graph.active_nodes() if n.node_type == node_type]

    def get_connected_nodes(self, node_id: str) -> list[GraphNode]:
        connected_ids = set()
        for e in self._graph.active_edges():
            if e.source_id == node_id:
                connected_ids.add(e.target_id)
            elif e.target_id == node_id:
                connected_ids.add(e.source_id)
        return [self._graph.nodes[nid] for nid in connected_ids
                if nid in self._graph.nodes]

    # ── 导出/持久化 ──────────────────────────────────────────

    def export_vis_json(self) -> str:
        """导出 react-force-graph-3d 兼容的 JSON。"""
        return json.dumps(self._graph.to_vis_data(), ensure_ascii=False, indent=2)

    def export_json(self) -> str:
        return self.export_vis_json()

    def save(self, case_id: str):
        path = self.store_dir / f"{case_id}_graph.json"
        with open(path, "w") as f:
            json.dump(self._graph.to_vis_data(), f, ensure_ascii=False, indent=2)

    def reset(self):
        self._graph = CanvasGraph()
