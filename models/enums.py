"""
策略画布核心枚举 — Stage, SkillStatus, NodeType, EdgeType

从 models/schema.py 拆分，v2 重构。
"""

from __future__ import annotations

from enum import Enum


# ── 决策阶段状态机 ────────────────────────────────────────────

class Stage(str, Enum):
    EXPLORE = "explore"
    CONVERGE = "converge"
    STRESS_TEST = "stress_test"
    COMMIT = "commit"
    REVIEW = "review"


# ── 技能状态 ──────────────────────────────────────────────────

class SkillStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING = "pending"


# ── 节点类型（14 种，从 30 个 skills 的分析框架提炼）─────────────

class NodeType(str, Enum):
    GOAL = "goal"                # 战略意图/愿景/北极星
    POSITION = "position"        # 竞争定位/战略姿态
    OPTION = "option"            # 可选路径/战略方案
    RESOURCE = "resource"        # 能力/资产/核心competence
    CONSTRAINT = "constraint"    # 环境约束/结构性限制
    TENSION = "tension"          # 矛盾/两难/悖论
    ASSUMPTION = "assumption"    # 隐含假设/未验证前提
    RISK = "risk"                # 失败轨迹/威胁
    SIGNAL = "signal"            # 验证信号/早期指标
    STAKEHOLDER = "stakeholder"  # 利益相关方/外部势力
    MECHANISM = "mechanism"      # 战略机制/杠杆手段
    EVIDENCE = "evidence"        # 数据/事实/对话证据
    PATTERN = "pattern"          # 战略模式/类型
    ACTION = "action"            # 具体下一步/实验/战术


# ── 边类型（14 种，从 skills 的关系逻辑提炼）──────────────────

class EdgeType(str, Enum):
    SUPPORTS = "supports"             # A 为 B 提供支撑
    CONTRADICTS = "contradicts"       # A 与 B 矛盾
    ENABLES = "enables"               # A 使 B 成为可能
    BLOCKS = "blocks"                 # A 阻碍 B
    DEPENDS_ON = "depends_on"         # A 的成立依赖 B
    VALIDATES = "validates"           # A 能验证 B 是否成立
    EVOLVES_FROM = "evolves_from"     # A 由 B 演化而来
    TRADEOFF = "tradeoff"             # A 和 B 互斥取舍
    MITIGATES = "mitigates"           # A 能缓解 B
    AMPLIFIES = "amplifies"           # A 会加剧 B
    FITS = "fits"                     # A 与 B 匹配/consonance
    COMPETES_WITH = "competes_with"   # A 与 B 竞争同一资源
    LEVERAGES = "leverages"           # A 放大 B 的效果
    SCOPES = "scopes"                 # A 限定 B 的适用范围
