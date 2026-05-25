"""
测试 engine 包 — 导入和基础集成。
"""

import pytest
from engine import (
    SkillRegistry,
    SkillRouter,
    ContextBus,
    CanvasStateManager,
    ConversationEngine,
)


class TestEnginePackage:
    def test_all_imports(self):
        """package-level imports from engine/__init__.py"""
        assert SkillRegistry is not None
        assert SkillRouter is not None
        assert ContextBus is not None
        assert CanvasStateManager is not None
        # ConversationEngine requires API key for LLM client — skip instantiation test
        assert ConversationEngine is not None

    def test_direct_imports(self):
        """direct module imports"""
        from engine.skill_registry import SkillRegistry as SR
        from engine.skill_router import SkillRouter as SRt
        from engine.context_bus import ContextBus as CB
        from engine.canvas_state import CanvasStateManager as CSM
        from engine.conversation import ConversationEngine as CE
        assert SR is not None
        assert SRt is not None
        assert CB is not None
        assert CSM is not None
        assert CE is not None

    def test_skill_registry_no_skills_dir(self):
        """SkillRegistry with nonexistent directory should not crash"""
        registry = SkillRegistry(skills_dir="/nonexistent/path")
        assert registry.counts() == {"active": 0, "deprecated": 0, "pending": 0}
        assert registry.list_all() == []

    def test_skill_registry_with_real_skills(self):
        """SkillRegistry loads actual skills from repo"""
        registry = SkillRegistry(skills_dir="skills")
        counts = registry.counts()
        total = sum(counts.values())
        assert total >= 25, f"Expected at least 25 skills, got {total}"
        # Most skills should be active
        assert counts.get("active", 0) >= 20

    def test_skill_registry_catalog(self):
        """catalog_for_prompt returns non-empty string"""
        registry = SkillRegistry(skills_dir="skills")
        catalog = registry.catalog_for_prompt()
        assert len(catalog) > 0
        assert "- " in catalog
