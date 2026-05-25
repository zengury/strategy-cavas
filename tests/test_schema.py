"""
测试 models 模块 — 数据类构造、序列化、枚举值。
"""

import pytest
from models.schema import (
    Stage, SkillStatus, NodeType, EdgeType,
    GraphNode, GraphEdge, GraphDiff, CanvasGraph,
    ConversationTurn, SkillInvocation, ContextObject,
    DecisionCase, SkillMeta,
    NODE_SPATIAL_BIAS, NODE_COLORS, EDGE_COLORS,
    CANVAS_ZONES, NODE_TYPE_TO_ZONE,
    CanvasState,
)


class TestEnums:
    def test_stage_values(self):
        assert Stage.EXPLORE == "explore"
        assert Stage.CONVERGE == "converge"
        assert Stage.STRESS_TEST == "stress_test"
        assert Stage.COMMIT == "commit"
        assert Stage.REVIEW == "review"
        assert len(Stage) == 5

    def test_skill_status_values(self):
        assert SkillStatus.ACTIVE == "active"
        assert SkillStatus.DEPRECATED == "deprecated"
        assert SkillStatus.PENDING == "pending"

    def test_node_type_count(self):
        assert len(NodeType) == 14

    def test_edge_type_count(self):
        assert len(EdgeType) == 14


class TestGraphNode:
    def test_default_construction(self):
        node = GraphNode()
        assert len(node.node_id) == 8
        assert node.node_type == NodeType.EVIDENCE
        assert node.status == "active"
        assert node.confidence == 0.8
        assert node.weight == 1.0
        assert not node.locked

    def test_custom_construction(self):
        node = GraphNode(
            node_type=NodeType.GOAL,
            label="North Star",
            content="Become market leader",
            confidence=0.95,
            weight=1.5,
            locked=True,
        )
        assert node.label == "North Star"
        assert node.node_type == NodeType.GOAL
        assert node.confidence == 0.95
        assert node.locked

    def test_to_dict(self, sample_node):
        d = sample_node.to_dict()
        assert d["id"] == sample_node.node_id
        assert d["node_type"] == "goal"
        assert d["label"] == "Test Goal"
        assert d["confidence"] == 0.9
        assert d["weight"] == 1.2
        assert d["locked"] == False
        assert d["status"] == "active"
        assert "color" in d
        assert "x" in d and "y" in d and "z" in d
        assert d["color"] == NODE_COLORS[NodeType.GOAL]

    def test_node_id_uniqueness(self):
        nodes = [GraphNode() for _ in range(100)]
        ids = {n.node_id for n in nodes}
        assert len(ids) == 100


class TestGraphEdge:
    def test_default_construction(self):
        edge = GraphEdge()
        assert len(edge.edge_id) == 8
        assert edge.edge_type == EdgeType.SUPPORTS
        assert edge.strength == 1.0

    def test_to_dict(self, sample_edge):
        d = sample_edge.to_dict()
        assert d["id"] == sample_edge.edge_id
        assert d["edge_type"] == "supports"
        assert d["source"] == "node-a"
        assert d["target"] == "node-b"
        assert d["strength"] == 0.85
        assert "color" in d
        assert d["color"] == EDGE_COLORS[EdgeType.SUPPORTS]


class TestCanvasGraph:
    def test_empty_canvas(self, empty_canvas):
        assert len(empty_canvas.active_nodes()) == 0
        assert len(empty_canvas.active_edges()) == 0
        assert empty_canvas.version == 0

    def test_add_and_query_nodes(self, empty_canvas, sample_node):
        empty_canvas.nodes[sample_node.node_id] = sample_node
        assert len(empty_canvas.active_nodes()) == 1

    def test_invalidated_nodes_excluded(self, empty_canvas, sample_node):
        sample_node.status = "invalidated"
        empty_canvas.nodes[sample_node.node_id] = sample_node
        assert len(empty_canvas.active_nodes()) == 0

    def test_to_vis_data(self, canvas_with_nodes):
        data = canvas_with_nodes.to_vis_data()
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) == 2

    def test_to_summary(self, canvas_with_nodes):
        summary = canvas_with_nodes.to_summary()
        assert "goal" in summary
        assert "option" in summary
        assert len(summary["goal"]) == 1

    def test_apply_diff_adds_nodes(self, empty_canvas):
        diff = GraphDiff(
            added_nodes=[
                GraphNode(node_type=NodeType.ACTION, label="Step 1", content="Do X"),
                GraphNode(node_type=NodeType.ACTION, label="Step 2", content="Do Y"),
            ]
        )
        empty_canvas.apply_diff(diff)
        assert len(empty_canvas.nodes) == 2
        assert empty_canvas.version == 1

    def test_apply_diff_invalidates_unlocked_nodes(self, canvas_with_nodes, sample_node):
        diff = GraphDiff(invalidated_node_ids=[sample_node.node_id])
        initial_version = canvas_with_nodes.version
        canvas_with_nodes.apply_diff(diff)
        assert canvas_with_nodes.nodes[sample_node.node_id].status == "invalidated"
        assert canvas_with_nodes.version == initial_version + 1

    def test_locked_node_not_invalidated(self, empty_canvas):
        node = GraphNode(node_type=NodeType.GOAL, label="Locked Goal", locked=True)
        empty_canvas.nodes[node.node_id] = node
        diff = GraphDiff(invalidated_node_ids=[node.node_id])
        empty_canvas.apply_diff(diff)
        assert empty_canvas.nodes[node.node_id].status == "active"


class TestConversationTurn:
    def test_default_construction(self):
        turn = ConversationTurn()
        assert turn.speaker == "user"
        assert turn.stage == Stage.EXPLORE
        assert len(turn.turn_id) == 12

    def test_assistant_turn(self, sample_turn):
        assert sample_turn.speaker == "user"
        assert sample_turn.text != ""
        assert sample_turn.stage == Stage.EXPLORE


class TestSkillInvocation:
    def test_construction(self, sample_invocation):
        assert sample_invocation.skill_id == "goal_clarifier"
        assert sample_invocation.skill_version == "1.0"
        assert sample_invocation.success == True


class TestBackwardCompat:
    def test_canvas_state_alias(self):
        assert CanvasState is CanvasGraph
