"""
测试 ContextBus — 上下文管理。
"""

import pytest
from engine.context_bus import ContextBus
from models.schema import ConversationTurn, Stage


class TestContextBus:
    def test_empty_bus(self):
        bus = ContextBus(max_turns=10)
        assert len(bus.all_turns()) == 0
        snapshot = bus.snapshot()
        assert snapshot["turn_count"] == 0
        assert snapshot["documents"] == []

    def test_add_turn(self):
        bus = ContextBus(max_turns=10)
        turn = ConversationTurn(speaker="user", text="Hello", stage=Stage.EXPLORE)
        bus.add_turn(turn)
        assert len(bus.all_turns()) == 1
        assert bus.all_turns()[0].text == "Hello"

    def test_max_turns_truncation(self):
        bus = ContextBus(max_turns=3)
        for i in range(5):
            bus.add_turn(ConversationTurn(speaker="user", text=f"Turn {i}"))
        assert len(bus.all_turns()) == 3
        assert bus.all_turns()[-1].text == "Turn 4"

    def test_recent_turns(self):
        bus = ContextBus(max_turns=10)
        for i in range(10):
            bus.add_turn(ConversationTurn(speaker="user", text=f"Turn {i}"))
        recent = bus.recent_turns(3)
        assert len(recent) == 3
        assert recent[-1].text == "Turn 9"

    def test_clear(self):
        bus = ContextBus(max_turns=10)
        bus.add_turn(ConversationTurn())
        bus.clear()
        assert len(bus.all_turns()) == 0

    def test_snapshot_includes_conversation(self):
        bus = ContextBus(max_turns=10)
        bus.add_turn(ConversationTurn(speaker="user", text="Q1"))
        bus.add_turn(ConversationTurn(speaker="assistant", text="A1"))
        snap = bus.snapshot()
        assert len(snap["conversation"]) == 2
        assert snap["turn_count"] == 2

    def test_add_document(self):
        bus = ContextBus()
        ctx = bus.add_document("doc content", "test.txt")
        assert ctx.source_type == "document"
        snap = bus.snapshot()
        assert len(snap["documents"]) == 1

    def test_add_structured(self):
        bus = ContextBus()
        ctx = bus.add_structured({"key": "value"}, "label1")
        assert ctx.source_type == "structured"
        snap = bus.snapshot()
        assert len(snap["structured_inputs"]) == 1
