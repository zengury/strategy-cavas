"""
测试 CanvasStateManager — 图状态管理。
"""

import pytest
from engine.canvas_state import CanvasStateManager
from models.schema import GraphNode, GraphEdge, GraphDiff, NodeType, EdgeType


class TestCanvasStateManager:
    def test_empty_graph(self):
        mgr = CanvasStateManager()
        assert len(mgr.graph.active_nodes()) == 0
        assert mgr.graph.version == 0

    def test_add_node(self, sample_node):
        mgr = CanvasStateManager()
        mgr.add_node(sample_node)
        assert len(mgr.graph.active_nodes()) == 1
        assert mgr.graph.version == 1
        # 3D coordinates should be assigned
        assert sample_node.x != 0 or sample_node.y != 0 or sample_node.z != 0

    def test_add_edge_invalid_source(self):
        mgr = CanvasStateManager()
        edge = GraphEdge(source_id="nonexistent", target_id="also-fake")
        mgr.add_edge(edge)  # should not raise
        # Edge not added (source/target not in graph)
        assert len(mgr.graph.edges) == 0

    def test_add_edge_valid(self):
        mgr = CanvasStateManager()
        n1 = mgr.add_node(GraphNode(node_type=NodeType.GOAL, label="A"))
        n2 = mgr.add_node(GraphNode(node_type=NodeType.OPTION, label="B"))
        edge = GraphEdge(source_id=n1.node_id, target_id=n2.node_id)
        mgr.add_edge(edge)
        assert len(mgr.graph.edges) == 1

    def test_lock_unlock(self, sample_node):
        mgr = CanvasStateManager()
        mgr.add_node(sample_node)
        assert mgr.lock_node(sample_node.node_id) == True
        assert sample_node.locked == True
        assert mgr.unlock_node(sample_node.node_id) == True
        assert sample_node.locked == False

    def test_lock_nonexistent(self):
        mgr = CanvasStateManager()
        assert mgr.lock_node("nonexistent") == False

    def test_apply_diff(self):
        mgr = CanvasStateManager()
        existing = mgr.add_node(GraphNode(node_type=NodeType.GOAL, label="Old"))

        diff = GraphDiff(
            added_nodes=[GraphNode(node_type=NodeType.OPTION, label="New")],
            added_edges=[],
            modified_nodes=[{"node_id": existing.node_id, "field": "label", "new": "Updated"}],
            invalidated_node_ids=[],
        )
        mgr.apply_diff(diff)
        assert len(mgr.graph.nodes) == 2
        assert mgr.graph.nodes[existing.node_id].label == "Updated"

    def test_apply_diff_invalidate(self, sample_node):
        mgr = CanvasStateManager()
        mgr.add_node(sample_node)
        diff = GraphDiff(invalidated_node_ids=[sample_node.node_id])
        mgr.apply_diff(diff)
        assert mgr.graph.nodes[sample_node.node_id].status == "invalidated"

    def test_export_json_returns_dict(self):
        mgr = CanvasStateManager()
        mgr.add_node(GraphNode(node_type=NodeType.GOAL, label="Test"))
        exported = mgr.export_json()
        import json
        data = json.loads(exported) if isinstance(exported, str) else exported
        assert "nodes" in data
        assert len(data["nodes"]) == 1

    def test_reset(self, sample_node):
        mgr = CanvasStateManager()
        mgr.add_node(sample_node)
        mgr.reset()
        assert len(mgr.graph.active_nodes()) == 0
        assert mgr.graph.version == 0

    def test_3d_positioning(self):
        mgr = CanvasStateManager()
        nodes = []
        for nt in NodeType:
            node = GraphNode(node_type=nt, label=nt.value)
            mgr.add_node(node)
            nodes.append(node)
        # All nodes should have coordinates
        for node in nodes:
            assert isinstance(node.x, float)
            assert isinstance(node.y, float)
            assert isinstance(node.z, float)
