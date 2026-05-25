"""
SkillRouter — 技能路由器 (v2)

职责（PRD FR-10~14）：
  - 每轮从技能库选择 1~3 个技能组合调用
  - 记录调用证据（skill id、版本、触发原因）
  - 技能调用失败时自动降级（fallback skill）
  - 路由策略：意图识别 + 结构缺口识别 + 置信度约束

路由双通道：
  1. 规则通道：基于画布结构缺口的确定性匹配（配置驱动，零 token）
  2. 模型通道：LLM 根据上下文选择最相关技能（仅在规则不足时启用）

v2: 路由规则从 config/routing.yaml 加载，不再硬编码。
"""

import json
import os
import re
import logging

from openai import AsyncOpenAI

from models.schema import (
    SkillInvocation, CanvasGraph, ConversationTurn,
    CANVAS_ZONES, Stage, NODE_TYPE_TO_ZONE,
)
from engine.skill_registry import SkillRegistry
from engine.config import get_config

log = logging.getLogger("skill_router")


class SkillRouter:

    def __init__(self, registry: SkillRegistry, llm_config: dict, config_dir: str = "config"):
        self.registry = registry
        self._cfg = get_config(config_dir)

        api_key = llm_config.get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")
        base_url = llm_config.get("api_base", "https://api.deepseek.com")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = llm_config.get("router_model", "deepseek-chat")

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
        for skill_id, reason in merged[:self._cfg.max_skills_per_turn]:
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
                skill_id=self._cfg.fallback_skill,
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

        # 配置驱动的缺口检测
        gap_rules = self._cfg.gap_rules
        for zone in CANVAS_ZONES:
            if zone not in covered_zones:
                candidates = gap_rules.get(zone, [])
                for skill_id in candidates:
                    if skill_id in active_ids:
                        suggestions.append((skill_id, f"canvas gap: {zone} zone is empty"))
                        break

        # 配置驱动的阶段技能
        stage_skills = self._cfg.stage_skills
        for skill_id, reason in stage_skills.get(stage.value, []):
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

        # 精简画布摘要：只列出已有节点类型和数量
        type_counts = {}
        for n in canvas.active_nodes():
            t = n.node_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        canvas_brief = json.dumps(type_counts, ensure_ascii=False) if type_counts else "空画布"

        prompt = self._cfg.router_prompt_template.format(
            user_text=turn.text,
            stage=turn.stage.value,
            canvas_brief=canvas_brief,
            catalog=catalog,
        )

        try:
            text = await self.llm.route(model=self.model, prompt=prompt)
            return parse_router_response(text)
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
