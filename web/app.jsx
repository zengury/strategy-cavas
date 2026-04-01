const { useState, useEffect, useRef, useCallback } = React;

const ZONES = [
  { key: "north_star", label: "North Star / 北极星", fullWidth: true },
  { key: "context",    label: "Context / 背景" },
  { key: "options",    label: "Options / 选项" },
  { key: "tradeoffs",  label: "Trade-offs / 取舍" },
  { key: "assumptions",label: "Assumptions / 假设" },
  { key: "signals",    label: "Signals / 信号" },
  { key: "next_moves", label: "Next Moves / 下一步", fullWidth: true },
];

// node_type → canvas zone mapping
const TYPE_TO_ZONE = {
  goal: "north_star",
  position: "north_star",
  resource: "context",
  constraint: "context",
  evidence: "context",
  stakeholder: "context",
  option: "options",
  mechanism: "options",
  tension: "tradeoffs",
  risk: "tradeoffs",
  assumption: "assumptions",
  pattern: "assumptions",
  signal: "signals",
  action: "next_moves",
};

// Convert flat node array → zone-keyed object for CanvasPanel
function nodesToCanvasZones(nodes) {
  const zones = {};
  ZONES.forEach(z => { zones[z.key] = []; });
  (nodes || []).forEach(n => {
    const zone = TYPE_TO_ZONE[n.node_type] || "context";
    zones[zone].push({
      node_id: n.id,
      content: n.label + (n.content ? " — " + n.content : ""),
      confidence: n.confidence || 0.5,
      locked: n.locked || false,
      status: n.status || "active",
      risk_level: n.risk_level || "",
      source_skill: n.source_skill || "",
    });
  });
  return zones;
}

const STAGE_LABELS = {
  explore: "Explore",
  converge: "Converge",
  stress_test: "Stress Test",
  commit: "Commit",
  review: "Review",
};

// NodeType → Strategy House 部分的映射
const NODE_HOUSE_MAP = {
  goal:        "roof",
  position:    "roof",
  option:      "pillar",
  mechanism:   "pillar",
  resource:    "foundation",
  constraint:  "foundation",
  evidence:    "foundation",
  tension:     "internal",
  assumption:  "internal",
  risk:        "internal",
  signal:      "signal",
  action:      "action",
  pattern:     "internal",
  stakeholder: "external",
};

const HOUSE_COLORS = {
  roof:       { bg: "#FFF8E1", border: "#FFD54F", text: "#F57F17" },
  pillar:     { bg: "#E8F5E9", border: "#81C784", text: "#2E7D32" },
  foundation: { bg: "#E3F2FD", border: "#64B5F6", text: "#1565C0" },
  internal:   { bg: "#FFF3E0", border: "#FFB74D", text: "#E65100" },
  signal:     { bg: "#E0F7FA", border: "#4DD0E1", text: "#00838F" },
  action:     { bg: "#F3E5F5", border: "#BA68C8", text: "#6A1B9A" },
  external:   { bg: "#ECEFF1", border: "#90A4AE", text: "#37474F" },
};

function useWebSocket(url) {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const handlersRef = useRef({});

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 2000);
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        const handler = handlersRef.current[data.type];
        if (handler) handler(data);
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, [url]);

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const on = useCallback((type, handler) => {
    handlersRef.current[type] = handler;
  }, []);

  return { connected, send, on };
}

function ChatPanel({ messages, onSend, thinking }) {
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || thinking) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.speaker}`}>
            <div className="chat-message-bubble">{msg.text}</div>
            {msg.invocations && (
              <div className="chat-message-meta">
                {msg.invocations.map((inv, j) => (
                  <span key={j} className="skill-tag">{inv.skill_id}</span>
                ))}
                {msg.latency_ms && <span>{msg.latency_ms}ms</span>}
              </div>
            )}
          </div>
        ))}
        {thinking && <div className="thinking-indicator">Thinking...</div>}
        <div ref={endRef} />
      </div>
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
            }}
            placeholder="Tell me about the decision you're facing..."
            rows={2}
          />
          <button className="chat-send-btn" onClick={handleSend} disabled={!input.trim() || thinking}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function CanvasNodeView({ node, onLock, isNew }) {
  const riskClass = node.risk_level === "warning" ? "warning"
                  : node.risk_level === "critical" ? "critical" : "";
  const classes = ["canvas-node", node.locked && "locked", riskClass, isNew && "just-added"]
    .filter(Boolean).join(" ");

  return (
    <div className={classes}>
      <span className="canvas-node-lock"
            onClick={() => onLock(node.node_id, !node.locked)}
            title={node.locked ? "Unlock" : "Lock"}>
        {node.locked ? "\u{1F512}" : "\u{1F513}"}
      </span>
      <div className="canvas-node-content">{node.content}</div>
      {node.source_skill && (
        <div className="canvas-node-skill">{node.source_skill}</div>
      )}
      <div className="canvas-node-confidence">
        confidence {Math.round((node.confidence || 0.5) * 100)}%
      </div>
    </div>
  );
}

function CanvasPanel({ canvas, onLock, newNodeIds }) {
  const nodes = canvas?.nodes || {};

  return (
    <div className="canvas-panel">
      <div className="canvas-grid">
        {ZONES.map(({ key, label, fullWidth }) => {
          const zoneNodes = (nodes[key] || []).filter(n => n.status === "active");
          return (
            <div key={key} className={`canvas-zone ${fullWidth ? "full-width" : ""}`}>
              <div className="canvas-zone-header">
                <span>{label}</span>
                <span className="canvas-zone-count">
                  {zoneNodes.length > 0 ? zoneNodes.length : ""}
                </span>
              </div>
              <div className="canvas-zone-content">
                {zoneNodes.length === 0
                  ? <div className="canvas-empty">Waiting for conversation...</div>
                  : zoneNodes.map(node => (
                      <CanvasNodeView key={node.node_id} node={node}
                        onLock={onLock} isNew={newNodeIds.has(node.node_id)} />
                    ))
                }
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Strategy House SVG Renderer ─────────────────────────────

function StrategyHouseHTML({ graphData }) {
  const nodes = graphData?.nodes || [];
  if (nodes.length === 0) {
    return (
      <div className="house-empty">
        <p>Start a conversation to build your Strategy House...</p>
      </div>
    );
  }

  // 按 house 部分分组
  const groups = { roof: [], pillar: [], foundation: [], internal: [], signal: [], action: [], external: [] };
  nodes.forEach(n => {
    const part = NODE_HOUSE_MAP[n.node_type] || "internal";
    groups[part].push(n);
  });

  const HouseNode = ({ node, colors }) => (
    <div className="house-node" style={{
      background: colors.bg, border: `1px solid ${colors.border}`,
      borderRadius: "6px", padding: "8px 10px", marginBottom: "6px",
    }}>
      <div style={{ fontSize: "10px", fontWeight: "600", color: colors.text, textTransform: "uppercase", marginBottom: "2px" }}>
        {node.node_type}
        {node.source_skill && <span style={{ fontWeight: "400", opacity: 0.6, marginLeft: "6px", textTransform: "none" }}>via {node.source_skill}</span>}
      </div>
      <div style={{ fontSize: "13px", fontWeight: "600", color: colors.text }}>{node.label}</div>
      <div style={{ fontSize: "11px", color: colors.text, opacity: 0.7, marginTop: "2px" }}>{node.content}</div>
      <div style={{ fontSize: "10px", color: colors.text, opacity: 0.5, marginTop: "4px" }}>
        confidence {Math.round((node.confidence || 0.5) * 100)}%
      </div>
    </div>
  );

  const Section = ({ title, icon, nodes, colors, style }) => {
    if (nodes.length === 0) return null;
    return (
      <div className="house-section" style={style}>
        <div className="house-section-header" style={{ color: colors.text }}>
          {icon} {title} <span style={{ opacity: 0.5 }}>({nodes.length})</span>
        </div>
        {nodes.map(n => <HouseNode key={n.id} node={n} colors={colors} />)}
      </div>
    );
  };

  return (
    <div className="strategy-house-html">
      {/* Roof - Vision */}
      <div className="house-roof">
        <div className="house-roof-label">VISION / 愿景</div>
        {groups.roof.map(n => <HouseNode key={n.id} node={n} colors={HOUSE_COLORS.roof} />)}
        {groups.roof.length === 0 && <div className="house-placeholder">Awaiting goal definition...</div>}
      </div>

      {/* Main body - 3 column layout */}
      <div className="house-body">
        <div className="house-body-left">
          <Section title="Pillars / 支柱" icon="&#9648;" nodes={groups.pillar} colors={HOUSE_COLORS.pillar} />
        </div>
        <div className="house-body-center">
          <Section title="Tensions & Risks / 张力与风险" icon="&#9888;" nodes={groups.internal} colors={HOUSE_COLORS.internal} />
        </div>
        <div className="house-body-right">
          <Section title="External / 外部" icon="&#9673;" nodes={groups.external} colors={HOUSE_COLORS.external} />
        </div>
      </div>

      {/* Foundation */}
      <div className="house-foundation">
        <div className="house-section-header" style={{ color: HOUSE_COLORS.foundation.text }}>
          FOUNDATION / 地基 <span style={{ opacity: 0.5 }}>({groups.foundation.length})</span>
        </div>
        <div className="house-foundation-grid">
          {groups.foundation.map(n => <HouseNode key={n.id} node={n} colors={HOUSE_COLORS.foundation} />)}
        </div>
      </div>

      {/* Bottom: Actions + Signals */}
      <div className="house-bottom">
        <Section title="Next Moves / 下一步" icon="&#9654;" nodes={groups.action} colors={HOUSE_COLORS.action} />
        <Section title="Validation Signals / 验证信号" icon="&#9678;" nodes={groups.signal} colors={HOUSE_COLORS.signal} />
      </div>
    </div>
  );
}

// ── Golden Phrases ──────────────────────────────────────────

function GoldenPhrases({ phrases }) {
  if (!phrases || phrases.length === 0) return null;

  return (
    <div className="golden-phrases">
      <div className="golden-phrases-header">Golden Phrases</div>
      {phrases.map((p, i) => (
        <div key={i} className="golden-phrase">
          <span className="golden-phrase-mark">&ldquo;</span>
          {p}
          <span className="golden-phrase-mark">&rdquo;</span>
        </div>
      ))}
    </div>
  );
}

// ── Named Concepts ──────────────────────────────────────────

function NamedConcepts({ concepts }) {
  if (!concepts || concepts.length === 0) return null;

  return (
    <div className="named-concepts">
      <div className="named-concepts-header">Named Concepts</div>
      <div className="named-concepts-list">
        {concepts.map((c, i) => (
          <span key={i} className="named-concept-tag">{c}</span>
        ))}
      </div>
    </div>
  );
}

// ── Strategy House Panel (combines SVG + golden phrases + concepts) ──

function StrategyHousePanel({ graphData, goldenPhrases, namedConcepts }) {
  return (
    <div className="strategy-house-panel">
      <StrategyHouseHTML graphData={graphData} />
      <GoldenPhrases phrases={goldenPhrases} />
      <NamedConcepts concepts={namedConcepts} />
    </div>
  );
}

function StatusBar({ judgment, confidence, stage }) {
  return (
    <div className="status-bar">
      <div className="status-judgment">{judgment || "Start a conversation to generate your strategic canvas..."}</div>
      {confidence > 0 && (
        <div className="status-confidence">confidence {Math.round(confidence * 100)}%</div>
      )}
      <div className="status-stage">{STAGE_LABELS[stage] || stage}</div>
    </div>
  );
}

function ThemeSwitcher({ theme, onChange }) {
  return (
    <div className="theme-switcher">
      {["whiteboard", "notebook", "minimal"].map(t => (
        <div key={t} className={`theme-btn ${theme === t ? "active" : ""}`}
             data-theme={t} onClick={() => onChange(t)} title={t} />
      ))}
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [canvas, setCanvas] = useState({ nodes: {} });
  const [thinking, setThinking] = useState(false);
  const [judgment, setJudgment] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [stage, setStage] = useState("explore");
  const [theme, setTheme] = useState("whiteboard");
  const [newNodeIds, setNewNodeIds] = useState(new Set());
  const [rightTab, setRightTab] = useState("house"); // "canvas" | "house"
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [goldenPhrases, setGoldenPhrases] = useState([]);
  const [namedConcepts, setNamedConcepts] = useState([]);

  const { send, on } = useWebSocket(`ws://${location.host}/ws`);

  // 加载 demo 数据（如果存在）
  useEffect(() => {
    fetch("/static/demo_graph.json")
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        if (data.graph) {
          setGraphData(data.graph);
          // Also populate canvas zones from flat node array
          if (data.graph.nodes) {
            setCanvas({ nodes: nodesToCanvasZones(data.graph.nodes) });
          }
        }
        if (data.golden_phrases) {
          setGoldenPhrases(data.golden_phrases);
        }
        if (data.named_concepts) {
          setNamedConcepts(data.named_concepts);
        }
        // Load demo conversation into chat
        if (data.conversation) {
          const msgs = [];
          data.conversation.forEach(turn => {
            if (turn.user) msgs.push({ speaker: "user", text: turn.user });
            if (turn.coach) msgs.push({ speaker: "assistant", text: turn.coach });
          });
          setMessages(msgs);
        }
      })
      .catch(() => {}); // no demo data, fine
  }, []);

  useEffect(() => {
    const map = { whiteboard: "", notebook: "notebook", minimal: "minimal" };
    document.documentElement.setAttribute("data-theme", map[theme] || "");
  }, [theme]);

  useEffect(() => {
    on("thinking", () => setThinking(true));

    on("response", (data) => {
      setThinking(false);
      setMessages(prev => [...prev, {
        speaker: "assistant", text: data.reply,
        invocations: data.invocations, latency_ms: data.latency_ms,
      }]);

      if (data.canvas) {
        const addedIds = new Set();
        for (const zone of Object.values(data.canvas.nodes || {})) {
          for (const node of zone) {
            if (!findNode(canvas, node.node_id)) addedIds.add(node.node_id);
          }
        }
        setNewNodeIds(addedIds);
        setCanvas(data.canvas);
        setTimeout(() => setNewNodeIds(new Set()), 600);

        // 更新 graph data for Strategy House
        if (data.canvas.nodes) {
          setGraphData(prev => ({
            nodes: data.canvas.nodes || prev.nodes,
            links: data.canvas.links || prev.links,
          }));
        }
      }

      // 更新 golden phrases（如果 LLM 返回）
      if (data.golden_phrases) {
        setGoldenPhrases(data.golden_phrases);
      }
      if (data.named_concepts) {
        setNamedConcepts(data.named_concepts);
      }

      setJudgment(data.one_line_judgment || "");
      setConfidence(data.confidence || 0);
      setStage(data.stage || "explore");
    });

    on("node_locked", (d) => setCanvas(prev => updateNode(prev, d.node_id, "locked", true)));
    on("node_unlocked", (d) => setCanvas(prev => updateNode(prev, d.node_id, "locked", false)));
  }, [on, canvas]);

  const handleSend = useCallback((text) => {
    setMessages(prev => [...prev, { speaker: "user", text }]);
    send({ type: "chat", text });
  }, [send]);

  const handleLock = useCallback((nodeId, lock) => {
    send({ type: lock ? "lock_node" : "unlock_node", node_id: nodeId });
  }, [send]);

  return (
    <div className="app">
      <div className="app-header">
        <h1>Strategic Canvas Live</h1>
        <ThemeSwitcher theme={theme} onChange={setTheme} />
      </div>
      <div className="app-main">
        <ChatPanel messages={messages} onSend={handleSend} thinking={thinking} />
        <div className="right-panel">
          <div className="right-tabs">
            <button className={`right-tab ${rightTab === "house" ? "active" : ""}`}
                    onClick={() => setRightTab("house")}>Strategy House</button>
            <button className={`right-tab ${rightTab === "canvas" ? "active" : ""}`}
                    onClick={() => setRightTab("canvas")}>Canvas</button>
          </div>
          {rightTab === "house" ? (
            <StrategyHousePanel graphData={graphData}
                                goldenPhrases={goldenPhrases}
                                namedConcepts={namedConcepts} />
          ) : (
            <CanvasPanel canvas={canvas} onLock={handleLock} newNodeIds={newNodeIds} />
          )}
        </div>
      </div>
      <StatusBar judgment={judgment} confidence={confidence} stage={stage} />
    </div>
  );
}

function findNode(canvas, id) {
  for (const nodes of Object.values(canvas.nodes || {}))
    if (nodes.find(n => n.node_id === id)) return true;
  return false;
}

function updateNode(canvas, id, field, value) {
  const u = { ...canvas, nodes: {} };
  for (const [z, ns] of Object.entries(canvas.nodes || {}))
    u.nodes[z] = ns.map(n => n.node_id === id ? { ...n, [field]: value } : n);
  return u;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
