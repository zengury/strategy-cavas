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

log = logging.getLogger("canvas_state")

# 3D 空间范围
SPACE_SCALE = 200  # 节点分布范围 [-SCALE, SCALE]
JITTER = 40        # 同类型节点的随机偏移量


class CanvasStateManager:

    def __init__(self, store_path: str = "store"):
        self.store_dir = Path(store_path) / "cases"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._graph = CanvasGraph()

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
        node.x = bias[0] * SPACE_SCALE + random.uniform(-JITTER, JITTER)
        node.y = bias[1] * SPACE_SCALE + random.uniform(-JITTER, JITTER)
        node.z = bias[2] * SPACE_SCALE + random.uniform(-JITTER, JITTER)

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
