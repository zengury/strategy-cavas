"""
Strategic Canvas Live — 战略散步教练

启动方式：
  uvicorn main:app --reload --port 8000
  python main.py
  python main.py --port 8080
"""

import asyncio
import json
import logging
import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from engine.skill_registry import SkillRegistry
from engine.skill_router import SkillRouter
from engine.context_bus import ContextBus
from engine.canvas_state import CanvasStateManager
from engine.conversation import ConversationEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

app = FastAPI(title="Strategic Canvas Live", version="0.1.0")


def load_config(path: str = "config/app.yaml") -> dict:
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


config = load_config()
registry = SkillRegistry(config.get("skills_dir", "skills"))
router = SkillRouter(registry, config.get("llm", {}))
context_bus = ContextBus(max_turns=config.get("max_turns", 50))
canvas_manager = CanvasStateManager(config.get("store_path", "store"))
engine = ConversationEngine(registry, router, context_bus, canvas_manager, config.get("llm", {}))

# ── 静态文件 ──────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/")
async def index():
    return FileResponse("web/index.html")


# ── REST 端点 ─────────────────────────────────────────────────

@app.get("/api/skills")
async def list_skills():
    return {
        "counts": registry.counts(),
        "skills": [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "status": s.status.value,
                "hit_count": s.hit_count,
                "quality_score": s.quality_score,
            }
            for s in registry.list_all()
        ],
    }


@app.get("/api/canvas")
async def get_canvas():
    return JSONResponse(content=json.loads(canvas_manager.export_json()))


@app.post("/api/canvas/lock/{node_id}")
async def lock_node(node_id: str):
    return {"success": canvas_manager.lock_node(node_id)}


@app.post("/api/canvas/unlock/{node_id}")
async def unlock_node(node_id: str):
    return {"success": canvas_manager.unlock_node(node_id)}


@app.post("/api/canvas/export")
async def export_canvas():
    return JSONResponse(content=json.loads(canvas_manager.export_json()))


@app.post("/api/stage/{stage}")
async def set_stage(stage: str):
    from models.schema import Stage
    try:
        engine.advance_stage(Stage(stage))
        return {"stage": stage}
    except ValueError:
        return JSONResponse(status_code=400, content={"error": f"Invalid stage: {stage}"})


@app.post("/api/context/document")
async def add_document(payload: dict):
    ctx = context_bus.add_document(
        content=payload.get("content", ""),
        source_name=payload.get("source_name", ""),
    )
    return {"context_id": ctx.context_id}


@app.post("/api/reset")
async def reset_session():
    context_bus.clear()
    canvas_manager.reset()
    return {"status": "reset"}


# ── WebSocket 对话 ────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    log.info("WebSocket client connected")

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "chat":
                user_text = msg.get("text", "")
                if not user_text.strip():
                    continue

                await ws.send_json({"type": "thinking", "text": "正在思考..."})

                result = await engine.process_turn(user_text)

                await ws.send_json({
                    "type": "response",
                    "reply": result["reply"],
                    "stage": result["stage"],
                    "one_line_judgment": result["one_line_judgment"],
                    "confidence": result["confidence"],
                    "invocations": result["invocations"],
                    "canvas": json.loads(result["canvas"]),
                    "canvas_diff": result["canvas_diff"],
                    "latency_ms": result["latency_ms"],
                    "turn_id": result["turn_id"],
                })

            elif msg.get("type") == "lock_node":
                canvas_manager.lock_node(msg["node_id"])
                await ws.send_json({"type": "node_locked", "node_id": msg["node_id"]})

            elif msg.get("type") == "unlock_node":
                canvas_manager.unlock_node(msg["node_id"])
                await ws.send_json({"type": "node_unlocked", "node_id": msg["node_id"]})

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")


if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser(description="Strategic Canvas Live")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
