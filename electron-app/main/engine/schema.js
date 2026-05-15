const crypto = require("crypto");

const STAGE = Object.freeze({
  EXPLORE: "explore", CONVERGE: "converge", STRESS_TEST: "stress_test",
  COMMIT: "commit", REVIEW: "review",
});

const NodeType = Object.freeze({
  goal: "goal", position: "position", option: "option", mechanism: "mechanism",
  resource: "resource", constraint: "constraint", evidence: "evidence",
  tension: "tension", assumption: "assumption", risk: "risk", signal: "signal",
  action: "action", pattern: "pattern", stakeholder: "stakeholder",
});

const EdgeType = Object.freeze({
  supports: "supports", contradicts: "contradicts", enables: "enables",
  blocks: "blocks", depends_on: "depends_on", validates: "validates",
  evolves_from: "evolves_from", tradeoff: "tradeoff", mitigates: "mitigates",
  amplifies: "amplifies", fits: "fits", competes_with: "competes_with",
  leverages: "leverages", scopes: "scopes",
});

const NODE_SPATIAL_BIAS = {
  goal: [0.8, 0.3, 0], position: [0.2, 0.2, 0], option: [0.3, 0, 0.1],
  resource: [-0.2, 0.3, 0.2], constraint: [-0.2, -0.2, 0.5],
  tension: [0, -0.4, 0], assumption: [0.1, -0.6, 0.3], risk: [0.2, -0.5, 0.2],
  signal: [-0.4, 0.5, 0.2], stakeholder: [0, 0, 0.7], mechanism: [0, 0.1, 0.1],
  evidence: [-0.5, 0.6, 0.4], pattern: [0.5, 0.5, 0.3], action: [-0.7, 0.1, 0.1],
};

const NODE_COLORS = {
  goal: "#FFD700", position: "#4A90D9", option: "#50C878", resource: "#9B59B6",
  constraint: "#E74C3C", tension: "#FF6B35", assumption: "#F39C12", risk: "#C0392B",
  signal: "#00BCD4", stakeholder: "#8D6E63", mechanism: "#7E57C2", evidence: "#26A69A",
  pattern: "#EC407A", action: "#66BB6A",
};

const EDGE_COLORS = {
  supports: "#4CAF50", contradicts: "#F44336", enables: "#2196F3", blocks: "#FF5722",
  depends_on: "#9E9E9E", validates: "#00BCD4", evolves_from: "#AB47BC", tradeoff: "#FF9800",
  mitigates: "#8BC34A", amplifies: "#E91E63", fits: "#3F51B5", competes_with: "#FF5252",
  leverages: "#7C4DFF", scopes: "#607D8B",
};

const NODE_TYPE_TO_ZONE = {
  goal: "north_star", position: "context", option: "options", resource: "context",
  constraint: "context", tension: "tradeoffs", assumption: "assumptions",
  risk: "signals", signal: "signals", stakeholder: "context", mechanism: "options",
  evidence: "context", pattern: "context", action: "next_moves",
};

const CANVAS_ZONES = ["north_star", "context", "options", "tradeoffs", "assumptions", "signals", "next_moves"];

function uid(len) { return crypto.randomUUID().replace(/-/g, "").slice(0, len); }

function createGraphNode(o = {}) {
  return { node_id: uid(8), node_type: "evidence", label: "", content: "",
    source_turn_id: "", source_evidence: "", source_skill: "",
    confidence: 0.8, weight: 1.0, locked: false, status: "active",
    x: 0, y: 0, z: 0,
    created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...o };
}

function createGraphEdge(o = {}) {
  return { edge_id: uid(8), edge_type: "supports", source_id: "", target_id: "",
    label: "", strength: 1.0, source_turn_id: "",
    created_at: new Date().toISOString(), ...o };
}

function createConversationTurn(o = {}) {
  return { turn_id: uid(12), speaker: "user", text: "", timestamp: new Date().toISOString(),
    intent: null, sentiment: null, stage: STAGE.EXPLORE, ...o };
}

function nodeToDict(n) {
  return { id: n.node_id, node_type: n.node_type, label: n.label, content: n.content,
    source_turn_id: n.source_turn_id, source_evidence: n.source_evidence,
    source_skill: n.source_skill, confidence: n.confidence, locked: n.locked,
    status: n.status, x: n.x, y: n.y, z: n.z, weight: n.weight,
    color: NODE_COLORS[n.node_type] || "#999", created_at: n.created_at, updated_at: n.updated_at };
}

function edgeToDict(e) {
  return { id: e.edge_id, edge_type: e.edge_type, source: e.source_id, target: e.target_id,
    label: e.label, strength: e.strength, color: EDGE_COLORS[e.edge_type] || "#999" };
}

class CanvasGraph {
  constructor() { this.nodes = new Map(); this.edges = new Map(); this.version = 0; this.updated_at = new Date().toISOString(); }
  activeNodes() { return [...this.nodes.values()].filter(n => n.status === "active"); }
  activeEdges() {
    const ids = new Set(this.activeNodes().map(n => n.node_id));
    return [...this.edges.values()].filter(e => ids.has(e.source_id) && ids.has(e.target_id));
  }
  toVisData() { return { nodes: this.activeNodes().map(nodeToDict), links: this.activeEdges().map(edgeToDict) }; }
  toSummary() {
    const m = {};
    for (const n of this.activeNodes()) {
      if (!m[n.node_type]) m[n.node_type] = [];
      m[n.node_type].push({ id: n.node_id, label: n.label, confidence: n.confidence, locked: n.locked });
    }
    return m;
  }
}

module.exports = { STAGE, NodeType, EdgeType, NODE_SPATIAL_BIAS, NODE_COLORS, EDGE_COLORS,
  NODE_TYPE_TO_ZONE, CANVAS_ZONES, CanvasGraph,
  createGraphNode, createGraphEdge, createConversationTurn, nodeToDict, edgeToDict };
