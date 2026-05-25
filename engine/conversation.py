"""
ConversationEngine v3 — 对话编排引擎。

职责（PRD FR-01~04, §6.2 对话协议）：
  - 多轮自然语言对话
  - "顺滑教练风格"系统提示词
  - 每轮 4 步：接住 → 点亮 → 试探 → 落脚
  - 阶段推进（explore → converge → stress_test → commit → review）
  - 调用选中 skill 定义注入上下文，生成教练回复 + 画布增量

v2: SYSTEM_PROMPT 从 config/prompts.yaml 加载，参数从 config 模块读取。
    技能强制原则不变：每轮助手输出必须由 skill 调用支撑。
"""

import json
import time
import logging

from models.schema import (
    ConversationTurn, SkillInvocation, Stage,
)
from engine.skill_registry import SkillRegistry
from engine.skill_router import SkillRouter
from engine.context_bus import ContextBus
from engine.canvas_state import CanvasStateManager
from engine.config import get_config
from engine.llm_client import LLMClient
from engine.response_parser import parse_json_response

log = logging.getLogger("conversation")


class ConversationEngine:

    def __init__(
        self,
        registry: SkillRegistry,
        router: SkillRouter,
        context_bus: ContextBus,
        canvas_manager: CanvasStateManager,
        llm_config: dict,
        config_dir: str = "config",
    ):
        self.registry = registry
        self.router = router
        self.context_bus = context_bus
        self.canvas_manager = canvas_manager
        self._cfg = get_config(config_dir)

        api_key = llm_config.get("api_key")
        base_url = llm_config.get("api_base", "https://api.deepseek.com")
        self.llm = LLMClient(api_key=api_key, api_base=base_url)
        self.model = llm_config.get("model", "deepseek-chat")
        self._stage = Stage.EXPLORE

    @property
    def stage(self) -> Stage:
        return self._stage

    async def process_turn(self, user_text: str) -> dict:
        """
        单轮处理流程（PRD §10.1）：
          用户输入 → 归一化 → skill 路由 → LLM 生成 → 画布 diff → 返回
        """
        t0 = time.time()

        # 1. 创建用户 turn
        user_turn = ConversationTurn(speaker="user", text=user_text, stage=self._stage)
        self.context_bus.add_turn(user_turn)

        # 2. Skill 路由
        context_snapshot = self.context_bus.snapshot(self.canvas_manager.graph)
        invocations = await self.router.route(
            user_turn, self.canvas_manager.graph, context_snapshot,
        )

        # 3. 加载技能定义（按配置截断，避免大量 token 消耗）
        max_chars = self._cfg.max_skill_chars
        skill_definitions = []
        for inv in invocations:
            defn = self.registry.get_definition(inv.skill_id)
            if defn:
                truncated = defn[:max_chars]
                if len(defn) > max_chars:
                    truncated += "\n...(已截断)"
                skill_definitions.append(f"### Skill: {inv.skill_id}\n{truncated}")
            self.registry.record_hit(inv.skill_id, success=True)

        # 4. LLM 生成
        llm_result = await self._call_llm(user_text, context_snapshot,
                                           skill_definitions, invocations)

        # 5. 解析回复
        parsed = parse_json_response(llm_result)

        # 6. 更新阶段
        new_stage = parsed.get("stage", self._stage.value)
        if new_stage in [s.value for s in Stage]:
            self._stage = Stage(new_stage)

        # 7. 画布增量
        diff = self.canvas_manager.parse_llm_canvas_output(parsed, user_turn.turn_id)
        self.canvas_manager.apply_diff(diff)

        # 8. 记录助手 turn
        assistant_turn = ConversationTurn(
            speaker="assistant", text=parsed.get("reply", ""), stage=self._stage,
        )
        self.context_bus.add_turn(assistant_turn)

        # 9. 结果
        latency_ms = (time.time() - t0) * 1000
        for inv in invocations:
            inv.latency_ms = latency_ms

        return {
            "reply": parsed.get("reply", ""),
            "stage": self._stage.value,
            "one_line_judgment": parsed.get("one_line_judgment", ""),
            "confidence": parsed.get("confidence", 0.0),
            "invocations": [
                {"skill_id": i.skill_id, "reason": i.reason, "version": i.skill_version}
                for i in invocations
            ],
            "canvas": self.canvas_manager.export_json(),
            "canvas_diff": {
                "added": len(diff.added_nodes),
                "modified": len(diff.modified_nodes),
                "invalidated": len(diff.invalidated_node_ids),
            },
            "latency_ms": round(latency_ms),
            "turn_id": user_turn.turn_id,
        }

    async def _call_llm(
        self, user_text: str, context: dict,
        skill_definitions: list[str], invocations: list[SkillInvocation],
    ) -> str:
        skills_block = "\n\n---\n\n".join(skill_definitions) if skill_definitions else "无特定技能激活"

        # 精简画布：只发类型计数 + 最重要的几个节点标签
        summary = self.canvas_manager.graph.to_summary()
        max_labels = self._cfg.max_canvas_labels_per_type
        brief = {}
        for ntype, nodes in summary.items():
            labels = [n["label"] for n in nodes[:max_labels]]
            brief[ntype] = {"count": len(nodes), "labels": labels}
        canvas_json = json.dumps(brief, ensure_ascii=False, indent=1)

        conversation_context = ""
        for t in self.context_bus.recent_turns(self._cfg.max_turns_context):
            prefix = "用户" if t.speaker == "user" else "教练"
            text = t.text[:800] if len(t.text) > 800 else t.text
            conversation_context += f"{prefix}: {text}\n\n"

        user_message = f"""## 对话历史
{conversation_context}

## 当前用户输入
{user_text}

## 当前决策阶段
{self._stage.value}

## 当前画布状态
{canvas_json}

## 本轮激活技能
{skills_block}

## 路由理由
{json.dumps([{"skill": i.skill_id, "reason": i.reason} for i in invocations], ensure_ascii=False)}

请按照系统提示词的格式输出你的回复。"""

        return await self.llm.chat(
            model=self.model,
            system_prompt=self._cfg.system_prompt,
            user_message=user_message,
        )

    def advance_stage(self, stage: Stage):
        self._stage = stage
        log.info(f"Stage advanced to: {stage.value}")
