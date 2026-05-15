const fs = require("fs");
const path = require("path");

class SkillRegistry {
  constructor(skillsDir) {
    this.skillsDir = skillsDir;
    this._skills = {};
    this._definitions = {};
    this._loadAll();
  }

  get(skillId) { return this._skills[skillId] || null; }
  getDefinition(skillId) { return this._definitions[skillId] || null; }
  listActive() { return Object.values(this._skills).filter(s => s.status === "active"); }
  skillIdsActive() { return this.listActive().map(s => s.skill_id); }

  catalogForPrompt() {
    return this.listActive().map(s =>
      `- ${s.skill_id}: ${s.name} — ${s.description} [适用: ${s.applicable_when}]`
    ).join("\n");
  }

  recordHit(skillId, success) {
    const s = this._skills[skillId];
    if (s) { s.hit_count += 1; if (!success) s.fail_count += 1; }
  }

  _loadAll() {
    if (!fs.existsSync(this.skillsDir)) return;
    // Load */SKILL.md
    const entries = fs.readdirSync(this.skillsDir, { withFileTypes: true });
    for (const d of entries) {
      if (d.isDirectory()) {
        const p = path.join(this.skillsDir, d.name, "SKILL.md");
        if (fs.existsSync(p)) this._loadSkill(p);
      }
    }
    // Load top-level *.md (not _ prefixed, not index)
    for (const d of entries) {
      if (d.isFile() && d.name.endsWith(".md") && !d.name.startsWith("_") && d.name !== "index.md") {
        this._loadSkill(path.join(this.skillsDir, d.name));
      }
    }
  }

  _loadSkill(filePath) {
    try {
      const text = fs.readFileSync(filePath, "utf-8");
      const meta = { skill_id: "", name: "", version: "1.0", description: "", applicable_when: "",
        status: "active", hit_count: 0, fail_count: 0, definition_path: filePath };
      let definition = text;

      const m = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)/);
      if (m) {
        definition = m[2];
        for (const line of m[1].split("\n")) {
          const idx = line.indexOf(":");
          if (idx === -1) continue;
          const key = line.slice(0, idx).trim();
          const val = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "");
          if (key === "id") meta.skill_id = val;
          else if (key === "name") meta.name = val;
          else if (key === "version") meta.version = val;
          else if (key === "description") meta.description = val;
          else if (key === "applicable_when") meta.applicable_when = val;
          else if (key === "status") meta.status = val;
        }
      }

      if (!meta.skill_id) {
        if (meta.name) meta.skill_id = meta.name;
        else if (path.basename(filePath) === "SKILL.md") meta.skill_id = path.basename(path.dirname(filePath));
        else meta.skill_id = path.basename(filePath, ".md");
      }

      this._skills[meta.skill_id] = meta;
      this._definitions[meta.skill_id] = definition;
    } catch (e) { /* skip */ }
  }

  reload() { this._skills = {}; this._definitions = {}; this._loadAll(); }
}
module.exports = { SkillRegistry };
