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
    SkillInvocation, CanvasState, ConversationTurn,
    CANVAS_ZONES, Stage,
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
        canvas: CanvasState,
        context_snapshot: dict,
    ) -> list[SkillInvocation]:
        # 通道1：规则匹配
        rule_suggestions = self._rule_based_suggestions(canvas, turn.stage)

        # 通道2：LLM 路由
        model_suggestions = await self._model_based_route(turn, canvas, context_snapshot)

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
        self, canvas: CanvasState, stage: Stage,
    ) -> list[tuple[str, str]]:
        suggestions = []
        active_ids = set(self.registry.skill_ids_active())

        for zone in CANVAS_ZONES:
            active_nodes = canvas.get_zone_nodes(zone)
            if len(active_nodes) == 0:
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
        canvas: CanvasState,
        context_snapshot: dict,
    ) -> list[tuple[str, str]]:
        catalog = self.registry.catalog_for_prompt()
        if not catalog:
            return []

        canvas_summary = json.dumps(canvas.to_summary(), ensure_ascii=False, indent=1)

        prompt = f"""你是一个战略教练系统的技能路由器。
用户刚说了这段话，请从技能目录中选出 1~3 个最相关的技能。

## 用户输入
{turn.text}

## 当前决策阶段
{turn.stage.value}

## 当前画布状态
{canvas_summary}

## 可用技能目录
{catalog}

## 输出格式
返回 JSON 数组，每项包含 skill_id 和 reason：
```json
[{{"skill_id": "xxx", "reason": "一句话说明为什么选这个"}}]
```

注意：最多选 3 个，优先选对当前对话最有帮助的，reason 要具体。"""

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
