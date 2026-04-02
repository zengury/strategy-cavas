"""
模拟一场完整的战略对话，生成 3D 图数据。

场景：一个金融科技公司的产品总监考虑是否加入朋友的气候科技创业公司担任联合创始人。
对话共 6 轮，故事模式展开，逐步涌现节点和关系。
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

conversation = []


def simulate_turn(turn_num, user_text, coach_reply, nodes, edges):
    conversation.append({"turn": turn_num, "user": user_text, "coach": coach_reply})
    diff = GraphDiff(added_nodes=nodes, added_edges=edges)
    mgr.apply_diff(diff)
    print(f"Turn {turn_num}: +{len(nodes)} nodes, +{len(edges)} edges")


# ══ Turn 1: 她描述了内心的纠结 ══════════════════════════════════

simulate_turn(1,
    "我在一家金融科技公司做了五年产品总监，马上有机会晋升VP。但我大学同学刚拿到一轮融资，做碳中和SaaS平台，邀请我做联合创始人。我两个孩子，还有房贷，但我真的对可持续发展有很深的热情。我每天都在想这件事，睡不着觉。",
    "你失眠不是因为选不了，而是因为两个选择分别代表了你内心两个不同版本的自己——一个追求安全感和社会认可，另一个追求意义感和创造力。我们先不急着选，先把你的纠结拆开来看。",
    nodes=[
        GraphNode(node_id="t1_tension", node_type=NodeType.TENSION,
            label="职业安全 vs 人生意义",
            content="在金融科技已建立稳固地位即将晋升VP，但内心对气候科技的热情让她无法安于现状",
            source_turn_id="turn_1", source_skill="icarus-paradox-diagnosis",
            confidence=0.92, weight=1.9),
        GraphNode(node_id="t1_stay", node_type=NodeType.OPTION,
            label="留任冲刺VP",
            content="继续在金融科技公司，争取VP晋升，稳定收入和职业阶梯",
            source_turn_id="turn_1", confidence=0.75, weight=1.2),
        GraphNode(node_id="t1_join", node_type=NodeType.OPTION,
            label="加入气候科技创业",
            content="作为联合创始人加入朋友的碳中和SaaS公司，从零开始但追随热情",
            source_turn_id="turn_1", confidence=0.55, weight=1.6),
        GraphNode(node_id="t1_family", node_type=NodeType.CONSTRAINT,
            label="家庭经济刚性约束",
            content="两个孩子的教育费用和房贷构成每月固定支出约3.5万，不能中断",
            source_turn_id="turn_1", source_skill="icarus-paradox-diagnosis",
            confidence=0.95, weight=1.5),
        GraphNode(node_id="t1_passion", node_type=NodeType.EVIDENCE,
            label="可持续发展热情",
            content="大学主修环境科学，工作之余持续关注碳交易政策，参加气候峰会志愿者三年",
            source_turn_id="turn_1", source_skill="decision-bias-detection",
            confidence=0.88, weight=1.1),
    ],
    edges=[
        GraphEdge(edge_id="e1_1", edge_type=EdgeType.TRADEOFF,
            source_id="t1_stay", target_id="t1_join",
            label="两条路径互斥", strength=0.9, source_turn_id="turn_1"),
        GraphEdge(edge_id="e1_2", edge_type=EdgeType.BLOCKS,
            source_id="t1_family", target_id="t1_join",
            label="家庭经济压力限制创业选择", strength=0.75, source_turn_id="turn_1"),
        GraphEdge(edge_id="e1_3", edge_type=EdgeType.SUPPORTS,
            source_id="t1_passion", target_id="t1_tension",
            label="热情加深内心纠结", strength=0.85, source_turn_id="turn_1"),
    ],
)


# ══ Turn 2: 盘点她的资源和优势 ══════════════════════════════════

simulate_turn(2,
    "其实我在金融科技这五年积累了很多。我负责过碳金融产品线的从0到1，团队从3人带到40人。我对碳交易的合规框架非常熟悉，而且我们公司和几个大型能源企业有合作关系。存款大概能支撑一年。",
    "你的资源比你意识到的更有战略价值。关键不是'你有什么'，而是'哪些资源在新赛道上有杠杆效应'。你的碳金融经验不是离开金融科技就消失的——它恰恰是气候科技最稀缺的能力。",
    nodes=[
        GraphNode(node_id="t2_carbon_exp", node_type=NodeType.RESOURCE,
            label="碳金融产品经验",
            content="负责碳金融产品线从0到1，深度理解碳交易合规框架和市场机制",
            source_turn_id="turn_2", source_skill="strategic-resource-evaluation",
            confidence=0.9, weight=1.4),
        GraphNode(node_id="t2_team_mgmt", node_type=NodeType.RESOURCE,
            label="规模化团队管理能力",
            content="五年内将团队从3人扩展到40人，有成熟的招聘和管理方法论",
            source_turn_id="turn_2", source_skill="strategic-resource-evaluation",
            confidence=0.85, weight=1.0),
        GraphNode(node_id="t2_energy_network", node_type=NodeType.RESOURCE,
            label="能源企业客户网络",
            content="通过现有公司与多家大型能源企业建立了合作关系，这些关系可以迁移",
            source_turn_id="turn_2", source_skill="resource-leverage-strategies",
            confidence=0.65, weight=1.3),
        GraphNode(node_id="t2_leverage", node_type=NodeType.MECHANISM,
            label="资源杠杆：碳金融×气候科技",
            content="碳金融的合规经验在气候科技赛道极度稀缺，可以作为差异化定位的核心杠杆",
            source_turn_id="turn_2", source_skill="resource-leverage-strategies",
            confidence=0.8, weight=1.7),
    ],
    edges=[
        GraphEdge(edge_id="e2_1", edge_type=EdgeType.ENABLES,
            source_id="t2_carbon_exp", target_id="t1_join",
            label="碳金融经验使创业可行", strength=0.85, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_2", edge_type=EdgeType.LEVERAGES,
            source_id="t2_leverage", target_id="t2_carbon_exp",
            label="杠杆放大碳金融经验价值", strength=0.8, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_3", edge_type=EdgeType.ENABLES,
            source_id="t2_energy_network", target_id="t1_join",
            label="客户网络降低获客成本", strength=0.6, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_4", edge_type=EdgeType.MITIGATES,
            source_id="t2_leverage", target_id="t1_family",
            label="高价值定位可能缩短回本周期", strength=0.55, source_turn_id="turn_2"),
        GraphEdge(edge_id="e2_5", edge_type=EdgeType.FITS,
            source_id="t2_carbon_exp", target_id="t1_passion",
            label="专业经验与个人热情高度匹配", strength=0.9, source_turn_id="turn_2"),
    ],
)


# ══ Turn 3: 分析气候科技的市场格局 ══════════════════════════════

simulate_turn(3,
    "气候科技现在确实很热。但我看到很多创业公司拿了钱之后做的东西很同质化，都是碳核算SaaS。我朋友想做的是碳交易合规自动化，面向出海企业的CBAM合规。这个赛道竞争没那么激烈，但客单价高。",
    "你观察到了一个结构性机会——CBAM合规是监管驱动的刚需市场，不是'锦上添花'。但你要警惕两个陷阱：一是时间窗口可能很窄，大厂一旦看到就会入场；二是合规类产品的壁垒不在技术，在信任。",
    nodes=[
        GraphNode(node_id="t3_position", node_type=NodeType.POSITION,
            label="CBAM合规自动化赛道",
            content="欧盟碳边境调节机制（CBAM）要求出海企业合规申报，市场碎片化，客单价高，竞争尚不激烈",
            source_turn_id="turn_3", source_skill="strategic-positioning-porter",
            confidence=0.72, weight=1.3),
        GraphNode(node_id="t3_competitor", node_type=NodeType.STAKEHOLDER,
            label="潜在大厂竞争者",
            content="SAP、Salesforce等大厂有能力快速推出合规模块，一旦市场被验证就会入场",
            source_turn_id="turn_3", source_skill="competitive-game-theory-analysis",
            confidence=0.78, weight=1.1),
        GraphNode(node_id="t3_window_risk", node_type=NodeType.RISK,
            label="时间窗口风险",
            content="CBAM合规需求在2026-2028集中爆发，如果不能在窗口期建立客户基础，后发者可能被大厂碾压",
            source_turn_id="turn_3", source_skill="competitive-game-theory-analysis",
            confidence=0.7, weight=1.4),
        GraphNode(node_id="t3_trust", node_type=NodeType.RISK,
            label="合规信任壁垒",
            content="合规类产品的核心壁垒不是技术而是客户信任，新创公司在这方面天然劣势",
            source_turn_id="turn_3", source_skill="strategic-positioning-porter",
            confidence=0.68, weight=1.2),
    ],
    edges=[
        GraphEdge(edge_id="e3_1", edge_type=EdgeType.COMPETES_WITH,
            source_id="t1_join", target_id="t3_competitor",
            label="创业公司与大厂争夺合规市场", strength=0.7, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_2", edge_type=EdgeType.AMPLIFIES,
            source_id="t3_competitor", target_id="t3_window_risk",
            label="大厂入场加速窗口关闭", strength=0.8, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_3", edge_type=EdgeType.MITIGATES,
            source_id="t2_carbon_exp", target_id="t3_trust",
            label="碳金融背景增强客户信任", strength=0.75, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_4", edge_type=EdgeType.FITS,
            source_id="t2_energy_network", target_id="t3_position",
            label="能源客户网络匹配CBAM目标客户", strength=0.7, source_turn_id="turn_3"),
        GraphEdge(edge_id="e3_5", edge_type=EdgeType.SCOPES,
            source_id="t3_window_risk", target_id="t1_join",
            label="时间窗口限定决策紧迫性", strength=0.85, source_turn_id="turn_3"),
    ],
)


# ══ Turn 4: 教练挑战她的假设 ════════════════════════════════════

simulate_turn(4,
    "我觉得我最大的优势就是既懂金融又懂碳市场，市场上这样的人很少。而且我朋友的技术团队很强，我负责商业化应该很合适。",
    "我要泼一盆冷水。'我是稀缺人才'这个判断本身可能是确认偏误——你在自己的圈子里觉得稀缺，但CBAM合规是全球赛道，欧洲有大量碳市场老手。另外，'技术很强就能做好产品'这个假设需要验证——合规产品的难点在于理解几十个国家的监管差异，不是算法。",
    nodes=[
        GraphNode(node_id="t4_bias", node_type=NodeType.PATTERN,
            label="确认偏误风险",
            content="可能过度高估自身稀缺性，在中国市场确实稀缺，但全球CBAM赛道有大量欧洲碳市场专家",
            source_turn_id="turn_4", source_skill="decision-bias-detection",
            confidence=0.72, weight=1.3),
        GraphNode(node_id="t4_assumption_tech", node_type=NodeType.ASSUMPTION,
            label="技术强≠产品强",
            content="隐含假设：朋友的技术团队强就能做出好的合规产品。但合规产品的难点在监管理解而非算法",
            source_turn_id="turn_4", source_skill="decision-bias-detection",
            confidence=0.38, weight=1.6),
        GraphNode(node_id="t4_assumption_rare", node_type=NodeType.ASSUMPTION,
            label="我的稀缺性是全局的",
            content="假设自己的碳金融+产品管理复合背景在全球CBAM赛道同样稀缺，需要市场验证",
            source_turn_id="turn_4", source_skill="chaos-theory-strategic-management",
            confidence=0.45, weight=1.4),
        GraphNode(node_id="t4_signal", node_type=NodeType.SIGNAL,
            label="客户付费意愿验证",
            content="找5家目标客户做付费POC测试，如果3家以上愿意签年度合同，说明产品方向正确且信任可建立",
            source_turn_id="turn_4", source_skill="chaos-theory-strategic-management",
            confidence=0.82, weight=1.3),
    ],
    edges=[
        GraphEdge(edge_id="e4_1", edge_type=EdgeType.CONTRADICTS,
            source_id="t4_bias", target_id="t4_assumption_rare",
            label="确认偏误质疑稀缺性假设", strength=0.8, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_2", edge_type=EdgeType.VALIDATES,
            source_id="t4_signal", target_id="t4_assumption_tech",
            label="POC可验证产品假设", strength=0.85, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_3", edge_type=EdgeType.DEPENDS_ON,
            source_id="t1_join", target_id="t4_assumption_tech",
            label="创业成功依赖产品假设", strength=0.9, source_turn_id="turn_4"),
        GraphEdge(edge_id="e4_4", edge_type=EdgeType.VALIDATES,
            source_id="t4_signal", target_id="t3_position",
            label="POC同时验证市场定位", strength=0.75, source_turn_id="turn_4"),
    ],
)


# ══ Turn 5: 设计具体行动路径 ════════════════════════════════════

simulate_turn(5,
    "你说得对，我确实可能太乐观了。那我现在能做什么来降低风险？我不想盲目辞职。",
    "最聪明的策略是'在职探测'——用你现在的平台资源来验证创业假设，而不是赌上一切。你可以和朋友约定一个3个月的'影子合伙人'期，利用周末和晚上参与关键商业决策和客户拜访，同时保留你的收入和VP机会。",
    nodes=[
        GraphNode(node_id="t5_shadow", node_type=NodeType.ACTION,
            label="3个月影子合伙人计划",
            content="与朋友约定3个月的兼职参与期，周末和晚上参与关键商业决策和客户拜访，保留全职工作",
            source_turn_id="turn_5", source_skill="incremental-market-domination-strategy",
            confidence=0.85, weight=1.8),
        GraphNode(node_id="t5_poc", node_type=NodeType.ACTION,
            label="5家企业POC验证",
            content="利用个人网络找5家出海企业做CBAM合规POC，验证付费意愿和产品方向",
            source_turn_id="turn_5", source_skill="incremental-market-domination-strategy",
            confidence=0.8, weight=1.5),
        GraphNode(node_id="t5_alliance", node_type=NodeType.MECHANISM,
            label="互补型合伙结构",
            content="与朋友明确分工：技术CTO+商业CEO模式，提前约定股权和退出条款",
            source_turn_id="turn_5", source_skill="strategic-alliance-management",
            confidence=0.7, weight=1.1),
        GraphNode(node_id="t5_signal_nps", node_type=NodeType.SIGNAL,
            label="决策检查点指标",
            content="3个月后评估：POC签约率>60%、客户续约意愿>70%、团队协作NPS>50则全职加入",
            source_turn_id="turn_5", source_skill="incremental-market-domination-strategy",
            confidence=0.78, weight=1.2),
    ],
    edges=[
        GraphEdge(edge_id="e5_1", edge_type=EdgeType.VALIDATES,
            source_id="t5_poc", target_id="t4_assumption_tech",
            label="POC验证产品假设", strength=0.9, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_2", edge_type=EdgeType.DEPENDS_ON,
            source_id="t5_signal_nps", target_id="t5_poc",
            label="决策指标依赖POC结果", strength=1.0, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_3", edge_type=EdgeType.MITIGATES,
            source_id="t5_shadow", target_id="t1_family",
            label="在职探测避免收入中断", strength=0.85, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_4", edge_type=EdgeType.MITIGATES,
            source_id="t5_alliance", target_id="t3_trust",
            label="清晰合伙结构降低合作风险", strength=0.65, source_turn_id="turn_5"),
        GraphEdge(edge_id="e5_5", edge_type=EdgeType.ENABLES,
            source_id="t5_shadow", target_id="t5_poc",
            label="影子期为POC提供时间", strength=0.8, source_turn_id="turn_5"),
    ],
)


# ══ Turn 6: 综合形成战略愿景 ════════════════════════════════════

simulate_turn(6,
    "这个方案太好了。我不用马上做选择，而是用行动来验证。如果3个月后数据支持，我就有信心了。那从更长远来看，我想做的到底是什么？",
    "你的愿景正在从模糊变得清晰：你不是想'加入一家创业公司'，你是想成为碳合规领域的定义者——用你金融科技的方法论重新定义企业如何合规。这个愿景不需要现在完美，但方向已经清楚了。你正在用最理性的方式追随热情。",
    nodes=[
        GraphNode(node_id="t6_goal", node_type=NodeType.GOAL,
            label="成为碳合规领域的标准定义者",
            content="3-5年愿景：用金融科技方法论重新定义全球企业碳合规方式，从CBAM切入逐步扩展到全球碳市场基础设施",
            source_turn_id="turn_6", source_skill="holistic-systems-perspective",
            confidence=0.58, weight=1.6),
        GraphNode(node_id="t6_analyzer", node_type=NodeType.PATTERN,
            label="Analyzer战略模式",
            content="当前最优战略是Miles-Snow的分析者模式：保持现有工作稳定性的同时有限度地探索新机会",
            source_turn_id="turn_6", source_skill="miles-snow-strategic-typology",
            confidence=0.82, weight=1.3),
        GraphNode(node_id="t6_synthesis", node_type=NodeType.EVIDENCE,
            label="系统综合判断",
            content="综合分析：碳金融经验高度匹配、市场窗口真实存在、但核心假设未验证、家庭约束刚性→最优路径是渐进式验证后决策",
            source_turn_id="turn_6", source_skill="holistic-systems-perspective",
            confidence=0.88, weight=1.7),
    ],
    edges=[
        GraphEdge(edge_id="e6_1", edge_type=EdgeType.SUPPORTS,
            source_id="t6_synthesis", target_id="t5_shadow",
            label="综合判断支持影子合伙策略", strength=0.9, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_2", edge_type=EdgeType.FITS,
            source_id="t6_analyzer", target_id="t1_tension",
            label="分析者模式化解当前两难", strength=0.85, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_3", edge_type=EdgeType.ENABLES,
            source_id="t5_poc", target_id="t6_goal",
            label="POC是通往愿景的第一步", strength=0.7, source_turn_id="turn_6"),
        GraphEdge(edge_id="e6_4", edge_type=EdgeType.DEPENDS_ON,
            source_id="t6_goal", target_id="t4_assumption_tech",
            label="愿景依赖产品假设成立", strength=0.85, source_turn_id="turn_6"),
    ],
)


# ════════════════════════════════════════════════════════════════
# 输出结果
# ════════════════════════════════════════════════════════════════

vis_data = mgr.graph.to_vis_data()

output = {
    "conversation": conversation,
    "graph": vis_data,
    "stats": {
        "total_nodes": len(vis_data["nodes"]),
        "total_edges": len(vis_data["links"]),
        "node_types": {},
        "edge_types": {},
    },
    "golden_phrases": [
        "你不是在选择公司，你是在选择你想成为的那个人。",
        "最聪明的冒险不是 all-in，而是在安全绳上探路。",
        "你的稀缺性不是一个事实，而是一个需要验证的假设。",
        "合规的壁垒不在代码里，在客户愿意把命运交给你的那个瞬间。",
    ],
    "named_concepts": [
        "影子合伙人", "确认偏误", "资源杠杆", "时间窗口",
        "在职探测", "Analyzer模式", "信任壁垒", "渐进式验证",
    ],
}

for n in vis_data["nodes"]:
    t = n["node_type"]
    output["stats"]["node_types"][t] = output["stats"]["node_types"].get(t, 0) + 1

for e in vis_data["links"]:
    t = e["edge_type"]
    output["stats"]["edge_types"][t] = output["stats"]["edge_types"].get(t, 0) + 1

# 写入两个位置
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)

for path in [
    os.path.join(base_dir, "graph_data.json"),
    os.path.join(project_dir, "web", "demo_graph.json"),
]:
    with open(path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Written: {path}")

print(f"\n=== Simulation Complete ===")
print(f"Nodes: {output['stats']['total_nodes']}")
print(f"Edges: {output['stats']['total_edges']}")
print(f"Node types: {json.dumps(output['stats']['node_types'], indent=2)}")
print(f"Edge types: {json.dumps(output['stats']['edge_types'], indent=2)}")
