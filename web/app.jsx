const { useState, useEffect, useRef, useCallback, useMemo } = React;

// ════════════════════════════════════════════════════════════════
// Constants
// ════════════════════════════════════════════════════════════════

const NODE_COLORS = {
  goal: "#FFD700", position: "#4A90D9", option: "#50C878",
  mechanism: "#7E57C2", resource: "#9B59B6", constraint: "#E74C3C",
  evidence: "#26A69A", tension: "#FF6B35", assumption: "#F39C12",
  risk: "#C0392B", signal: "#00BCD4", action: "#66BB6A",
  pattern: "#EC407A", stakeholder: "#8D6E63",
};

const NODE_TYPE_LABELS = {
  goal: "目标", position: "定位", option: "选项",
  mechanism: "机制", resource: "资源", constraint: "约束",
  evidence: "证据", tension: "张力", assumption: "假设",
  risk: "风险", signal: "信号", action: "行动",
  pattern: "模式", stakeholder: "利益方",
};

const NODE_HOUSE_MAP = {
  goal: "roof", position: "roof",
  option: "pillar", mechanism: "pillar",
  resource: "foundation", constraint: "foundation", evidence: "foundation",
  tension: "internal", assumption: "internal", risk: "internal", pattern: "internal",
  signal: "signal", action: "action", stakeholder: "external",
};

const HOUSE_SECTION_META = {
  roof:       { label: "VISION / 愿景",     color: "#F57F17", bg: "#FFF8E1", border: "#FFD54F" },
  pillar:     { label: "PILLARS / 战略支柱", color: "#2E7D32", bg: "#E8F5E9", border: "#81C784" },
  foundation: { label: "FOUNDATION / 地基",  color: "#1565C0", bg: "#E3F2FD", border: "#64B5F6" },
  internal:   { label: "TENSIONS / 内部张力", color: "#E65100", bg: "#FFF3E0", border: "#FFB74D" },
  signal:     { label: "SIGNALS / 验证信号",  color: "#00838F", bg: "#E0F7FA", border: "#4DD0E1" },
  action:     { label: "ACTIONS / 下一步",    color: "#6A1B9A", bg: "#F3E5F5", border: "#BA68C8" },
  external:   { label: "EXTERNAL / 外部",     color: "#37474F", bg: "#ECEFF1", border: "#90A4AE" },
};

const STAGE_LABELS = {
  explore: "Explore / 探索", converge: "Converge / 收敛",
  stress_test: "Stress Test / 压力测试", commit: "Commit / 决策",
  review: "Review / 回顾",
};

// ════════════════════════════════════════════════════════════════
// Project persistence (localStorage)
// ════════════════════════════════════════════════════════════════

const STORAGE_KEY = "strategy_canvas_projects";

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function createEmptyProject(name) {
  return {
    id: genId(),
    name: name || "New Project",
    createdAt: new Date().toISOString(),
    messages: [],
    graphData: { nodes: [], links: [] },
    goldenPhrases: [],
    namedConcepts: [],
    stage: "explore",
    confidence: 0,
    judgment: "",
  };
}

function loadProjects() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

function saveProjects(projects, activeId) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ projects, activeId }));
  } catch {}
}

// ════════════════════════════════════════════════════════════════
// WebSocket hook
// ════════════════════════════════════════════════════════════════

function useWebSocket(url) {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const handlersRef = useRef({});

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => { setConnected(false); setTimeout(connect, 2000); };
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
    if (wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(JSON.stringify(msg));
  }, []);

  const on = useCallback((type, handler) => {
    handlersRef.current[type] = handler;
  }, []);

  return { connected, send, on };
}

// ════════════════════════════════════════════════════════════════
// Column 1: Project Sidebar
// ════════════════════════════════════════════════════════════════

function ProjectSidebar({ projects, activeId, onSelect, onNew, onRename, onDelete }) {
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");

  const startRename = (p) => {
    setEditingId(p.id);
    setEditName(p.name);
  };

  const commitRename = () => {
    if (editName.trim()) onRename(editingId, editName.trim());
    setEditingId(null);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Projects</span>
      </div>
      <button className="sidebar-new-btn" onClick={onNew}>
        + New Project
      </button>
      <div className="sidebar-list">
        {projects.map(p => (
          <div key={p.id}
               className={`sidebar-item ${p.id === activeId ? "active" : ""}`}
               onClick={() => onSelect(p.id)}>
            {editingId === p.id ? (
              <input className="sidebar-rename-input"
                     value={editName}
                     onChange={e => setEditName(e.target.value)}
                     onBlur={commitRename}
                     onKeyDown={e => { if (e.key === "Enter") commitRename(); }}
                     autoFocus
                     onClick={e => e.stopPropagation()} />
            ) : (
              <>
                <div className="sidebar-item-name">{p.name}</div>
                <div className="sidebar-item-meta">
                  {p.graphData?.nodes?.length || 0} nodes
                  <span className="sidebar-item-date">
                    {new Date(p.createdAt).toLocaleDateString("zh-CN")}
                  </span>
                </div>
              </>
            )}
            <div className="sidebar-item-actions" onClick={e => e.stopPropagation()}>
              <button className="sidebar-action-btn" onClick={() => startRename(p)} title="Rename">&#9998;</button>
              {projects.length > 1 && (
                <button className="sidebar-action-btn danger" onClick={() => onDelete(p.id)} title="Delete">&times;</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 2: Chat Panel
// ════════════════════════════════════════════════════════════════

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
    <div className="col col-chat">
      <div className="col-header">Conversation / 对话</div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">Start a conversation about the decision you're facing...</div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.speaker}`}>
            <div className="chat-bubble">{msg.text}</div>
            {msg.invocations && (
              <div className="chat-meta">
                {msg.invocations.map((inv, j) => (
                  <span key={j} className="skill-tag">{inv.skill_id}</span>
                ))}
                {msg.latency_ms && <span className="latency">{msg.latency_ms}ms</span>}
              </div>
            )}
          </div>
        ))}
        {thinking && <div className="thinking-dot"><span /><span /><span /></div>}
        <div ref={endRef} />
      </div>
      <div className="chat-input-area">
        <textarea className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
          }}
          placeholder="Describe your strategic decision..."
          rows={2} />
        <button className="chat-send" onClick={handleSend}
                disabled={!input.trim() || thinking}>Send</button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 3: 3D Force Graph
// ════════════════════════════════════════════════════════════════

function Graph3DPanel({ graphData }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current || typeof ForceGraph3D === "undefined") return;

    const graph = ForceGraph3D({ controlType: "orbit" })(containerRef.current)
      .backgroundColor("rgba(0,0,0,0)")
      .showNavInfo(false)
      .nodeLabel(n => {
        const esc = s => (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
        return `<div style="background:#222;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;max-width:200px">
        <b>${esc(n.label)}</b><br/><span style="opacity:0.7">${esc(n.node_type)}</span>
        ${n.content ? `<br/><span style="opacity:0.5;font-size:11px">${esc(n.content.slice(0, 80))}</span>` : ""}
      </div>`;
      })
      .nodeColor(n => NODE_COLORS[n.node_type] || "#999")
      .nodeVal(n => (n.weight || 1) * 3)
      .nodeOpacity(0.9)
      .linkColor(() => "rgba(150,150,150,0.3)")
      .linkWidth(1)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.5)
      .linkDirectionalParticleColor(() => "rgba(100,180,255,0.6)")
      .linkLabel(l => l.label || "")
      .onNodeClick(node => {
        // Focus on node
        const distance = 120;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
        graph.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node, 1000
        );
      });

    graphRef.current = graph;

    // Handle resize
    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        graph.width(width).height(height);
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      graph._destructor && graph._destructor();
    };
  }, []);

  // Update data
  useEffect(() => {
    if (!graphRef.current) return;
    const nodes = (graphData?.nodes || []).map(n => ({ ...n }));
    const links = (graphData?.links || []).map(l => ({
      source: l.source, target: l.target,
      label: l.label || "", edge_type: l.edge_type || "",
    }));
    graphRef.current.graphData({ nodes, links });
  }, [graphData]);

  const nodeCount = graphData?.nodes?.length || 0;
  const linkCount = graphData?.links?.length || 0;

  return (
    <div className="col col-graph">
      <div className="col-header">
        Node Graph / 节点图
        <span className="col-header-badge">{nodeCount} nodes / {linkCount} edges</span>
      </div>
      <div className="graph3d-container" ref={containerRef}>
        {nodeCount === 0 && (
          <div className="graph3d-empty">Nodes will appear here as the conversation progresses...</div>
        )}
      </div>
      {nodeCount > 0 && (
        <div className="graph3d-legend">
          {Object.entries(NODE_COLORS).map(([type, color]) => {
            const count = (graphData?.nodes || []).filter(n => n.node_type === type).length;
            if (count === 0) return null;
            return (
              <span key={type} className="legend-item">
                <span className="legend-dot" style={{ background: color }} />
                {NODE_TYPE_LABELS[type] || type} ({count})
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 4: Summary / Analysis Panel
// ════════════════════════════════════════════════════════════════

function SummaryPanel({ graphData, goldenPhrases, namedConcepts, stage, confidence, judgment }) {
  const nodes = graphData?.nodes || [];
  const links = graphData?.links || [];

  // Node stats by type
  const typeStats = useMemo(() => {
    const stats = {};
    nodes.forEach(n => {
      stats[n.node_type] = (stats[n.node_type] || 0) + 1;
    });
    return Object.entries(stats).sort((a, b) => b[1] - a[1]);
  }, [nodes]);

  // Key tensions
  const tensions = nodes.filter(n => n.node_type === "tension" || n.node_type === "risk");
  // Key assumptions (low confidence)
  const weakAssumptions = nodes
    .filter(n => n.node_type === "assumption" && n.confidence < 0.6)
    .sort((a, b) => a.confidence - b.confidence);

  return (
    <div className="col col-summary">
      <div className="col-header">Analysis / 分析总结</div>
      <div className="summary-scroll">
        {/* Stage & Confidence */}
        <div className="summary-card">
          <div className="summary-card-title">Stage / 阶段</div>
          <div className="stage-badge">{STAGE_LABELS[stage] || stage}</div>
          <div className="confidence-bar-wrapper">
            <div className="confidence-label">
              Confidence: {Math.round(confidence * 100)}%
            </div>
            <div className="confidence-bar">
              <div className="confidence-fill" style={{ width: `${confidence * 100}%` }} />
            </div>
          </div>
        </div>

        {/* One-line judgment */}
        {judgment && (
          <div className="summary-card">
            <div className="summary-card-title">Judgment / 判断</div>
            <div className="judgment-text">{judgment}</div>
          </div>
        )}

        {/* Node statistics */}
        <div className="summary-card">
          <div className="summary-card-title">
            Nodes / 节点 <span className="count-badge">{nodes.length}</span>
          </div>
          <div className="type-stats">
            {typeStats.map(([type, count]) => (
              <div key={type} className="type-stat-row">
                <span className="type-dot" style={{ background: NODE_COLORS[type] }} />
                <span className="type-label">{NODE_TYPE_LABELS[type] || type}</span>
                <span className="type-count">{count}</span>
                <div className="type-bar">
                  <div style={{ width: `${(count / nodes.length) * 100}%`, background: NODE_COLORS[type] }} />
                </div>
              </div>
            ))}
          </div>
          <div className="edge-stat">{links.length} relationships / 关系</div>
        </div>

        {/* Key Tensions & Risks */}
        {tensions.length > 0 && (
          <div className="summary-card warning-card">
            <div className="summary-card-title">Key Tensions & Risks / 关键张力</div>
            {tensions.map(t => (
              <div key={t.id} className="tension-item">
                <span className="tension-type">{t.node_type}</span>
                <span className="tension-label">{t.label}</span>
                <span className="tension-conf">{Math.round(t.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        )}

        {/* Weak Assumptions */}
        {weakAssumptions.length > 0 && (
          <div className="summary-card danger-card">
            <div className="summary-card-title">Unverified Assumptions / 待验证假设</div>
            {weakAssumptions.map(a => (
              <div key={a.id} className="assumption-item">
                <div className="assumption-label">{a.label}</div>
                <div className="assumption-conf">
                  confidence {Math.round(a.confidence * 100)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Golden Phrases */}
        {goldenPhrases && goldenPhrases.length > 0 && (
          <div className="summary-card golden-card">
            <div className="summary-card-title">Golden Phrases / 金句</div>
            {goldenPhrases.map((p, i) => (
              <div key={i} className="golden-phrase">&ldquo;{p}&rdquo;</div>
            ))}
          </div>
        )}

        {/* Named Concepts */}
        {namedConcepts && namedConcepts.length > 0 && (
          <div className="summary-card">
            <div className="summary-card-title">Named Concepts / 命名概念</div>
            <div className="concepts-list">
              {namedConcepts.map((c, i) => (
                <span key={i} className="concept-tag">{c}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 5: Strategy House (Canvas-rendered, on-demand)
// ════════════════════════════════════════════════════════════════

function drawStrategyHouse(canvas, nodes) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const W = 560, H = 900;
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width = W + "px";
  canvas.style.height = H + "px";
  ctx.scale(dpr, dpr);

  // Group nodes
  const groups = { roof: [], pillar: [], foundation: [], internal: [], signal: [], action: [], external: [] };
  nodes.forEach(n => {
    const part = NODE_HOUSE_MAP[n.node_type] || "internal";
    groups[part].push(n);
  });

  // Background
  ctx.fillStyle = "#FAFAF8";
  ctx.fillRect(0, 0, W, H);

  const pad = 24;
  const contentW = W - pad * 2;
  let y = pad;

  // ── Helper: rounded rect
  function roundRect(x, y, w, h, r, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.stroke(); }
  }

  // ── Helper: wrap text and return lines
  function wrapText(text, maxW, font) {
    ctx.font = font;
    const words = text.split("");
    const lines = [];
    let line = "";
    for (const ch of words) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxW && line) {
        lines.push(line);
        line = ch;
      } else {
        line = test;
      }
    }
    if (line) lines.push(line);
    return lines;
  }

  // ── Helper: draw section with nodes
  function drawSection(meta, sectionNodes, startY, sectionW) {
    if (sectionNodes.length === 0) return startY;
    const innerPad = 10;
    const lineH = 16;

    // Measure total height
    let totalH = 36; // header
    sectionNodes.forEach(n => {
      const lines = wrapText(n.label + (n.content ? " — " + n.content : ""), sectionW - innerPad * 2 - 16, "12px sans-serif");
      totalH += 8 + lines.length * lineH + 8;
    });

    roundRect(pad, startY, sectionW, totalH, 6, meta.bg, meta.border);

    // Header
    ctx.font = "bold 11px sans-serif";
    ctx.fillStyle = meta.color;
    ctx.fillText(meta.label, pad + innerPad, startY + 22);

    let ny = startY + 36;
    sectionNodes.forEach(n => {
      // Node type badge
      const badgeColor = NODE_COLORS[n.node_type] || "#999";
      ctx.fillStyle = badgeColor;
      roundRect(pad + innerPad, ny, 6, 6, 3, badgeColor, null);

      // Label + content
      ctx.font = "bold 12px sans-serif";
      ctx.fillStyle = meta.color;
      const fullText = n.label + (n.content ? " — " + n.content : "");
      const lines = wrapText(fullText, sectionW - innerPad * 2 - 16, "12px sans-serif");
      ctx.font = "12px sans-serif";
      ctx.fillStyle = "#333";
      lines.forEach((line, li) => {
        ctx.fillText(line, pad + innerPad + 14, ny + 6 + li * lineH);
      });

      // Confidence
      const conf = Math.round((n.confidence || 0.5) * 100);
      ctx.font = "10px sans-serif";
      ctx.fillStyle = "#999";
      ctx.fillText(`${conf}%`, pad + sectionW - innerPad - 30, ny + 6);

      ny += 8 + lines.length * lineH + 4;
    });

    return startY + totalH + 10;
  }

  // ── Title
  ctx.font = "bold 18px sans-serif";
  ctx.fillStyle = "#1a1a1a";
  ctx.textAlign = "center";
  ctx.fillText("STRATEGY HOUSE / 战略屋", W / 2, y + 20);
  ctx.textAlign = "left";
  y += 40;

  // ── Roof triangle (vision)
  const roofH = 60 + groups.roof.length * 24;
  ctx.beginPath();
  ctx.moveTo(W / 2, y);
  ctx.lineTo(pad, y + roofH);
  ctx.lineTo(W - pad, y + roofH);
  ctx.closePath();
  ctx.fillStyle = "#FFF8E1";
  ctx.fill();
  ctx.strokeStyle = "#FFD54F";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.font = "bold 11px sans-serif";
  ctx.fillStyle = "#F57F17";
  ctx.textAlign = "center";
  ctx.fillText("VISION / 愿景", W / 2, y + 28);

  groups.roof.forEach((n, i) => {
    ctx.font = "13px sans-serif";
    ctx.fillStyle = "#B8860B";
    const label = n.label.length > 35 ? n.label.slice(0, 33) + "..." : n.label;
    ctx.fillText(label, W / 2, y + 48 + i * 22);
  });
  ctx.textAlign = "left";
  y += roofH + 4;

  // ── Pillars (side by side)
  if (groups.pillar.length > 0) {
    const pillarCount = groups.pillar.length;
    const gap = 8;
    const pillarW = (contentW - gap * (pillarCount - 1)) / pillarCount;
    const pillarH = 120;

    groups.pillar.forEach((n, i) => {
      const px = pad + i * (pillarW + gap);
      roundRect(px, y, pillarW, pillarH, 4, "#E8F5E9", "#81C784");

      ctx.font = "bold 11px sans-serif";
      ctx.fillStyle = "#2E7D32";
      const label = n.label.length > (pillarW / 7) ? n.label.slice(0, Math.floor(pillarW / 7) - 2) + ".." : n.label;
      ctx.fillText(label, px + 8, y + 20);

      ctx.font = "11px sans-serif";
      ctx.fillStyle = "#4a7c4e";
      const lines = wrapText(n.content || "", pillarW - 16, "11px sans-serif");
      lines.slice(0, 5).forEach((line, li) => {
        ctx.fillText(line, px + 8, y + 36 + li * 14);
      });
    });
    y += 120 + 10;
  }

  // ── Internal tensions/risks/assumptions
  y = drawSection(HOUSE_SECTION_META.internal, groups.internal, y, contentW);

  // ── Foundation
  y = drawSection(HOUSE_SECTION_META.foundation, groups.foundation, y, contentW);

  // ── Actions
  y = drawSection(HOUSE_SECTION_META.action, groups.action, y, contentW);

  // ── Signals
  y = drawSection(HOUSE_SECTION_META.signal, groups.signal, y, contentW);

  // ── External
  if (groups.external.length > 0) {
    y = drawSection(HOUSE_SECTION_META.external, groups.external, y, contentW);
  }

  // ── Watermark
  ctx.font = "10px sans-serif";
  ctx.fillStyle = "#ccc";
  ctx.textAlign = "center";
  ctx.fillText("Generated by Strategic Canvas", W / 2, y + 16);
  ctx.textAlign = "left";

  // Resize canvas to actual content height
  const finalH = y + 32;
  if (finalH < H) {
    const imgData = ctx.getImageData(0, 0, W * dpr, finalH * dpr);
    canvas.height = finalH * dpr;
    canvas.style.height = finalH + "px";
    ctx.putImageData(imgData, 0, 0);
  }
}

function StrategyHousePanel({ graphData }) {
  const canvasRef = useRef(null);
  const [generated, setGenerated] = useState(false);
  const [generating, setGenerating] = useState(false);
  const nodes = graphData?.nodes || [];

  const handleGenerate = () => {
    if (nodes.length === 0) return;
    setGenerating(true);
    // Small delay for UX feedback
    setTimeout(() => {
      drawStrategyHouse(canvasRef.current, nodes);
      setGenerated(true);
      setGenerating(false);
    }, 300);
  };

  const handleDownload = () => {
    if (!canvasRef.current) return;
    const link = document.createElement("a");
    link.download = "strategy-house.png";
    link.href = canvasRef.current.toDataURL("image/png");
    link.click();
  };

  return (
    <div className="col col-house">
      <div className="col-header">
        Strategy House / 战略屋
        {generated && (
          <button className="download-btn" onClick={handleDownload} title="Download PNG">
            &#8681; PNG
          </button>
        )}
      </div>
      <div className="house-content">
        {!generated && (
          <div className="house-placeholder">
            <div className="house-placeholder-icon">&#9960;</div>
            <p>Complete your strategic conversation, then generate a Strategy House diagram.</p>
            <p className="house-placeholder-stats">
              {nodes.length > 0 ? `${nodes.length} nodes ready for analysis` : "No nodes yet"}
            </p>
            <button className="generate-btn"
                    onClick={handleGenerate}
                    disabled={nodes.length === 0 || generating}>
              {generating ? "Generating..." : "Generate Strategy / 生成战略"}
            </button>
          </div>
        )}
        <canvas ref={canvasRef}
                className="house-canvas"
                style={{ display: generated ? "block" : "none" }} />
        {generated && (
          <button className="regenerate-btn" onClick={handleGenerate}>
            Regenerate / 重新生成
          </button>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Status Bar
// ════════════════════════════════════════════════════════════════

function StatusBar({ stage, confidence, connected, projectName }) {
  return (
    <div className="status-bar">
      <div className="status-left">
        <span className={`ws-dot ${connected ? "on" : "off"}`} />
        <span className="status-project">{projectName}</span>
      </div>
      <div className="status-center">
        {confidence > 0 && (
          <span className="status-conf">confidence {Math.round(confidence * 100)}%</span>
        )}
      </div>
      <div className="status-right">
        <span className="status-stage">{STAGE_LABELS[stage] || stage}</span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Main App
// ════════════════════════════════════════════════════════════════

function App() {
  const [projects, setProjects] = useState(() => {
    const saved = loadProjects();
    return saved?.projects?.length > 0 ? saved.projects : [createEmptyProject("Demo Session")];
  });
  const [activeId, setActiveId] = useState(() => {
    const saved = loadProjects();
    return saved?.activeId || projects[0]?.id;
  });
  const [thinking, setThinking] = useState(false);
  const [demoLoaded, setDemoLoaded] = useState(false);

  const project = projects.find(p => p.id === activeId) || projects[0];

  const { connected, send, on } = useWebSocket(`ws://${location.host}/ws`);

  // Update a field on the active project
  const updateProject = useCallback((updates) => {
    setProjects(prev => prev.map(p =>
      p.id === activeId ? { ...p, ...updates } : p
    ));
  }, [activeId]);

  // Save to localStorage whenever projects change
  useEffect(() => {
    saveProjects(projects, activeId);
  }, [projects, activeId]);

  // Load demo data into first project (once)
  useEffect(() => {
    if (demoLoaded) return;
    fetch("/static/demo_graph.json")
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const updates = {};
        if (data.graph) updates.graphData = data.graph;
        if (data.golden_phrases) updates.goldenPhrases = data.golden_phrases;
        if (data.named_concepts) updates.namedConcepts = data.named_concepts;
        if (data.conversation) {
          const msgs = [];
          data.conversation.forEach(turn => {
            if (turn.user) msgs.push({ speaker: "user", text: turn.user });
            if (turn.coach) msgs.push({ speaker: "assistant", text: turn.coach });
          });
          updates.messages = msgs;
          updates.name = "气候科技创业决策 (Demo)";
        }
        if (Object.keys(updates).length > 0) {
          updateProject(updates);
        }
        setDemoLoaded(true);
      })
      .catch(() => setDemoLoaded(true));
  }, [demoLoaded, updateProject]);

  // WebSocket handlers
  useEffect(() => {
    on("thinking", () => setThinking(true));

    on("response", (data) => {
      setThinking(false);

      const newMsg = {
        speaker: "assistant", text: data.reply,
        invocations: data.invocations, latency_ms: data.latency_ms,
      };

      setProjects(prev => prev.map(p => {
        if (p.id !== activeId) return p;
        const updated = { ...p };
        updated.messages = [...p.messages, newMsg];

        if (data.canvas?.nodes) {
          updated.graphData = {
            nodes: data.canvas.nodes || p.graphData.nodes,
            links: data.canvas.links || p.graphData.links,
          };
        }
        if (data.golden_phrases) updated.goldenPhrases = data.golden_phrases;
        if (data.named_concepts) updated.namedConcepts = data.named_concepts;
        if (data.one_line_judgment) updated.judgment = data.one_line_judgment;
        if (data.confidence) updated.confidence = data.confidence;
        if (data.stage) updated.stage = data.stage;

        return updated;
      }));
    });
  }, [on, activeId]);

  // Handlers
  const handleSend = useCallback((text) => {
    updateProject({
      messages: [...project.messages, { speaker: "user", text }],
    });
    send({ type: "chat", text });
  }, [send, project, updateProject]);

  const handleNewProject = () => {
    const p = createEmptyProject("New Project " + (projects.length + 1));
    setProjects(prev => [p, ...prev]);
    setActiveId(p.id);
  };

  const handleRenameProject = (id, name) => {
    setProjects(prev => prev.map(p => p.id === id ? { ...p, name } : p));
  };

  const handleDeleteProject = (id) => {
    setProjects(prev => {
      const next = prev.filter(p => p.id !== id);
      if (activeId === id && next.length > 0) setActiveId(next[0].id);
      return next;
    });
  };

  return (
    <div className="app">
      <div className="app-header">
        <h1>Strategic Canvas</h1>
        <div className="header-right">
          <span className="node-count">{project.graphData?.nodes?.length || 0} nodes</span>
        </div>
      </div>
      <div className="app-main">
        <ProjectSidebar
          projects={projects}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNewProject}
          onRename={handleRenameProject}
          onDelete={handleDeleteProject}
        />
        <ChatPanel
          messages={project.messages}
          onSend={handleSend}
          thinking={thinking}
        />
        <Graph3DPanel graphData={project.graphData} />
        <SummaryPanel
          graphData={project.graphData}
          goldenPhrases={project.goldenPhrases}
          namedConcepts={project.namedConcepts}
          stage={project.stage || "explore"}
          confidence={project.confidence || 0}
          judgment={project.judgment || ""}
        />
        <StrategyHousePanel graphData={project.graphData} />
      </div>
      <StatusBar
        stage={project.stage || "explore"}
        confidence={project.confidence || 0}
        connected={connected}
        projectName={project.name}
      />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
