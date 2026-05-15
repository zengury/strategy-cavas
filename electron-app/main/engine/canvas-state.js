const { CanvasGraph, createGraphNode, NodeType, NODE_SPATIAL_BIAS } = require("./schema");

const SPACE_SCALE = 200;
const JITTER = 40;

class CanvasStateManager {
  constructor() { this._graph = new CanvasGraph(); }
  get graph() { return this._graph; }

  addNode(node) {
    const bias = NODE_SPATIAL_BIAS[node.node_type] || [0, 0, 0];
    node.x = bias[0] * SPACE_SCALE + (Math.random() * 2 - 1) * JITTER;
    node.y = bias[1] * SPACE_SCALE + (Math.random() * 2 - 1) * JITTER;
    node.z = bias[2] * SPACE_SCALE + (Math.random() * 2 - 1) * JITTER;
    this._graph.nodes.set(node.node_id, node);
    this._graph.version += 1;
    this._graph.updated_at = new Date().toISOString();
    return node;
  }

  addEdge(edge) {
    if (!this._graph.nodes.has(edge.source_id) || !this._graph.nodes.has(edge.target_id)) return edge;
    this._graph.edges.set(edge.edge_id, edge);
    return edge;
  }

  applyDiff(diff) {
    for (const n of diff.added_nodes || []) this.addNode(n);
    for (const e of diff.added_edges || []) this.addEdge(e);
    for (const mod of diff.modified_nodes || []) {
      const node = this._graph.nodes.get(mod.node_id);
      if (node && !node.locked) { node[mod.field] = mod.new; node.updated_at = new Date().toISOString(); }
    }
    for (const nid of diff.invalidated_node_ids || []) {
      const node = this._graph.nodes.get(nid);
      if (node && !node.locked) node.status = "invalidated";
    }
    this._graph.version += 1;
    this._graph.updated_at = new Date().toISOString();
    return this._graph;
  }

  lockNode(id) { const n = this._graph.nodes.get(id); if (n) { n.locked = true; return true; } return false; }
  unlockNode(id) { const n = this._graph.nodes.get(id); if (n) { n.locked = false; return true; } return false; }

  parseLlmCanvasOutput(parsed, turnId) {
    const diff = { added_nodes: [], added_edges: [], modified_nodes: [], invalidated_node_ids: [] };
    const updates = parsed.canvas_updates || {};
    const zoneToType = {
      north_star: [NodeType.goal], context: [NodeType.position, NodeType.resource, NodeType.constraint, NodeType.stakeholder, NodeType.evidence, NodeType.pattern],
      options: [NodeType.option, NodeType.mechanism], tradeoffs: [NodeType.tension],
      assumptions: [NodeType.assumption], signals: [NodeType.signal, NodeType.risk], next_moves: [NodeType.action],
    };
    for (const [zone, items] of Object.entries(updates)) {
      if (!Array.isArray(items)) continue;
      const nodeType = (zoneToType[zone] || [NodeType.evidence])[0] || NodeType.evidence;
      for (const item of items) {
        if (!item || typeof item !== "object") continue;
        const action = item.action || "add";
        if (action === "invalidate") { if (item.node_id) diff.invalidated_node_ids.push(item.node_id); }
        else if (action === "modify") { if (item.node_id && item.content) diff.modified_nodes.push({ node_id: item.node_id, field: "content", new: item.content }); }
        else {
          if (!item.content) continue;
          diff.added_nodes.push(createGraphNode({
            node_type: nodeType, label: item.content.slice(0, 40), content: item.content,
            source_turn_id: turnId, source_evidence: item.evidence || "",
            confidence: item.confidence != null ? item.confidence : 0.8,
          }));
        }
      }
    }
    return diff;
  }

  exportJson() { return this._graph.toVisData(); }
  reset() { this._graph = new CanvasGraph(); }
}
module.exports = { CanvasStateManager };
