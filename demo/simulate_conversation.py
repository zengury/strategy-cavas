"""
模拟一场完整的战略对话，生成 3D 图数据。

场景：一个大厂技术总监考虑是否离职创业做 AI 教育产品。
对话共 6 轮，逐步涌现节点和关系，覆盖多个 skill 的分析框架。
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schema import (
    GraphNode, GraphEdge, NodeType, EdgeType, GraphDiff,
)
from engine.canvas_state import CanvasStateManager

mgr = CanvasStateManager(store_path="demo/store")


# ════════════════════════════════════════════════════════════════
# 模拟对话轮次
# ════════════════════════════════════════════════════════════════

conversation = []


def simulate_turn(turn_num: int, user_text: str, coach_reply: str,
                  nodes: list[GraphNode], edges: list[GraphEdge]):
    """模拟一轮对话：添加节点和边。"""
    conversation.append({"turn": turn_num, "user": user_text, "coach": coach_reply})
    diff = GraphDiff(added_nodes=nodes, added_edges=edges)
    mgr.apply_diff(diff)
    print(f"Turn {turn_num}: +{len(nodes)} nodes, +{len(edges)} edges")


# ── Turn 1: 用户提出困惑 ────────────────────────────────────────
# Skills: icarus-paradox-diagnosis, decision-bias-detection

n_tension_1 = GraphNode(
    node_id="t1_tension",
    node_type=NodeType.TENSION,
    label="创业冲动 vs 家庭稳定",
    content="在大厂做到技术总监，但感觉增长天花板明显；同时家里刚有孩子，经济压力大",
    source_turn_id="turn_1",
    source_skill="icarus-paradox-diagnosis",
    confidence=0.9,
)

n_option_stay = GraphNode(
    node_id="t1_stay",
    node_type=NodeType.OPTION,
    label="留在大厂",
    content="继续在当前公司做技术总监，稳定收入，但成长空间有限",
    source_turn_id="turn_1",
    confidence=0.7,
)

n_option_startup = GraphNode(
    node_id="t1_startup",
    node_type=NodeType.OPTION,
    label="离职创业",
    content="做 AI 教育产品，利用自己的技术和教育行业认知",
    source_turn_id="turn_1",
    confidence=0.6,
)

n_constraint_family = GraphNode(
    node_id="t1_family",
    node_type=NodeType.CONSTRAINT,
    label="家庭经济压力",
    content="孩子刚出生，房贷压力，配偶希望稳定",
    source_turn_id="turn_1",
    confidence=0.95,
)

n_evidence_ceiling = GraphNode(
    node_id="t1_ceiling",
    node_type=NodeType.EVIDENCE,
    label="大厂天花板",
    content="用户明确感到在当前公司的技术总监位置上增长空间有限，过去一年没有新挑战",
    source_turn_id="turn_1",
    confidence=0.85,
)

simulate_turn(1,
    "我在一家大厂做技术总监，做了三年了。最近一直在想要不要出来做 AI 教育方面的创业，但是家里刚有了孩子，很纠结。",
    "你的纠结核心其实不是'创业好不好'，而是'在这个人生节点，我能承受多大的不确定性'...",
    nodes=[n_tension_1, n_option_stay, n_option_startup, n_constraint_family, n_evidence_ceiling],
    edges=[
        GraphEdge(edge_id="e1_1", edge_type=EdgeType.TRADEOFF,
                  source_id="t1_stay", target_id="t1_startup",
                  label="互斥选择", strength=0.9, source_turn_id="turn_1"),
        GraphEdge(edge_id="e1_2", edge_type=EdgeType.BLOCKS,
                  source_id="t1_family", target_id="t1_startup",
                  label="经济压力限制创业", strength=0.7, source_turn_id="turn_1"),
        GraphEdge(edge_id="e1_3", edge_type=EdgeType.SUPPORTS,
                  source_id="t1_ceiling", target_id="t1_tension",
                  label="天花板加剧纠结", strength=0.8, source_turn_id="turn_1"),
    ],
)

# ── Turn 2: 探索资源和能力 ──────────────────────────────────────
# Skills: strategic-resource-evaluation (VRIS), resource-leverage-strategies

n_resource_tech = GraphNode(
    node_id="t2_tech",
    node_type=NodeType.RESOURCE,
    label="AI 技术能力",
    content="在大模型微调、RAG 架构方面有深度积累，团队管理经验",
    source_turn_id="turn_2",
    source_skill="strategic-resource-evaluation",
    confidence=0.85,
)

n_resource_network = GraphNode(
    node_id="t2_network",
    node_type=NodeType.RESOURCE,
    label="教育行业人脉",
    content="之前做过教育科技项目，认识一些校长和培训机构负责人",
    source_turn_id="turn_2",
    source_skill="strategic-resource-evaluation",
    confidence=0.7,
)

n_resource_savings = GraphNode(
    node_id="t2_savings",
    node_type=NodeType.RESOURCE,
    label="积蓄 runway",
    content="大约有 18 个月的生活费积蓄",
    source_turn_id="turn_2",
    source_skill="resource-leverage-strategies",
    confidence=0.9,
)

n_mechanism_leverage = GraphNode(
    node_id="t2_leverage",
    node_type=NodeType.MECHANISM,
    label="资源杠杆: 先兼职验证",
    content="利用业余时间先做 MVP，不辞职，用最小资源验证市场需求",
    source_turn_id="turn_2",
    source_skill="resource-leverage-strategies",
    confidence=0.75,
)

simulate_turn(2,
    "我的技术还是比较强的，在 AI 和大模型方面有很深的积累。之前也做过一个教育科技的项目，认识一些行业里的人。存款大概够用一年半。",
    "你的资源盘点其实比你想象的丰富——但问题是这些资源的'杠杆率'可以很高。你不需要一步到位地'辞职创业'...",
    nodes=[n_resource_tech, n_resource_network, n_resource_savings, n_mechanism_leverage],
    edges=[
        GraphEdge(edge_id="e2_1", edge_type=EdgeType.ENABLES,
                  source_id="t2_tech", target_id="t1_startup",
                  label="核心技术使创业可行", strength=0.85, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_2", edge_type=EdgeType.ENABLES,
                  source_id="t2_network", target_id="t1_startup",
                  label="人脉降低获客成本", strength=0.6, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_3", edge_type=EdgeType.SCOPES,
                  source_id="t2_savings", target_id="t1_startup",
                  label="18 月 runway 限定时间窗口", strength=0.9, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_4", edge_type=EdgeType.MITIGATES,
                  source_id="t2_leverage", target_id="t1_family",
                  label="兼职模式缓解经济压力", strength=0.8, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_5", edge_type=EdgeType.LEVERAGES,
                  source_id="t2_leverage", target_id="t2_tech",
                  label="杠杆放大技术优势", strength=0.7, source_turn_id="turn_2"),
    ],
)

# ── Turn 3: 分析竞争格局 ───────────────────────────────────────
# Skills: strategic-positioning-porter, competitive-game-theory-analysis

n_position_market = GraphNode(
    node_id="t3_market",
    node_type=NodeType.POSITION,
    label="AI 教育赛道定位",
    content="当前 AI 教育市场高度碎片化，大厂（字节、网易）在通用教育，但垂直领域（编程+AI 素养）缺乏深度产品",
    source_turn_id="turn_3",
    source_skill="strategic-positioning-porter",
    confidence=0.7,
)

n_stakeholder_bigtech = GraphNode(
    node_id="t3_bigtech",
    node_type=NodeType.STAKEHOLDER,
    label="大厂竞争者",
    content="字节跳动、网易有道等，资金充裕但在 AI 素养教育方面不够深",
    source_turn_id="turn_3",
    source_skill="competitive-game-theory-analysis",
    confidence=0.8,
)

n_risk_compete = GraphNode(
    node_id="t3_compete",
    node_type=NodeType.RISK,
    label="大厂降维打击",
    content="如果 AI 素养教育被大厂看到并快速投入，小团队可能被碾压",
    source_turn_id="turn_3",
    source_skill="competitive-game-theory-analysis",
    confidence=0.65,
)

n_assumption_niche = GraphNode(
    node_id="t3_niche",
    node_type=NodeType.ASSUMPTION,
    label="垂直细分有护城河",
    content="假设：在 AI 素养教育的垂直细分领域，深度内容和社区粘性可以构建大厂难以复制的护城河",
    source_turn_id="turn_3",
    source_skill="strategic-positioning-porter",
    confidence=0.55,
)

simulate_turn(3,
    "AI 教育现在挺热的，字节和网易都在做。但我觉得他们做的都比较浅，真正的 AI 素养教育没人做好。我想做更深度的内容。",
    "你看到了一个真实的缝隙——但问题是这个缝隙是否足够宽、足够深，能让你在大厂注意到之前建好壁垒...",
    nodes=[n_position_market, n_stakeholder_bigtech, n_risk_compete, n_assumption_niche],
    edges=[
        GraphEdge(edge_id="e3_1", edge_type=EdgeType.COMPETES_WITH,
                  source_id="t1_startup", target_id="t3_bigtech",
                  label="争夺 AI 教育市场", strength=0.7, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_2", edge_type=EdgeType.AMPLIFIES,
                  source_id="t3_bigtech", target_id="t3_compete",
                  label="大厂入场加剧碾压风险", strength=0.8, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_3", edge_type=EdgeType.DEPENDS_ON,
                  source_id="t3_market", target_id="t3_niche",
                  label="定位依赖细分护城河假设", strength=0.9, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_4", edge_type=EdgeType.MITIGATES,
                  source_id="t3_niche", target_id="t3_compete",
                  label="护城河缓解碾压风险", strength=0.6, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_5", edge_type=EdgeType.FITS,
                  source_id="t2_tech", target_id="t3_market",
                  label="技术能力匹配市场定位", strength=0.8, source_turn_id="turn_3"),
    ],
)

# ── Turn 4: 压力测试假设 ───────────────────────────────────────
# Skills: decision-bias-detection, chaos-theory-strategic-management

n_pattern_bias = GraphNode(
    node_id="t4_bias",
    node_type=NodeType.PATTERN,
    label="乐观偏差",
    content="识别到用户可能存在'乐观偏差'——过度相信自己的技术优势能转化为商业成功",
    source_turn_id="turn_4",
    source_skill="decision-bias-detection",
    confidence=0.75,
)

n_assumption_convert = GraphNode(
    node_id="t4_convert",
    node_type=NodeType.ASSUMPTION,
    label="技术能力=商业成功",
    content="隐含假设：深度技术能力能直接转化为教育产品的商业成功",
    source_turn_id="turn_4",
    source_skill="decision-bias-detection",
    confidence=0.4,
)

n_signal_validate = GraphNode(
    node_id="t4_signal",
    node_type=NodeType.SIGNAL,
    label="付费验证信号",
    content="找 10 个目标用户，收费 199 做一个 4 周的 AI 素养小班课。如果 7 人以上愿意付费，说明需求真实",
    source_turn_id="turn_4",
    source_skill="chaos-theory-strategic-management",
    confidence=0.8,
)

n_risk_chaos = GraphNode(
    node_id="t4_chaos",
    node_type=NodeType.RISK,
    label="AI 政策不确定性",
    content="AI 教育领域可能面临政策监管的突然变化（如内容审查、牌照要求）",
    source_turn_id="turn_4",
    source_skill="chaos-theory-strategic-management",
    confidence=0.6,
)

simulate_turn(4,
    "我觉得我对 AI 的理解比市面上大部分教育从业者都深，这是我的核心优势。",
    "这可能是真的——但也可能是你的盲区。'我比别人强'这个判断本身需要被验证，否则就是乐观偏差在驱动决策...",
    nodes=[n_pattern_bias, n_assumption_convert, n_signal_validate, n_risk_chaos],
    edges=[
        GraphEdge(edge_id="e4_1", edge_type=EdgeType.CONTRADICTS,
                  source_id="t4_bias", target_id="t4_convert",
                  label="乐观偏差质疑转化假设", strength=0.8, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_2", edge_type=EdgeType.VALIDATES,
                  source_id="t4_signal", target_id="t4_convert",
                  label="付费小班课验证转化假设", strength=0.85, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_3", edge_type=EdgeType.VALIDATES,
                  source_id="t4_signal", target_id="t3_niche",
                  label="同时验证细分市场假设", strength=0.7, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_4", edge_type=EdgeType.AMPLIFIES,
                  source_id="t4_chaos", target_id="t3_compete",
                  label="政策不确定性叠加竞争风险", strength=0.5, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_5", edge_type=EdgeType.DEPENDS_ON,
                  source_id="t1_startup", target_id="t4_convert",
                  label="创业选项依赖转化假设", strength=0.9, source_turn_id="turn_4"),
    ],
)

# ── Turn 5: 设计行动路径 ───────────────────────────────────────
# Skills: incremental-market-domination-strategy, strategic-alliance-management

n_action_mvp = GraphNode(
    node_id="t5_mvp",
    node_type=NodeType.ACTION,
    label="4 周小班课 MVP",
    content="不辞职，用 2 周准备课程内容，在教育行业人脉圈发起 10 人付费小班课（199 元/人）",
    source_turn_id="turn_5",
    source_skill="incremental-market-domination-strategy",
    confidence=0.85,
)

n_action_signal_check = GraphNode(
    node_id="t5_check",
    node_type=NodeType.ACTION,
    label="6 周后决策检查点",
    content="小班课结束后评估：续报率、NPS、用户反馈。如果数据正面，启动第二期并考虑兼职转全职时间表",
    source_turn_id="turn_5",
    source_skill="incremental-market-domination-strategy",
    confidence=0.8,
)

n_mechanism_alliance = GraphNode(
    node_id="t5_alliance",
    node_type=NodeType.MECHANISM,
    label="联盟: 找教育合伙人",
    content="找一个有教育行业运营经验的合伙人，补齐非技术短板，降低单人风险",
    source_turn_id="turn_5",
    source_skill="strategic-alliance-management",
    confidence=0.7,
)

n_signal_nps = GraphNode(
    node_id="t5_nps",
    node_type=NodeType.SIGNAL,
    label="NPS > 50 为绿灯",
    content="如果首期小班课 NPS > 50 且续报意愿 > 60%，认为产品方向正确",
    source_turn_id="turn_5",
    confidence=0.8,
)

simulate_turn(5,
    "你说得对，我确实可能太乐观了。那你觉得我现在最应该做什么？",
    "最聪明的一步是'不下牌桌的探测'——你不需要辞职就能验证最关键的假设...",
    nodes=[n_action_mvp, n_action_signal_check, n_mechanism_alliance, n_signal_nps],
    edges=[
        GraphEdge(edge_id="e5_1", edge_type=EdgeType.VALIDATES,
                  source_id="t5_mvp", target_id="t4_convert",
                  label="MVP 验证技术→商业转化", strength=0.9, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_2", edge_type=EdgeType.DEPENDS_ON,
                  source_id="t5_check", target_id="t5_mvp",
                  label="检查点依赖 MVP 完成", strength=1.0, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_3", edge_type=EdgeType.MITIGATES,
                  source_id="t5_alliance", target_id="t3_compete",
                  label="合伙人补齐短板降低竞争风险", strength=0.6, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_4", edge_type=EdgeType.ENABLES,
                  source_id="t5_alliance", target_id="t5_mvp",
                  label="合伙人加速 MVP 执行", strength=0.7, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_5", edge_type=EdgeType.VALIDATES,
                  source_id="t5_nps", target_id="t3_niche",
                  label="NPS 验证细分市场价值", strength=0.85, source_turn_id="turn_5"),
    ],
)

# ── Turn 6: 形成临时战略判断 ────────────────────────────────────
# Skills: holistic-systems-perspective, miles-snow-strategic-typology

n_goal_north = GraphNode(
    node_id="t6_goal",
    node_type=NodeType.GOAL,
    label="成为 AI 素养教育领导者",
    content="3 年愿景：成为中国 AI 素养教育的头部品牌，从小班课开始，逐步扩展到平台",
    source_turn_id="turn_6",
    source_skill="holistic-systems-perspective",
    confidence=0.55,
)

n_pattern_analyzer = GraphNode(
    node_id="t6_analyzer",
    node_type=NodeType.PATTERN,
    label="分析者战略模式",
    content="当前最佳战略模式是 Miles-Snow 的 Analyzer：在大厂保持稳定（Defender 面），同时有限度地探索新机会（Prospector 面）",
    source_turn_id="turn_6",
    source_skill="miles-snow-strategic-typology",
    confidence=0.8,
)

n_evidence_synthesis = GraphNode(
    node_id="t6_synthesis",
    node_type=NodeType.EVIDENCE,
    label="系统综合判断",
    content="综合看：技术能力强（资源优势）、市场缝隙存在（定位机会）、但转化假设未验证（关键风险）、家庭约束真实（刚性限制）→ 最优路径是渐进式验证",
    source_turn_id="turn_6",
    source_skill="holistic-systems-perspective",
    confidence=0.85,
)

simulate_turn(6,
    "这个方案我很认可。先做小班课验证，不冒险。如果数据好再考虑下一步。那我的长期愿景应该是什么？",
    "你的愿景不需要现在就精确——但方向是清楚的。你正在用最聪明的方式接近它：不是赌博式的 all-in，而是像一个 Analyzer...",
    nodes=[n_goal_north, n_pattern_analyzer, n_evidence_synthesis],
    edges=[
        GraphEdge(edge_id="e6_1", edge_type=EdgeType.SUPPORTS,
                  source_id="t6_synthesis", target_id="t2_leverage",
                  label="综合判断支持兼职验证策略", strength=0.9, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_2", edge_type=EdgeType.FITS,
                  source_id="t6_analyzer", target_id="t1_tension",
                  label="Analyzer 模式匹配当前两难", strength=0.85, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_3", edge_type=EdgeType.ENABLES,
                  source_id="t5_mvp", target_id="t6_goal",
                  label="MVP 是通往愿景的第一步", strength=0.7, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_4", edge_type=EdgeType.SCOPES,
                  source_id="t6_analyzer", target_id="t1_startup",
                  label="Analyzer 模式限定创业为渐进式", strength=0.8, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_5", edge_type=EdgeType.DEPENDS_ON,
                  source_id="t6_goal", target_id="t4_convert",
                  label="愿景依赖技术→商业转化成立", strength=0.85, source_turn_id="turn_6"),
    ],
)


# ════════════════════════════════════════════════════════════════
# 输出结果
# ════════════════════════════════════════════════════════════════

vis_data = mgr.graph.to_vis_data()

# 添加对话数据
output = {
    "conversation": conversation,
    "graph": vis_data,
    "stats": {
        "total_nodes": len(vis_data["nodes"]),
        "total_edges": len(vis_data["links"]),
        "node_types": {},
        "edge_types": {},
    },
}

for n in vis_data["nodes"]:
    t = n["node_type"]
    output["stats"]["node_types"][t] = output["stats"]["node_types"].get(t, 0) + 1

for e in vis_data["links"]:
    t = e["edge_type"]
    output["stats"]["edge_types"][t] = output["stats"]["edge_types"].get(t, 0) + 1

# 写入文件
os.makedirs("demo", exist_ok=True)
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_data.json")
with open(output_path, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n=== Simulation Complete ===")
print(f"Nodes: {output['stats']['total_nodes']}")
print(f"Edges: {output['stats']['total_edges']}")
print(f"Node types: {json.dumps(output['stats']['node_types'], indent=2)}")
print(f"Edge types: {json.dumps(output['stats']['edge_types'], indent=2)}")
print(f"\nOutput: {output_path}")
