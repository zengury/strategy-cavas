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

  const { send, on } = useWebSocket(`ws://${location.host}/ws`);

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
        <CanvasPanel canvas={canvas} onLock={handleLock} newNodeIds={newNodeIds} />
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
