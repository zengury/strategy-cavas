"""
CanvasStateManager — 画布状态管理器。

职责（PRD FR-40~45）：
  - 将每轮 LLM 输出映射为画布 JSON
  - 增量 diff 更新（新增/修改/失效）
  - 节点可回溯到对话轮次与输入证据
  - 节点锁定（用户确认后不可被自动覆盖）
  - 导出 JSON
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from models.schema import CanvasState, CanvasNode, CanvasDiff, CANVAS_ZONES

log = logging.getLogger("canvas_state")


class CanvasStateManager:

    def __init__(self, store_path: str = "store"):
        self.store_dir = Path(store_path) / "cases"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._canvas = CanvasState()

    @property
    def canvas(self) -> CanvasState:
        return self._canvas

    def apply_diff(self, diff: CanvasDiff) -> CanvasState:
        self._canvas.apply_diff(diff)
        log.info(f"Canvas updated: v{self._canvas.version} "
                 f"(+{len(diff.added)} ~{len(diff.modified)} -{len(diff.invalidated)})")
        return self._canvas

    def parse_llm_canvas_output(self, output: dict, turn_id: str) -> CanvasDiff:
        """
        LLM 输出格式约定：
        {
          "canvas_updates": {
            "north_star": [{"content": "...", "confidence": 0.9}],
            "options": [
              {"content": "选项A", "confidence": 0.8},
              {"action": "invalidate", "node_id": "abc123"}
            ]
          }
        }
        """
        diff = CanvasDiff()
        updates = output.get("canvas_updates", {})

        for zone, items in updates.items():
            if zone not in CANVAS_ZONES:
                continue

            for item in items:
                action = item.get("action", "add")

                if action == "add":
                    node = CanvasNode(
                        zone=zone,
                        content=item.get("content", ""),
                        source_turn_id=turn_id,
                        source_evidence=item.get("evidence", ""),
                        confidence=item.get("confidence", 0.8),
                        risk_level=item.get("risk_level", "normal"),
                    )
                    diff.added.append(node)

                elif action == "modify" and "node_id" in item:
                    for field in ("content", "confidence", "risk_level"):
                        if field in item:
                            diff.modified.append({
                                "node_id": item["node_id"],
                                "field": field,
                                "old": None,
                                "new": item[field],
                            })

                elif action == "invalidate" and "node_id" in item:
                    diff.invalidated.append(item["node_id"])

        return diff

    def lock_node(self, node_id: str) -> bool:
        node = self._find_node(node_id)
        if node:
            node.locked = True
            return True
        return False

    def unlock_node(self, node_id: str) -> bool:
        node = self._find_node(node_id)
        if node:
            node.locked = False
            return True
        return False

    def _find_node(self, node_id: str):
        for zone_nodes in self._canvas.nodes.values():
            for node in zone_nodes:
                if node.node_id == node_id:
                    return node
        return None

    def export_json(self) -> str:
        return json.dumps(self._to_dict(), ensure_ascii=False, indent=2)

    def save(self, case_id: str):
        path = self.store_dir / f"{case_id}_canvas.json"
        with open(path, "w") as f:
            json.dump(self._to_dict(), f, ensure_ascii=False, indent=2)

    def load(self, case_id: str) -> bool:
        path = self.store_dir / f"{case_id}_canvas.json"
        if not path.exists():
            return False
        with open(path) as f:
            data = json.load(f)
        self._from_dict(data)
        return True

    def reset(self):
        self._canvas = CanvasState()

    def _to_dict(self) -> dict:
        result = {
            "case_id": self._canvas.case_id,
            "version": self._canvas.version,
            "updated_at": self._canvas.updated_at,
            "nodes": {},
            "edges": self._canvas.edges,
        }
        for zone, nodes in self._canvas.nodes.items():
            result["nodes"][zone] = [
                {
                    "node_id": n.node_id,
                    "content": n.content,
                    "source_turn_id": n.source_turn_id,
                    "source_evidence": n.source_evidence,
                    "confidence": n.confidence,
                    "locked": n.locked,
                    "status": n.status,
                    "risk_level": n.risk_level,
                    "created_at": n.created_at,
                    "updated_at": n.updated_at,
                }
                for n in nodes
            ]
        return result

    def _from_dict(self, data: dict):
        self._canvas = CanvasState(
            case_id=data.get("case_id", ""),
            version=data.get("version", 0),
            updated_at=data.get("updated_at", ""),
            edges=data.get("edges", []),
        )
        for zone in CANVAS_ZONES:
            zone_data = data.get("nodes", {}).get(zone, [])
            self._canvas.nodes[zone] = [
                CanvasNode(**{k: v for k, v in nd.items() if k != "zone"}, zone=zone)
                for nd in zone_data
            ]
