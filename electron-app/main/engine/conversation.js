const { createConversationTurn, STAGE } = require("./schema");

const SYSTEM_PROMPT = `你是 Strategic Canvas 的战略教练——一个像经验丰富的朋友、并肩散步时帮对方理清重大选择的伙伴。

## 你的身份
- 你不区分"商业决策"还是"生活决策"——所有重大选择都用同一套战略逻辑
- 你的语气温暖但精准，像一个值得信赖的老朋友而不是面试官
- 你永远先接住对方的情绪和担忧，再展开分析

## 每轮回复协议（严格遵守）
1. **接住**：用自己的话复述用户真正担心的点
2. **点亮**：只提 1 个关键启发问题
3. **试探**：给出条件化判断（"如果 X 成立，那么 Y 可能是更好的方向，但代价是 Z"）
4. **落脚**：给一个最小验证动作

## 约束
- 每轮最多 1 个主问题，避免审讯感
- 每 2-3 轮必须产出临时结论
- 建议必须包含：成立条件、代价、失败信号

## 画布更新
每轮输出画布增量 JSON，映射到 7 个区块：north_star / context / options / tradeoffs / assumptions / signals / next_moves

## 输出格式
\`\`\`json
{
  "reply": "自然语言回复",
  "stage": "explore/converge/stress_test/commit/review",
  "one_line_judgment": "一句话判断",
  "confidence": 0.65,
  "skills_applied": ["skill_id"],
  "canvas_updates": {
    "north_star": [], "options": [], "context": [], "tradeoffs": [],
    "assumptions": [], "signals": [], "next_moves": []
  }
}
\`\`\``;

const STAGE_VALUES = Object.values(STAGE);

class ConversationEngine {
  constructor(registry, router, contextBus, canvasManager, client, model) {
    this.registry = registry;
    this.router = router;
    this.contextBus = contextBus;
    this.canvasManager = canvasManager;
    this.client = client;
    this.model = model || "deepseek-chat";
    this._stage = STAGE.EXPLORE;
  }

  async processTurn(userText) {
    const t0 = Date.now();
    const userTurn = createConversationTurn({ speaker: "user", text: userText, stage: this._stage });
    this.contextBus.addTurn(userTurn);

    const ctx = this.contextBus.snapshot(this.canvasManager.graph);
    const invocations = await this.router.route(userTurn, this.canvasManager.graph, ctx);

    const skillDefs = [];
    for (const inv of invocations) {
      let defn = this.registry.getDefinition(inv.skill_id);
      if (defn) {
        if (defn.length > 1500) defn = defn.slice(0, 1500) + "\n...(已截断)";
        skillDefs.push("### Skill: " + inv.skill_id + "\n" + defn);
      }
      this.registry.recordHit(inv.skill_id, true);
    }

    const llmText = await this._callLlm(userText, ctx, skillDefs, invocations);
    const parsed = this._parseResponse(llmText);

    const newStage = parsed.stage || this._stage;
    if (STAGE_VALUES.includes(newStage)) this._stage = newStage;

    const diff = this.canvasManager.parseLlmCanvasOutput(parsed, userTurn.turn_id);
    this.canvasManager.applyDiff(diff);

    this.contextBus.addTurn(createConversationTurn({ speaker: "assistant", text: parsed.reply || "", stage: this._stage }));

    const latency = Date.now() - t0;
    return {
      reply: parsed.reply || "", stage: this._stage,
      one_line_judgment: parsed.one_line_judgment || "", confidence: parsed.confidence || 0,
      invocations: invocations.map(i => ({ skill_id: i.skill_id, reason: i.reason, version: i.skill_version })),
      canvas: this.canvasManager.exportJson(),
      canvas_diff: { added: (diff.added_nodes || []).length, modified: (diff.modified_nodes || []).length, invalidated: (diff.invalidated_node_ids || []).length },
      latency_ms: latency, turn_id: userTurn.turn_id,
    };
  }

  async _callLlm(userText, context, skillDefs, invocations) {
    const skillsBlock = skillDefs.length > 0 ? skillDefs.join("\n\n---\n\n") : "无特定技能激活";
    const summary = this.canvasManager.graph.toSummary();
    const brief = {};
    for (const [t, nodes] of Object.entries(summary)) brief[t] = { count: nodes.length, labels: nodes.slice(0, 5).map(n => n.label) };

    let convCtx = "";
    for (const t of this.contextBus.recentTurns(5)) {
      convCtx += (t.speaker === "user" ? "用户" : "教练") + ": " + (t.text.length > 800 ? t.text.slice(0, 800) : t.text) + "\n\n";
    }

    const userMsg = `## 对话历史\n${convCtx}\n## 当前用户输入\n${userText}\n\n## 当前决策阶段\n${this._stage}\n\n## 当前画布状态\n${JSON.stringify(brief, null, 1)}\n\n## 本轮激活技能\n${skillsBlock}\n\n## 路由理由\n${JSON.stringify(invocations.map(i => ({ skill: i.skill_id, reason: i.reason })))}\n\n请按照系统提示词的格式输出你的回复。`;

    const resp = await this.client.chat.completions.create({
      model: this.model, max_tokens: 4096, temperature: 0.7,
      messages: [{ role: "system", content: SYSTEM_PROMPT }, { role: "user", content: userMsg }],
    });
    return resp.choices[0].message.content;
  }

  _parseResponse(text) {
    const m = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (m) { try { return JSON.parse(m[1]); } catch {} }
    try { return JSON.parse(text); } catch {}
    return { reply: text, canvas_updates: {} };
  }
}
module.exports = ConversationEngine;
