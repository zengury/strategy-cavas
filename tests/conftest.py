"""
测试 fixtures — 共享的测试数据和工具函数。
"""

import pytest
from models.schema import (
    Stage, NodeType, EdgeType,
    GraphNode, GraphEdge, GraphDiff, CanvasGraph,
    ConversationTurn, SkillInvocation,
)


@pytest.fixture
def sample_node():
    return GraphNode(
        node_type=NodeType.GOAL,
        label="Test Goal",
        content="A strategic goal for testing",
        source_turn_id="turn-001",
        source_evidence="User mentioned in turn 1",
        source_skill="goal_clarifier",
        confidence=0.9,
        weight=1.2,
    )


@pytest.fixture
def sample_edge():
    return GraphEdge(
        edge_type=EdgeType.SUPPORTS,
        source_id="node-a",
        target_id="node-b",
        label="supports relationship",
        strength=0.85,
        source_turn_id="turn-001",
    )


@pytest.fixture
def empty_canvas():
    return CanvasGraph()


@pytest.fixture
def canvas_with_nodes(sample_node):
    canvas = CanvasGraph()
    node2 = GraphNode(
        node_type=NodeType.OPTION,
        label="Option B",
        content="An alternative option",
        confidence=0.7,
    )
    canvas.nodes[sample_node.node_id] = sample_node
    canvas.nodes[node2.node_id] = node2
    return canvas


@pytest.fixture
def sample_turn():
    return ConversationTurn(
        speaker="user",
        text="I'm considering whether to pivot my startup.",
        stage=Stage.EXPLORE,
    )


@pytest.fixture
def sample_invocation():
    return SkillInvocation(
        turn_id="turn-001",
        skill_id="goal_clarifier",
        skill_version="1.0",
        reason="User is exploring goals",
    )
