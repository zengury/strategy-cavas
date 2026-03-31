const { useState, useEffect, useRef, useCallback } = React;

const ZONES = [
  { key: "north_star", label: "North Star", fullWidth: true },
  { key: "context",    label: "Context" },
  { key: "options",    label: "Options" },
  { key: "tradeoffs",  label: "Trade-offs" },
  { key: "assumptions",label: "Assumptions" },
  { key: "signals",    label: "Signals" },
  { key: "next_moves", label: "Next Moves", fullWidth: true },
];

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
      <div>{node.content}</div>
      <div className="canvas-node-confidence">
        confidence {Math.round(node.confidence * 100)}%
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

function StrategyHouseSVG({ graphData }) {
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

  // SVG 尺寸
  const W = 720, H = 580;
  const pad = 20;

  // 屋顶三角形
  const roofY = 30;
  const roofH = 100;
  const roofPeakX = W / 2;
  const roofBaseY = roofY + roofH;
  const roofTriangle = `${roofPeakX},${roofY} ${pad},${roofBaseY} ${W - pad},${roofBaseY}`;

  // 柱子区域
  const pillarY = roofBaseY + 8;
  const pillarH = 180;
  const pillarCount = Math.max(groups.pillar.length, 2);
  const pillarW = Math.min(120, (W - pad * 2 - 40) / pillarCount - 16);

  // 地基
  const foundY = pillarY + pillarH + 8;
  const foundH = 70;

  // 内部 (假设/风险/张力) — 柱子之间
  const internalY = pillarY + 10;
  const internalH = pillarH - 20;

  // 行动 + 信号 — 地基下方
  const actionY = foundY + foundH + 16;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="strategy-house-svg" xmlns="http://www.w3.org/2000/svg">
      {/* 屋顶 - 愿景/目标 */}
      <polygon
        points={roofTriangle}
        fill={HOUSE_COLORS.roof.bg}
        stroke={HOUSE_COLORS.roof.border}
        strokeWidth="2"
      />
      <text x={roofPeakX} y={roofY + 30} textAnchor="middle"
            fontSize="11" fill={HOUSE_COLORS.roof.text} fontWeight="600">VISION</text>
      {groups.roof.map((n, i) => (
        <text key={n.id} x={roofPeakX} y={roofY + 50 + i * 18}
              textAnchor="middle" fontSize="12" fill={HOUSE_COLORS.roof.text}>
          {n.label.length > 40 ? n.label.slice(0, 38) + "..." : n.label}
        </text>
      ))}

      {/* 柱子 - 战略选项 */}
      {groups.pillar.map((n, i) => {
        const totalW = pillarCount * (pillarW + 16) - 16;
        const startX = (W - totalW) / 2;
        const px = startX + i * (pillarW + 16);
        return (
          <g key={n.id}>
            <rect x={px} y={pillarY} width={pillarW} height={pillarH}
                  rx="4" fill={HOUSE_COLORS.pillar.bg}
                  stroke={HOUSE_COLORS.pillar.border} strokeWidth="1.5" />
            <foreignObject x={px + 6} y={pillarY + 8} width={pillarW - 12} height={pillarH - 16}>
              <div xmlns="http://www.w3.org/1999/xhtml" style={{
                fontSize: "11px", color: HOUSE_COLORS.pillar.text,
                lineHeight: "1.4", overflow: "hidden", height: "100%",
                fontWeight: "600", marginBottom: "4px",
              }}>
                {n.label}
                <div style={{ fontWeight: "400", fontSize: "10px", marginTop: "6px", opacity: 0.8 }}>
                  {n.content.length > 80 ? n.content.slice(0, 78) + "..." : n.content}
                </div>
              </div>
            </foreignObject>
          </g>
        );
      })}

      {/* 内部标签 — 假设/风险/张力（柱子间区域标注） */}
      {groups.internal.length > 0 && (
        <g>
          {groups.internal.slice(0, 4).map((n, i) => {
            const ix = W - pad - 160;
            const iy = internalY + i * 40;
            const colors = HOUSE_COLORS.internal;
            return (
              <g key={n.id}>
                <rect x={ix} y={iy} width={150} height={32}
                      rx="4" fill={colors.bg} stroke={colors.border} strokeWidth="1"
                      strokeDasharray="4,2" />
                <text x={ix + 8} y={iy + 14} fontSize="9" fill={colors.text} fontWeight="600">
                  {n.node_type.toUpperCase()}
                </text>
                <text x={ix + 8} y={iy + 26} fontSize="10" fill={colors.text}>
                  {n.label.length > 20 ? n.label.slice(0, 18) + "..." : n.label}
                </text>
              </g>
            );
          })}
        </g>
      )}

      {/* 地基 - 资源/能力 */}
      <rect x={pad} y={foundY} width={W - pad * 2} height={foundH}
            rx="4" fill={HOUSE_COLORS.foundation.bg}
            stroke={HOUSE_COLORS.foundation.border} strokeWidth="2" />
      <text x={pad + 12} y={foundY + 18} fontSize="11"
            fill={HOUSE_COLORS.foundation.text} fontWeight="600">FOUNDATION</text>
      {groups.foundation.slice(0, 4).map((n, i) => {
        const fx = pad + 12 + i * 170;
        return (
          <text key={n.id} x={fx} y={foundY + 38} fontSize="11"
                fill={HOUSE_COLORS.foundation.text}>
            {n.label.length > 22 ? n.label.slice(0, 20) + ".." : n.label}
          </text>
        );
      })}

      {/* 行动步骤 + 信号指标 */}
      {(groups.action.length > 0 || groups.signal.length > 0) && (
        <g>
          <text x={pad} y={actionY} fontSize="11" fill="#666" fontWeight="600">
            NEXT MOVES
          </text>
          {groups.action.map((n, i) => (
            <g key={n.id}>
              <rect x={pad + i * 230} y={actionY + 6} width={220} height={36}
                    rx="4" fill={HOUSE_COLORS.action.bg}
                    stroke={HOUSE_COLORS.action.border} strokeWidth="1" />
              <text x={pad + i * 230 + 10} y={actionY + 28} fontSize="11"
                    fill={HOUSE_COLORS.action.text}>
                {n.label.length > 30 ? n.label.slice(0, 28) + ".." : n.label}
              </text>
            </g>
          ))}

          {groups.signal.length > 0 && (
            <>
              <text x={pad} y={actionY + 58} fontSize="11" fill="#666" fontWeight="600">
                VALIDATION SIGNALS
              </text>
              {groups.signal.map((n, i) => (
                <g key={n.id}>
                  <rect x={pad + i * 230} y={actionY + 64} width={220} height={36}
                        rx="4" fill={HOUSE_COLORS.signal.bg}
                        stroke={HOUSE_COLORS.signal.border} strokeWidth="1" />
                  <text x={pad + i * 230 + 10} y={actionY + 86} fontSize="11"
                        fill={HOUSE_COLORS.signal.text}>
                    {n.label.length > 30 ? n.label.slice(0, 28) + ".." : n.label}
                  </text>
                </g>
              ))}
            </>
          )}
        </g>
      )}
    </svg>
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
      <StrategyHouseSVG graphData={graphData} />
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
        if (data?.graph) {
          setGraphData(data.graph);
        }
        if (data?.golden_phrases) {
          setGoldenPhrases(data.golden_phrases);
        }
        if (data?.named_concepts) {
          setNamedConcepts(data.named_concepts);
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
