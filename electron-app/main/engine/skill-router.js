const { NodeType, NODE_TYPE_TO_ZONE, CANVAS_ZONES, STAGE } = require("./schema");

const GAP_RULES = {
  north_star: ["goal_clarifier", "north_star_setter"],
  context: ["context_mapper", "constraint_scanner"],
  options: ["option_generator", "lateral_thinker"],
  tradeoffs: ["tradeoff_analyzer", "cost_benefit"],
  assumptions: ["assumption_surfacer", "hidden_belief_detector"],
  signals: ["signal_designer", "pre_mortem"],
  next_moves: ["experiment_designer", "minimum_viable_test"],
};

class SkillRouter {
  constructor(registry, client, model) {
    this.registry = registry;
    this.client = client;
    this.model = model || "deepseek-chat";
    this.MAX_SKILLS_PER_TURN = 3;
    this._fallbackSkill = "general_advisor";
  }

  async route(turn, canvas, contextSnapshot) {
    const rule = this._ruleBasedSuggestions(canvas, turn.stage);
    const model = rule.length < 2 ? await this._modelBasedRoute(turn, canvas, contextSnapshot) : [];
    const merged = this._merge(rule, model);

    const invocations = [];
    for (const [skillId, reason] of merged.slice(0, this.MAX_SKILLS_PER_TURN)) {
      const meta = this.registry.get(skillId);
      if (!meta) continue;
      invocations.push({ turn_id: turn.turn_id, skill_id: skillId, skill_version: meta.version, reason });
    }

    if (invocations.length === 0) {
      invocations.push({ turn_id: turn.turn_id, skill_id: this._fallbackSkill, skill_version: "1.0", reason: "fallback" });
    }
    return invocations;
  }

  _ruleBasedSuggestions(canvas, stage) {
    const suggestions = [];
    const activeIds = new Set(this.registry.skillIdsActive());
    const coveredZones = new Set();
    for (const n of canvas.activeNodes()) {
      const zone = NODE_TYPE_TO_ZONE[n.node_type];
      if (zone) coveredZones.add(zone);
    }
    for (const zone of CANVAS_ZONES) {
      if (!coveredZones.has(zone)) {
        for (const sid of GAP_RULES[zone] || []) {
          if (activeIds.has(sid)) { suggestions.push([sid, `canvas gap: ${zone} zone is empty`]); break; }
        }
      }
    }
    const stageSkills = {
      stress_test: [["pre_mortem", "stage: stress testing"], ["devils_advocate", "stage: contrarian view"]],
      commit: [["experiment_designer", "stage: commitment tests"], ["decision_criteria", "stage: criteria"]],
      review: [["retrospective", "stage: review"], ["cognitive_bias_check", "stage: bias audit"]],
    };
    for (const [sid, reason] of stageSkills[stage] || []) {
      if (activeIds.has(sid)) suggestions.push([sid, reason]);
    }
    return suggestions;
  }

  async _modelBasedRoute(turn, canvas, contextSnapshot) {
    const catalog = this.registry.catalogForPrompt();
    if (!catalog) return [];
    const typeCounts = {};
    for (const n of canvas.activeNodes()) typeCounts[n.node_type] = (typeCounts[n.node_type] || 0) + 1;
    const brief = Object.keys(typeCounts).length ? JSON.stringify(typeCounts) : "空画布";

    const prompt = `从技能目录选 1~3 个最相关技能。\n\n用户: ${turn.text}\n阶段: ${turn.stage}\n画布: ${brief}\n\n技能:\n${catalog}\n\n返回 JSON: [{"skill_id": "xxx", "reason": "..."}]`;

    try {
      const response = await this.client.chat.completions.create({
        model: this.model, max_tokens: 512, temperature: 0.0,
        messages: [{ role: "user", content: prompt }],
      });
      const text = response.choices[0].message.content;
      const m = text.match(/\[[\s\S]*\]/);
      if (m) {
        const items = JSON.parse(m[0]);
        return items.map(i => [i.skill_id, i.reason]);
      }
    } catch (e) { /* skip */ }
    return [];
  }

  _merge(rule, model) {
    const seen = new Set(); const merged = [];
    for (const [sid, reason] of [...rule, ...model]) {
      if (!seen.has(sid)) { seen.add(sid); merged.push([sid, reason]); }
    }
    return merged;
  }
}
module.exports = { SkillRouter, GAP_RULES };
