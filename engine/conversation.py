"""
ConversationEngine — 对话引擎。

职责（PRD FR-01~04, §6.2 对话协议）：
  - 多轮自然语言对话
  - "顺滑教练风格"系统提示词
  - 每轮 4 步：接住 → 点亮 → 试探 → 落脚
  - 阶段推进（explore → converge → stress_test → commit → review）
  - 调用选中 skill 定义注入上下文，生成教练回复 + 画布增量

技能强制原则：每轮助手输出必须由 skill 调用支撑。
"""

import json
import re
import time
import logging

from anthropic import Anthropic

from models.schema import (
    ConversationTurn, SkillInvocation, Stage, CanvasDiff,
)
from engine.skill_registry import SkillRegistry
from engine.skill_router import SkillRouter
from engine.context_bus import ContextBus
from engine.canvas_state import CanvasStateManager

log = logging.getLogger("conversation")

SYSTEM_PROMPT = """你是 Strategic Canvas 的战略教练——一个像经验丰富的朋友、并肩散步时帮对方理清重大选择的伙伴。

## 你的身份
- 你不区分"商业决策"还是"生活决策"——所有重大选择都用同一套战略逻辑
- 你的语气温暖但精准，像一个值得信赖的老朋友而不是面试官
- 你永远先接住对方的情绪和担忧，再展开分析

## 每轮回复协议（严格遵守）
每轮回复必须包含以下 4 步，但表达要自然流畅，不要显式标号：

1. **接住**：用自己的话复述用户真正担心的点（证明你听懂了）
2. **点亮**：只提 1 个关键启发问题（不要连续追问）
3. **试探**：给出条件化判断（"如果 X 成立，那么 Y 可能是更好的方向，但代价是 Z"）
4. **落脚**：给一个最小验证动作（用户可以立即去做的具体小步骤）

## 约束
- 每轮最多 1 个主问题，避免审讯感
- 每 2-3 轮必须产出临时结论
- 建议必须包含：成立条件、代价、失败信号
- 不要说"这是一个好问题"之类的空话
- 不要列清单，用自然段落表达

## 技能驱动
你的分析由激活的技能（skills）驱动。每轮回复中，你必须运用指定技能的框架进行思考。
技能定义会以上下文形式提供给你。

## 画布更新
每轮回复同时输出画布增量更新（JSON），映射到 7 个区块：
north_star / context / options / tradeoffs / assumptions / signals / next_moves

## 输出格式
你的回复必须是以下 JSON，包裹在 ```json ``` 中：

```json
{
  "reply": "你对用户说的自然语言回复（遵循 4 步协议）",
  "stage": "当前决策阶段 (explore/converge/stress_test/commit/review)",
  "one_line_judgment": "一句话当前判断",
  "confidence": 0.65,
  "skills_applied": ["skill_id_1", "skill_id_2"],
  "canvas_updates": {
    "north_star": [{"content": "...", "confidence": 0.9, "evidence": "用户第3轮提到..."}],
    "options": [],
    "context": [],
    "tradeoffs": [],
    "assumptions": [],
    "signals": [],
    "next_moves": []
  }
}
```

注意：
- canvas_updates 中只包含本轮有变化的区块（无变化的写空数组）
- 每个节点必须有 evidence 字段说明来源
- 如果要失效某个已有节点：{"action": "invalidate", "node_id": "xxx"}
- 如果要修改某个已有节点：{"action": "modify", "node_id": "xxx", "content": "新内容"}
"""


class ConversationEngine:

    def __init__(
        self,
        registry: SkillRegistry,
        router: SkillRouter,
        context_bus: ContextBus,
        canvas_manager: CanvasStateManager,
        llm_config: dict,
    ):
        self.registry = registry
        self.router = router
        self.context_bus = context_bus
        self.canvas_manager = canvas_manager

        self.client = Anthropic(api_key=llm_config.get("api_key"))
        self.model = llm_config.get("model", "claude-sonnet-4-5-20250514")
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
        context_snapshot = self.context_bus.snapshot(self.canvas_manager.canvas)
        invocations = await self.router.route(
            user_turn, self.canvas_manager.canvas, context_snapshot,
        )

        # 3. 加载技能定义
        skill_definitions = []
        for inv in invocations:
            defn = self.registry.get_definition(inv.skill_id)
            if defn:
                skill_definitions.append(f"### Skill: {inv.skill_id}\n{defn}")
            self.registry.record_hit(inv.skill_id, success=True)

        # 4. LLM 生成
        llm_result = await self._call_llm(user_text, context_snapshot,
                                           skill_definitions, invocations)

        # 5. 解析回复
        parsed = self._parse_response(llm_result)

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
                "added": len(diff.added),
                "modified": len(diff.modified),
                "invalidated": len(diff.invalidated),
            },
            "latency_ms": round(latency_ms),
            "turn_id": user_turn.turn_id,
        }

    async def _call_llm(
        self, user_text: str, context: dict,
        skill_definitions: list[str], invocations: list[SkillInvocation],
    ) -> str:
        skills_block = "\n\n---\n\n".join(skill_definitions) if skill_definitions else "无特定技能激活"
        canvas_json = json.dumps(
            self.canvas_manager.canvas.to_summary(), ensure_ascii=False, indent=1,
        )

        conversation_context = ""
        for t in self.context_bus.recent_turns(10):
            prefix = "用户" if t.speaker == "user" else "教练"
            conversation_context += f"{prefix}: {t.text}\n\n"

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def _parse_response(self, text: str) -> dict:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                log.warning(f"JSON parse error: {e}")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        return {"reply": text, "canvas_updates": {}}

    def advance_stage(self, stage: Stage):
        self._stage = stage
        log.info(f"Stage advanced to: {stage.value}")
