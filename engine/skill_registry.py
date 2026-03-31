"""
SkillRegistry — 技能注册表管理。

职责（PRD FR-20~23）：
  - 加载 skills/ 文件夹中所有 .md 技能定义
  - 维护 active/deprecated/pending 状态
  - 提供技能元数据查询
  - 支持健康度追踪（命中率、失败率）
  - 支持热更新（文件变更自动加载）
"""

import re
import logging
from pathlib import Path
from typing import Optional

from models.schema import SkillMeta, SkillStatus

log = logging.getLogger("skill_registry")


class SkillRegistry:

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._skills: dict[str, SkillMeta] = {}
        self._definitions: dict[str, str] = {}
        self._load_all()

    def get(self, skill_id: str) -> Optional[SkillMeta]:
        return self._skills.get(skill_id)

    def get_definition(self, skill_id: str) -> Optional[str]:
        return self._definitions.get(skill_id)

    def list_active(self) -> list[SkillMeta]:
        return [s for s in self._skills.values() if s.status == SkillStatus.ACTIVE]

    def list_all(self) -> list[SkillMeta]:
        return list(self._skills.values())

    def counts(self) -> dict[str, int]:
        counts = {"active": 0, "deprecated": 0, "pending": 0}
        for s in self._skills.values():
            counts[s.status.value] = counts.get(s.status.value, 0) + 1
        return counts

    def skill_ids_active(self) -> list[str]:
        return [s.skill_id for s in self.list_active()]

    def catalog_for_prompt(self) -> str:
        lines = []
        for s in self.list_active():
            lines.append(f"- {s.skill_id}: {s.name} — {s.description} "
                         f"[适用: {s.applicable_when}]")
        return "\n".join(lines)

    def set_status(self, skill_id: str, status: SkillStatus):
        if skill_id in self._skills:
            self._skills[skill_id].status = status
            log.info(f"Skill {skill_id} → {status.value}")

    def record_hit(self, skill_id: str, success: bool):
        s = self._skills.get(skill_id)
        if s:
            s.hit_count += 1
            if not success:
                s.fail_count += 1

    def _load_all(self):
        if not self.skills_dir.exists():
            log.warning(f"Skills directory not found: {self.skills_dir}")
            return

        # 加载子目录中的 SKILL.md（主要格式）
        for path in sorted(self.skills_dir.glob("*/SKILL.md")):
            try:
                self._load_skill(path)
            except Exception as e:
                log.error(f"Failed to load skill {path.parent.name}: {e}")

        # 兼容：加载顶层 .md（排除 _ 开头和 index）
        for path in sorted(self.skills_dir.glob("*.md")):
            if path.name.startswith("_") or path.stem == "index":
                continue
            try:
                self._load_skill(path)
            except Exception as e:
                log.error(f"Failed to load skill {path.name}: {e}")

        log.info(f"Loaded {len(self._skills)} skills: {self.counts()}")

    def _load_skill(self, path: Path):
        text = path.read_text(encoding="utf-8")
        meta, definition = self._parse_frontmatter(text, path)
        self._skills[meta.skill_id] = meta
        self._definitions[meta.skill_id] = definition
        log.debug(f"  Loaded: {meta.skill_id} ({meta.name})")

    def _parse_frontmatter(self, text: str, path: Path) -> tuple[SkillMeta, str]:
        meta = SkillMeta(definition_path=str(path))

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if match:
            frontmatter_text = match.group(1)
            definition = match.group(2)

            for line in frontmatter_text.split("\n"):
                line = line.strip()
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                if key == "id":
                    meta.skill_id = val
                elif key == "name":
                    meta.name = val
                elif key == "version":
                    meta.version = val
                elif key == "description":
                    meta.description = val
                elif key == "applicable_when":
                    meta.applicable_when = val
                elif key == "status":
                    meta.status = SkillStatus(val)
        else:
            meta.skill_id = path.stem
            meta.name = path.stem.replace("_", " ").title()
            definition = text

        if not meta.skill_id:
            # 用 name 字段作为 skill_id（大多数 skill 只有 name 没有 id）
            if meta.name:
                meta.skill_id = meta.name
            # SKILL.md 文件用父目录名
            elif path.stem == "SKILL":
                meta.skill_id = path.parent.name
            else:
                meta.skill_id = path.stem

        return meta, definition

    def reload(self):
        self._skills.clear()
        self._definitions.clear()
        self._load_all()
