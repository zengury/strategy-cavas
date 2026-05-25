"""
配置加载器 — 从 YAML 文件读取所有可配置参数，提供默认值。

v2 重构：将硬编码常量（SYSTEM_PROMPT, GAP_RULES, 可视化参数）提取到外部配置。
"""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml

log = logging.getLogger("config")


class Config:
    """应用配置的单一入口，惰性加载 YAML 文件。"""

    _instance: Optional["Config"] = None

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)

    # ── LLM ──────────────────────────────────────────────────

    @property
    def llm_provider(self) -> str:
        return self._load_app().get("llm", {}).get("provider", "deepseek")

    @property
    def llm_api_base(self) -> str:
        return self._load_app().get("llm", {}).get("api_base", "https://api.deepseek.com")

    @property
    def llm_model(self) -> str:
        return self._load_app().get("llm", {}).get("model", "deepseek-chat")

    @property
    def llm_router_model(self) -> str:
        return self._load_app().get("llm", {}).get("router_model", "deepseek-chat")

    @property
    def llm_api_key(self) -> str:
        return self._load_app().get("llm", {}).get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")

    @property
    def skills_dir(self) -> str:
        return self._load_app().get("skills_dir", "skills")

    @property
    def store_path(self) -> str:
        return self._load_app().get("store_path", "store")

    @property
    def max_turns(self) -> int:
        return self._load_app().get("max_turns", 50)

    # ── Routing ──────────────────────────────────────────────

    @property
    def gap_rules(self) -> dict:
        return self._load_routing().get("gap_rules", {})

    @property
    def stage_skills(self) -> dict:
        return self._load_routing().get("stage_skills", {})

    @property
    def max_skills_per_turn(self) -> int:
        return self._load_routing().get("max_skills_per_turn", 3)

    @property
    def fallback_skill(self) -> str:
        return self._load_routing().get("fallback_skill", "general_advisor")

    # ── Prompts ──────────────────────────────────────────────

    @property
    def system_prompt(self) -> str:
        return self._load_prompts().get("system_prompt", "")

    @property
    def router_prompt_template(self) -> str:
        return self._load_prompts().get("router_prompt", "")

    @property
    def max_skill_chars(self) -> int:
        return self._load_prompts().get("max_skill_chars", 1500)

    @property
    def max_turns_context(self) -> int:
        return self._load_prompts().get("max_turns_context", 5)

    @property
    def max_canvas_labels_per_type(self) -> int:
        return self._load_prompts().get("max_canvas_labels_per_type", 5)

    # ── Graph ────────────────────────────────────────────────

    @property
    def space_scale(self) -> int:
        return self._load_graph().get("space_scale", 200)

    @property
    def jitter(self) -> int:
        return self._load_graph().get("jitter", 40)

    @property
    def max_nodes(self) -> int:
        return self._load_graph().get("max_nodes", 500)

    # ── Internal loaders (lazy, cached) ──────────────────────

    def _load_app(self) -> dict:
        if not hasattr(self, "_cache_app"):
            path = self.config_dir / "app.yaml"
            self._cache_app = self._read_yaml(path) if path.exists() else {}
        return self._cache_app

    def _load_routing(self) -> dict:
        if not hasattr(self, "_cache_routing"):
            path = self.config_dir / "routing.yaml"
            self._cache_routing = self._read_yaml(path) if path.exists() else {}
        return self._cache_routing

    def _load_prompts(self) -> dict:
        if not hasattr(self, "_cache_prompts"):
            path = self.config_dir / "prompts.yaml"
            self._cache_prompts = self._read_yaml(path) if path.exists() else {}
        return self._cache_prompts

    def _load_graph(self) -> dict:
        if not hasattr(self, "_cache_graph"):
            path = self.config_dir / "graph.yaml"
            self._cache_graph = self._read_yaml(path) if path.exists() else {}
        return self._cache_graph

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if data else {}


# 全局配置实例（惰性初始化）
_config: Optional[Config] = None


def get_config(config_dir: str = "config") -> Config:
    """获取配置单例。"""
    global _config
    if _config is None:
        _config = Config(config_dir)
    return _config


def reload_config():
    """清空缓存，下次访问时重新加载配置。"""
    global _config
    _config = Config(_config.config_dir if _config else "config")
