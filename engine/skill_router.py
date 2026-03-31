"""
SkillRouter — 技能路由器。

职责（PRD FR-10~14）：
  - 每轮从技能库选择 1~3 个技能组合调用
  - 记录调用证据（skill id、版本、触发原因）
  - 技能调用失败时自动降级（fallback skill）
  - 路由策略：意图识别 + 结构缺口识别 + 置信度约束

路由双通道：
  1. 规则通道：基于画布结构缺口的确定性匹配
  2. 模型通道：LLM 根据上下文选择最相关技能
"""

import json
import re
import time
import logging
from typing import Optional

from anthropic import Anthropic

from models.schema import (
    SkillInvocation, CanvasGraph, ConversationTurn,
    CANVAS_ZONES, Stage, NODE_TYPE_TO_ZONE,
)
from engine.skill_registry import SkillRegistry

log = logging.getLogger("skill_router")

# 结构缺口 → 推荐 skill 的规则映射
GAP_RULES: dict[str, list[str]] = {
    "north_star": ["goal_clarifier", "north_star_setter"],
    "context":    ["context_mapper", "constraint_scanner"],
    "options":    ["option_generator", "lateral_thinker"],
    "tradeoffs":  ["tradeoff_analyzer", "cost_benefit"],
    "assumptions": ["assumption_surfacer", "hidden_belief_detector"],
    "signals":    ["signal_designer", "pre_mortem"],
    "next_moves": ["experiment_designer", "minimum_viable_test"],
}


class SkillRouter:

    MAX_SKILLS_PER_TURN = 3

    def __init__(self, registry: SkillRegistry, llm_config: dict):
        self.registry = registry
        self.client = Anthropic(api_key=llm_config.get("api_key"))
        self.model = llm_config.get("router_model", "claude-sonnet-4-5-20250514")
        self._fallback_skill = "general_advisor"

    async def route(
        self,
        turn: ConversationTurn,
        canvas: CanvasGraph,
        context_snapshot: dict,
    ) -> list[SkillInvocation]:
        # 通道1：规则匹配（零 token 消耗）
        rule_suggestions = self._rule_based_suggestions(canvas, turn.stage)

        # 通道2：LLM 路由（仅在规则匹配不足时启用，节省 token）
        if len(rule_suggestions) < 2:
            model_suggestions = await self._model_based_route(turn, canvas, context_snapshot)
        else:
            model_suggestions = []

        # 合并去重
        merged = self._merge(rule_suggestions, model_suggestions)

        invocations = []
        for skill_id, reason in merged[:self.MAX_SKILLS_PER_TURN]:
            meta = self.registry.get(skill_id)
            if not meta:
                continue
            invocations.append(SkillInvocation(
                turn_id=turn.turn_id,
                skill_id=skill_id,
                skill_version=meta.version,
                reason=reason,
            ))

        if not invocations:
            invocations.append(SkillInvocation(
                turn_id=turn.turn_id,
                skill_id=self._fallback_skill,
                skill_version="1.0",
                reason="fallback — no specific skill matched",
            ))

        log.info(f"Routed skills: {[i.skill_id for i in invocations]}")
        return invocations

    def _rule_based_suggestions(
        self, canvas: CanvasGraph, stage: Stage,
    ) -> list[tuple[str, str]]:
        suggestions = []
        active_ids = set(self.registry.skill_ids_active())

        # 从图节点推断哪些 zone 已覆盖
        covered_zones = set()
        for node in canvas.active_nodes():
            zone = NODE_TYPE_TO_ZONE.get(node.node_type)
            if zone:
                covered_zones.add(zone)

        for zone in CANVAS_ZONES:
            if zone not in covered_zones:
                candidates = GAP_RULES.get(zone, [])
                for skill_id in candidates:
                    if skill_id in active_ids:
                        suggestions.append((skill_id, f"canvas gap: {zone} zone is empty"))
                        break

        stage_skills = {
            Stage.STRESS_TEST: [("pre_mortem", "stage: stress testing phase"),
                                ("devils_advocate", "stage: need contrarian view")],
            Stage.COMMIT: [("experiment_designer", "stage: designing commitment tests"),
                           ("decision_criteria", "stage: finalizing criteria")],
            Stage.REVIEW: [("retrospective", "stage: review and learn"),
                           ("cognitive_bias_check", "stage: bias audit")],
        }
        for skill_id, reason in stage_skills.get(stage, []):
            if skill_id in active_ids:
                suggestions.append((skill_id, reason))

        return suggestions

    async def _model_based_route(
        self,
        turn: ConversationTurn,
        canvas: CanvasGraph,
        context_snapshot: dict,
    ) -> list[tuple[str, str]]:
        catalog = self.registry.catalog_for_prompt()
        if not catalog:
            return []

        # 精简画布摘要：只列出已有节点类型和数量，避免发送完整内容
        type_counts = {}
        for n in canvas.active_nodes():
            t = n.node_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        canvas_brief = json.dumps(type_counts, ensure_ascii=False) if type_counts else "空画布"

        prompt = f"""从技能目录选 1~3 个最相关技能。

用户: {turn.text}
阶段: {turn.stage.value}
画布: {canvas_brief}

技能:
{catalog}

返回 JSON: [{{"skill_id": "xxx", "reason": "..."}}]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text

            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                items = json.loads(match.group())
                return [(item["skill_id"], item["reason"]) for item in items]
        except Exception as e:
            log.warning(f"Model-based routing failed: {e}")

        return []

    def _merge(
        self,
        rule: list[tuple[str, str]],
        model: list[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        seen = set()
        merged = []
        for skill_id, reason in rule + model:
            if skill_id not in seen:
                seen.add(skill_id)
                merged.append((skill_id, reason))
        return merged
