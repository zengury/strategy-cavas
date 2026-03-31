"""
ContextBus — 多模态上下文总线。

职责（PRD FR-30~35）：
  - 接入对话文本、文档、结构化输入、语音转写
  - 归一化为统一 ContextObject 供 skill 调用
  - 对冲突信息打标签（uncertainty）
  - 维护当前案例的完整上下文窗口
"""

import logging
from typing import Optional

from models.schema import ContextObject, ConversationTurn, CanvasGraph

log = logging.getLogger("context_bus")


class ContextBus:

    def __init__(self, max_turns: int = 50):
        self.max_turns = max_turns
        self._turns: list[ConversationTurn] = []
        self._documents: list[ContextObject] = []
        self._structured: list[ContextObject] = []

    # ── 输入接入 ──────────────────────────────────────────────────

    def add_turn(self, turn: ConversationTurn):
        self._turns.append(turn)
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

    def add_document(self, content: str, source_name: str = "") -> ContextObject:
        ctx = ContextObject(
            source_type="document",
            raw_content=content,
            normalized_payload={"source": source_name, "text": content},
        )
        self._documents.append(ctx)
        log.info(f"Document added: {source_name} ({len(content)} chars)")
        return ctx

    def add_structured(self, data: dict, label: str = "") -> ContextObject:
        ctx = ContextObject(
            source_type="structured",
            raw_content=str(data),
            normalized_payload={"label": label, "data": data},
        )
        self._structured.append(ctx)
        log.info(f"Structured input added: {label}")
        return ctx

    # ── 上下文快照 ────────────────────────────────────────────────

    def snapshot(self, canvas: Optional[CanvasGraph] = None) -> dict:
        return {
            "conversation": [
                {"speaker": t.speaker, "text": t.text, "turn_id": t.turn_id,
                 "intent": t.intent, "stage": t.stage.value}
                for t in self._turns[-20:]
            ],
            "documents": [
                {"source": d.normalized_payload.get("source", ""),
                 "text": d.normalized_payload.get("text", "")[:2000]}
                for d in self._documents
            ],
            "structured_inputs": [
                s.normalized_payload for s in self._structured
            ],
            "canvas_summary": canvas.to_summary() if canvas else {},
            "turn_count": len(self._turns),
        }

    def recent_turns(self, n: int = 5) -> list[ConversationTurn]:
        return self._turns[-n:]

    def all_turns(self) -> list[ConversationTurn]:
        return list(self._turns)

    def clear(self):
        self._turns.clear()
        self._documents.clear()
        self._structured.clear()
