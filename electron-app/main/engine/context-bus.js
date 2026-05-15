class ContextBus {
  constructor(maxTurns = 50) {
    this.maxTurns = maxTurns;
    this._turns = [];
    this._documents = [];
    this._structured = [];
  }
  addTurn(turn) {
    this._turns.push(turn);
    if (this._turns.length > this.maxTurns) this._turns = this._turns.slice(-this.maxTurns);
  }
  addDocument(content, sourceName = "") {
    this._documents.push({ source_type: "document", raw_content: content, normalized_payload: { source: sourceName, text: content } });
  }
  addStructured(data, label = "") {
    this._structured.push({ source_type: "structured", raw_content: JSON.stringify(data), normalized_payload: { label, data } });
  }
  snapshot(canvas) {
    return {
      conversation: this._turns.slice(-20).map(t => ({ speaker: t.speaker, text: t.text, turn_id: t.turn_id, intent: t.intent, stage: t.stage })),
      documents: this._documents.map(d => ({ source: d.normalized_payload.source || "", text: (d.normalized_payload.text || "").slice(0, 2000) })),
      structured_inputs: this._structured.map(s => s.normalized_payload),
      canvas_summary: canvas ? canvas.toSummary() : {},
      turn_count: this._turns.length,
    };
  }
  recentTurns(n = 5) { return this._turns.slice(-n); }
  allTurns() { return [...this._turns]; }
  clear() { this._turns = []; this._documents = []; this._structured = []; }
}
module.exports = { ContextBus };
