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
  goal: "目标 Goal", position: "定位 Position", option: "选项 Option",
  mechanism: "机制 Mechanism", resource: "资源 Resource", constraint: "约束 Constraint",
  evidence: "证据 Evidence", tension: "张力 Tension", assumption: "假设 Assumption",
  risk: "风险 Risk", signal: "信号 Signal", action: "行动 Action",
  pattern: "模式 Pattern", stakeholder: "利益方 Stakeholder",
};

const NODE_TYPE_ZH = {
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
    id: genId(), name: name || "New Project",
    createdAt: new Date().toISOString(),
    messages: [], graphData: { nodes: [], links: [] },
    goldenPhrases: [], namedConcepts: [],
    stage: "explore", confidence: 0, judgment: "",
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
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ projects, activeId })); } catch {}
}

// ════════════════════════════════════════════════════════════════
// IPC hook (replaces WebSocket)
// ════════════════════════════════════════════════════════════════

function useIPC() {
  const [connected, setConnected] = useState(false);
  const handlersRef = useRef({});

  useEffect(() => {
    const api = window.electronAPI;
    if (!api) return;
    setConnected(true);

    api.onThinking(() => {
      const h = handlersRef.current["thinking"];
      if (h) h({});
    });

    api.onResponse((data) => {
      const h = handlersRef.current["response"];
      if (h) h(data);
    });

    return () => { api.removeListeners && api.removeListeners(); };
  }, []);

  const send = useCallback((msg) => {
    if (msg.type === "chat" && window.electronAPI) {
      window.electronAPI.sendChat(msg.text);
    }
  }, []);

  const on = useCallback((type, handler) => {
    handlersRef.current[type] = handler;
  }, []);

  return { connected, send, on };
}

// ════════════════════════════════════════════════════════════════
// HTML escape for nodeLabel
// ════════════════════════════════════════════════════════════════

function esc(s) {
  return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ════════════════════════════════════════════════════════════════
// Column 1: Project Sidebar
// ════════════════════════════════════════════════════════════════

function ProjectSidebar({ projects, activeId, onSelect, onNew, onRename, onDelete, flex, onExpand, isExpanded, collapsed }) {
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");

  const startRename = (p) => { setEditingId(p.id); setEditName(p.name); };
  const commitRename = () => { if (editName.trim()) onRename(editingId, editName.trim()); setEditingId(null); };

  return (
    <div className={`sidebar${collapsed ? ' sidebar-collapsed' : ''}`}
      style={{ flex: isExpanded ? `0 0 ${flex}%` : flex }}
      onClick={collapsed ? () => onExpand('sidebar') : undefined}>
      <div className="sidebar-header" onDoubleClick={() => onExpand('sidebar')}>
        <span className="sidebar-title">Projects</span></div>
      <button className="sidebar-new-btn" onClick={onNew}>+ New Project</button>
      <div className="sidebar-list">
        {projects.map(p => (
          <div key={p.id} className={`sidebar-item ${p.id === activeId ? "active" : ""}`} onClick={() => onSelect(p.id)}>
            {editingId === p.id ? (
              <input className="sidebar-rename-input" value={editName}
                onChange={e => setEditName(e.target.value)}
                onBlur={commitRename}
                onKeyDown={e => { if (e.key === "Enter") commitRename(); }}
                autoFocus onClick={e => e.stopPropagation()} />
            ) : (
              <>
                <div className="sidebar-item-name">{p.name}</div>
                <div className="sidebar-item-meta">
                  {p.graphData?.nodes?.length || 0} nodes
                  <span className="sidebar-item-date">{new Date(p.createdAt).toLocaleDateString("zh-CN")}</span>
                </div>
              </>
            )}
            <div className="sidebar-item-actions" onClick={e => e.stopPropagation()}>
              <button className="sidebar-action-btn" onClick={() => startRename(p)}>&#9998;</button>
              {projects.length > 1 && <button className="sidebar-action-btn danger" onClick={() => onDelete(p.id)}>&times;</button>}
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

function ChatPanel({ messages, onSend, thinking, flex, onExpand, isExpanded, collapsed }) {
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, thinking]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || thinking) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className={`col col-chat${collapsed ? ' col-collapsed' : ''}`}
      style={{ flex: isExpanded ? `0 0 ${flex}%` : flex }}
      onClick={collapsed ? () => onExpand('chat') : undefined}>
      <div className="col-header" onDoubleClick={() => onExpand('chat')}>Conversation / 对话</div>
      <div className="chat-messages">
        {messages.length === 0 && <div className="chat-empty">Start a conversation about the decision you're facing...</div>}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.speaker}`}>
            <div className="chat-bubble">{msg.text}</div>
          </div>
        ))}
        {thinking && <div className="thinking-dot"><span /><span /><span /></div>}
        <div ref={endRef} />
      </div>
      <div className="chat-input-area">
        <textarea className="chat-input" value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          placeholder="Describe your strategic decision..." rows={2} />
        <button className="chat-send" onClick={handleSend} disabled={!input.trim() || thinking}>Send</button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 3: 3D Force Graph (with glow spheres + canvas labels)
// ════════════════════════════════════════════════════════════════

function Graph3DPanel({ graphData, selectedNodeId, onNodeSelect, flex, onExpand, isExpanded, collapsed }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);

  function truncate(str, len) {
    return str && str.length > len ? str.slice(0, len - 1) + "…" : (str || "");
  }

  useEffect(() => {
    if (!containerRef.current || typeof ForceGraph3D === "undefined") return;

    const THREE = window.THREE || (ForceGraph3D && ForceGraph3D({})._destructor ? null : null);
    let threeLib = null;
    try {
      const testGraph = ForceGraph3D()(document.createElement("div"));
      threeLib = testGraph.scene().constructor.__proto__.constructor;
      testGraph._destructor && testGraph._destructor();
    } catch(e) {}

    const graph = ForceGraph3D({ controlType: "orbit" })(containerRef.current)
      .backgroundColor("rgba(0,0,0,0)")
      .showNavInfo(false)
      .nodeLabel(n => {
        return `<div style="background:#222;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;max-width:200px">
          <b>${esc(n.label)}</b><br/><span style="opacity:0.7">${esc(n.node_type)}</span>
          ${n.content ? `<br/><span style="opacity:0.5;font-size:11px">${esc(n.content.slice(0, 80))}</span>` : ""}
        </div>`;
      })
      .nodeThreeObject(n => {
        const T = graph.scene().constructor.__proto__?.constructor || window.THREE;
        if (!T || !T.Group) {
          return undefined;
        }

        const group = new T.Group();
        const color = NODE_COLORS[n.node_type] || "#999";
        const linkCount = (graphData?.links || []).filter(l => l.source === n.id || l.target === n.id || l.source?.id === n.id || l.target?.id === n.id).length;
        const size = Math.max(3, Math.min(8, 3 + linkCount * 0.8));

        const geo = new T.SphereGeometry(size, 16, 16);
        const mat = new T.MeshLambertMaterial({
          color: color, emissive: color, emissiveIntensity: (n.confidence || 0.8) * 0.6,
          transparent: true, opacity: 0.9,
        });
        group.add(new T.Mesh(geo, mat));

        const cvs = document.createElement("canvas");
        cvs.width = 512; cvs.height = 128;
        const ctx = cvs.getContext("2d");
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(76, 20, 360, 88);
        ctx.textAlign = "center";
        ctx.font = "bold 22px sans-serif";
        ctx.fillStyle = color;
        ctx.fillText((n.node_type || "").toUpperCase(), 256, 48);
        ctx.font = "bold 28px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(truncate(n.label, 20), 256, 82);

        const tex = new T.CanvasTexture(cvs);
        const lblMat = new T.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
        const lbl = new T.Sprite(lblMat);
        lbl.scale.set(48, 12, 1);
        lbl.position.set(0, size + 8, 0);
        group.add(lbl);

        return group;
      })
      .nodeVal(n => (n.weight || 1) * 3)
      .linkColor(() => "rgba(150,150,150,0.3)")
      .linkWidth(1)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.5)
      .linkDirectionalParticleColor(() => "rgba(100,180,255,0.6)")
      .linkLabel(l => l.label || "")
      .d3Force("charge").strength(-120);

    graph.d3Force("link").distance(l => 30 + (1 - (l.strength || 0.5)) * 50);

    graph.controls().autoRotate = true;
    graph.controls().autoRotateSpeed = 0.5;

    graph.onNodeClick(node => {
      if (onNodeSelect) onNodeSelect(node.id);
      const distance = 120;
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
      graph.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node, 1000
      );
    });

    graphRef.current = graph;

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        graph.width(width).height(height);
      }
    });
    ro.observe(containerRef.current);

    return () => { ro.disconnect(); graph._destructor && graph._destructor(); };
  }, []);

  useEffect(() => {
    if (!graphRef.current) return;
    const nodes = (graphData?.nodes || []).map(n => ({ ...n }));
    const links = (graphData?.links || []).map(l => ({
      source: l.source, target: l.target,
      label: l.label || "", edge_type: l.edge_type || "", strength: l.strength || 0.5,
    }));
    graphRef.current.graphData({ nodes, links });
  }, [graphData]);

  const nodeCount = graphData?.nodes?.length || 0;
  const linkCount = graphData?.links?.length || 0;

  return (
    <div className={`col col-graph${collapsed ? ' col-collapsed' : ''}`}
      style={{ flex: isExpanded ? `0 0 ${flex}%` : flex }}
      onClick={collapsed ? () => onExpand('graph') : undefined}>
      <div className="col-header" onDoubleClick={() => onExpand('graph')}>
        Node Graph / 节点图
        <span className="col-header-badge">{nodeCount} nodes / {linkCount} edges</span>
      </div>
      <div className="graph3d-container" ref={containerRef}>
        {nodeCount === 0 && <div className="graph3d-empty">Nodes will appear here as the conversation progresses...</div>}
      </div>
      {nodeCount > 0 && (
        <div className="graph3d-legend">
          {Object.entries(NODE_COLORS).map(([type, color]) => {
            const count = (graphData?.nodes || []).filter(n => n.node_type === type).length;
            if (count === 0) return null;
            return <span key={type} className="legend-item"><span className="legend-dot" style={{ background: color }} />{NODE_TYPE_ZH[type] || type} ({count})</span>;
          })}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 4: Node Selector Panel (bilingual, grouped by type)
// ════════════════════════════════════════════════════════════════

function NodeSelectorPanel({ graphData, selectedNodeId, onNodeSelect, flex, onExpand, isExpanded, collapsed }) {
  const nodes = graphData?.nodes || [];

  const grouped = useMemo(() => {
    const groups = {};
    nodes.forEach(n => {
      const t = n.node_type || "evidence";
      if (!groups[t]) groups[t] = [];
      groups[t].push(n);
    });
    return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  }, [nodes]);

  return (
    <div className={`col col-nodes${collapsed ? ' col-collapsed' : ''}`}
      style={{ flex: isExpanded ? `0 0 ${flex}%` : flex }}
      onClick={collapsed ? () => onExpand('nodes') : undefined}>
      <div className="col-header" onDoubleClick={() => onExpand('nodes')}>
        Nodes / 节点选择
        <span className="col-header-badge">{nodes.length}</span>
      </div>
      <div className="ns-scroll">
        {nodes.length === 0 && <div className="ns-empty">No nodes yet. Start a conversation to generate nodes.</div>}
        {grouped.map(([type, items]) => (
          <div key={type} className="ns-group">
            <div className="ns-group-header">
              <span className="ns-group-dot" style={{ background: NODE_COLORS[type] || "#999" }} />
              <span className="ns-group-label-en">{type.toUpperCase()}</span>
              <span className="ns-group-label-zh">{NODE_TYPE_ZH[type] || ""}</span>
              <span className="ns-group-count">{items.length}</span>
            </div>
            {items.map(n => (
              <div key={n.id} className={`ns-item ${n.id === selectedNodeId ? "selected" : ""}`}
                   onClick={() => onNodeSelect && onNodeSelect(n.id)}>
                <span className="ns-item-dot" style={{ background: NODE_COLORS[type] || "#999" }} />
                <span className="ns-item-label" title={n.content || n.label}>{n.label}</span>
                <span className="ns-item-conf">{Math.round((n.confidence || 0.8) * 100)}%</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Column 5: Strategy House (Canvas-rendered, on-demand)
// ════════════════════════════════════════════════════════════════

function drawStrategyHouse(canvas, nodes, isDark) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  // Responsive width: use container width up to 600px
  const containerW = canvas.parentElement ? canvas.parentElement.clientWidth - 24 : 560;
  const W = Math.min(Math.max(containerW, 320), 600);
  const H = 1200;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + "px"; canvas.style.height = H + "px";
  ctx.scale(dpr, dpr);

  const groups = { roof: [], pillar: [], foundation: [], internal: [], signal: [], action: [], external: [] };
  nodes.forEach(n => { const part = NODE_HOUSE_MAP[n.node_type] || "internal"; groups[part].push(n); });

  const bgColor = isDark ? "#1a1a2a" : "#FAFAF8";
  const textColor = isDark ? "#e0e0e0" : "#1a1a1a";
  const subtextColor = isDark ? "#aaa" : "#333";
  const watermark = isDark ? "#444" : "#ccc";

  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, W, H);

  const pad = 24, contentW = W - pad * 2;
  let y = pad;

  function roundRect(x, y, w, h, r, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.stroke(); }
  }

  function wrapText(text, maxW, font) {
    ctx.font = font;
    const lines = []; let line = "";
    for (const ch of text.split("")) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = ch; } else { line = test; }
    }
    if (line) lines.push(line);
    return lines;
  }

  function drawSection(meta, sectionNodes, startY, sectionW) {
    if (sectionNodes.length === 0) return startY;
    const innerPad = 10, lineH = 16;
    let totalH = 36;
    sectionNodes.forEach(n => {
      const lines = wrapText(n.label + (n.content ? " — " + n.content : ""), sectionW - innerPad * 2 - 16, "12px sans-serif");
      totalH += 8 + lines.length * lineH + 8;
    });
    const sectionBg = isDark ? meta.color + "18" : meta.bg;
    roundRect(pad, startY, sectionW, totalH, 6, sectionBg, meta.border);
    ctx.font = "bold 11px sans-serif"; ctx.fillStyle = meta.color;
    ctx.fillText(meta.label, pad + innerPad, startY + 22);
    let ny = startY + 36;
    sectionNodes.forEach(n => {
      const badgeColor = NODE_COLORS[n.node_type] || "#999";
      ctx.fillStyle = badgeColor;
      roundRect(pad + innerPad, ny, 6, 6, 3, badgeColor, null);
      const fullText = n.label + (n.content ? " — " + n.content : "");
      const lines = wrapText(fullText, sectionW - innerPad * 2 - 16, "12px sans-serif");
      ctx.font = "12px sans-serif"; ctx.fillStyle = subtextColor;
      lines.forEach((line, li) => { ctx.fillText(line, pad + innerPad + 14, ny + 6 + li * lineH); });
      const conf = Math.round((n.confidence || 0.5) * 100);
      ctx.font = "10px sans-serif"; ctx.fillStyle = isDark ? "#666" : "#999";
      ctx.fillText(`${conf}%`, pad + sectionW - innerPad - 30, ny + 6);
      ny += 8 + lines.length * lineH + 4;
    });
    return startY + totalH + 10;
  }

  ctx.font = "bold 18px sans-serif"; ctx.fillStyle = textColor;
  ctx.textAlign = "center";
  ctx.fillText("STRATEGY HOUSE / 战略屋", W / 2, y + 20);
  ctx.textAlign = "left"; y += 40;

  const roofH = 60 + groups.roof.length * 24;
  ctx.beginPath(); ctx.moveTo(W / 2, y); ctx.lineTo(pad, y + roofH); ctx.lineTo(W - pad, y + roofH); ctx.closePath();
  ctx.fillStyle = isDark ? "#F57F1718" : "#FFF8E1"; ctx.fill();
  ctx.strokeStyle = "#FFD54F"; ctx.lineWidth = 2; ctx.stroke();
  ctx.font = "bold 11px sans-serif"; ctx.fillStyle = "#F57F17";
  ctx.textAlign = "center"; ctx.fillText("VISION / 愿景", W / 2, y + 28);
  groups.roof.forEach((n, i) => {
    ctx.font = "13px sans-serif"; ctx.fillStyle = isDark ? "#FFD700" : "#B8860B";
    ctx.fillText(n.label.length > 35 ? n.label.slice(0, 33) + "..." : n.label, W / 2, y + 48 + i * 22);
  });
  ctx.textAlign = "left"; y += roofH + 4;

  if (groups.pillar.length > 0) {
    const pillarCount = groups.pillar.length, gap = 8;
    const pillarW = (contentW - gap * (pillarCount - 1)) / pillarCount, pillarH = 120;
    groups.pillar.forEach((n, i) => {
      const px = pad + i * (pillarW + gap);
      const pillarBg = isDark ? "#2E7D3218" : "#E8F5E9";
      roundRect(px, y, pillarW, pillarH, 4, pillarBg, "#81C784");
      ctx.font = "bold 11px sans-serif"; ctx.fillStyle = "#2E7D32";
      const label = n.label.length > (pillarW / 7) ? n.label.slice(0, Math.floor(pillarW / 7) - 2) + ".." : n.label;
      ctx.fillText(label, px + 8, y + 20);
      ctx.font = "11px sans-serif"; ctx.fillStyle = subtextColor;
      wrapText(n.content || "", pillarW - 16, "11px sans-serif").slice(0, 5).forEach((line, li) => {
        ctx.fillText(line, px + 8, y + 36 + li * 14);
      });
    });
    y += 120 + 10;
  }

  y = drawSection(HOUSE_SECTION_META.internal, groups.internal, y, contentW);
  y = drawSection(HOUSE_SECTION_META.foundation, groups.foundation, y, contentW);
  y = drawSection(HOUSE_SECTION_META.action, groups.action, y, contentW);
  y = drawSection(HOUSE_SECTION_META.signal, groups.signal, y, contentW);
  if (groups.external.length > 0) y = drawSection(HOUSE_SECTION_META.external, groups.external, y, contentW);

  ctx.font = "10px sans-serif"; ctx.fillStyle = watermark; ctx.textAlign = "center";
  ctx.fillText("Generated by Strategic Canvas", W / 2, y + 16); ctx.textAlign = "left";

  const finalH = y + 32;
  const croppedH = Math.min(finalH, H);
  const imgData = ctx.getImageData(0, 0, W * dpr, croppedH * dpr);
  canvas.height = croppedH * dpr; canvas.style.height = croppedH + "px";
  ctx.putImageData(imgData, 0, 0);
}

function StrategyHousePanel({ graphData, theme, flex, onExpand, isExpanded, collapsed }) {
  const canvasRef = useRef(null);
  const [generated, setGenerated] = useState(false);
  const [generating, setGenerating] = useState(false);
  const nodes = graphData?.nodes || [];
  const isDark = theme === "dark";

  const handleGenerate = () => {
    if (nodes.length === 0) return;
    setGenerating(true);
    setTimeout(() => { drawStrategyHouse(canvasRef.current, nodes, isDark); setGenerated(true); setGenerating(false); }, 300);
  };

  const handleDownload = () => {
    if (!canvasRef.current) return;
    const link = document.createElement("a");
    link.download = "strategy-house.png";
    link.href = canvasRef.current.toDataURL("image/png");
    link.click();
  };

  return (
    <div className={`col col-house${collapsed ? ' col-collapsed' : ''}`}
      style={{ flex: isExpanded ? `0 0 ${flex}%` : flex }}
      onClick={collapsed ? () => onExpand('house') : undefined}>
      <div className="col-header" onDoubleClick={() => onExpand('house')}>
        Strategy House / 战略屋
        {generated && <button className="download-btn" onClick={handleDownload}>&#8681; PNG</button>}
      </div>
      <div className="house-content">
        {!generated && (
          <div className="house-placeholder">
            <div className="house-placeholder-icon">&#9960;</div>
            <p>Complete your strategic conversation, then generate a Strategy House diagram.</p>
            <p className="house-placeholder-stats">{nodes.length > 0 ? `${nodes.length} nodes ready` : "No nodes yet"}</p>
            <button className="generate-btn" onClick={handleGenerate} disabled={nodes.length === 0 || generating}>
              {generating ? "Generating..." : "Generate Strategy / 生成战略"}
            </button>
          </div>
        )}
        <canvas ref={canvasRef} className="house-canvas" style={{ display: generated ? "block" : "none" }} />
        {generated && <button className="regenerate-btn" onClick={handleGenerate}>Regenerate / 重新生成</button>}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Settings Modal
// ════════════════════════════════════════════════════════════════

function SettingsModal({ onClose }) {
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("deepseek-chat");

  useEffect(() => {
    if (!window.electronAPI) return;
    window.electronAPI.getApiKey().then(k => setApiKey(k || ""));
    window.electronAPI.getModel().then(m => setModel(m || "deepseek-chat"));
  }, []);

  const handleSave = async () => {
    if (window.electronAPI) {
      await window.electronAPI.setApiKey(apiKey);
      await window.electronAPI.setModel(model);
    }
    onClose();
  };

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <h2>Settings / 设置</h2>
        <div className="settings-field">
          <label>DeepSeek API Key</label>
          <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="sk-..." />
        </div>
        <div className="settings-field">
          <label>Model</label>
          <select value={model} onChange={e => setModel(e.target.value)}>
            <option value="deepseek-chat">DeepSeek Chat</option>
            <option value="deepseek-reasoner">DeepSeek Reasoner</option>
          </select>
        </div>
        <div className="settings-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>Save</button>
        </div>
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
        {confidence > 0 && <span className="status-conf">confidence {Math.round(confidence * 100)}%</span>}
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
  const [theme, setTheme] = useState(() => localStorage.getItem("sc_theme") || "dark");
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
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [expandedCol, setExpandedCol] = useState(null);

  const project = projects.find(p => p.id === activeId) || projects[0];
  const { connected, send, on } = useIPC();

  const RATIOS = {
    null:      [2, 8, 3, 2, 1],
    sidebar:   [8, 2, 3, 1, 1],
    graph:     [1, 2, 8, 2, 1],
    nodes:     [1, 1, 2, 8, 2],
    house:     [1, 1, 2, 2, 8],
  };
  const flexes = RATIOS[expandedCol] || RATIOS[null];
  const handleExpand = (col) => setExpandedCol(prev => prev === col ? null : col);
  const isExpanded = expandedCol !== null;
  const total = flexes.reduce((a, b) => a + b, 0);
  const [sf, cf, gf, nf, hf] = flexes.map(f => (f / total * 100).toFixed(1));
  const collapsed = [sf, cf, gf, nf, hf].map(f => parseFloat(f) < 15);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("sc_theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === "dark" ? "white" : "dark");

  const updateProject = useCallback((updates) => {
    setProjects(prev => prev.map(p => p.id === activeId ? { ...p, ...updates } : p));
  }, [activeId]);

  useEffect(() => { saveProjects(projects, activeId); }, [projects, activeId]);

  // Load demo data
  useEffect(() => {
    if (demoLoaded) return;
    fetch("demo_graph.json")
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
        if (Object.keys(updates).length > 0) updateProject(updates);
        setDemoLoaded(true);
      })
      .catch(() => setDemoLoaded(true));
  }, [demoLoaded, updateProject]);

  // IPC handlers
  useEffect(() => {
    on("thinking", () => setThinking(true));
    on("response", (data) => {
      setThinking(false);
      if (data.error) {
        const errMsg = { speaker: "assistant", text: `[Error] ${data.message}` };
        setProjects(prev => prev.map(p => {
          if (p.id !== activeId) return p;
          return { ...p, messages: [...p.messages, errMsg] };
        }));
        return;
      }
      const newMsg = {
        speaker: "assistant", text: data.reply,
        invocations: data.invocations, latency_ms: data.latency_ms,
      };
      setProjects(prev => prev.map(p => {
        if (p.id !== activeId) return p;
        const updated = { ...p, messages: [...p.messages, newMsg] };
        if (data.canvas?.nodes) {
          updated.graphData = { nodes: data.canvas.nodes || p.graphData.nodes, links: data.canvas.links || p.graphData.links };
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

  const handleSend = useCallback((text) => {
    updateProject({ messages: [...project.messages, { speaker: "user", text }] });
    send({ type: "chat", text });
  }, [send, project, updateProject]);

  const handleNewProject = () => {
    const p = createEmptyProject("New Project " + (projects.length + 1));
    setProjects(prev => [p, ...prev]);
    setActiveId(p.id);
  };

  return (
    <div className="app">
      <div className="app-header">
        <h1 onClick={() => setExpandedCol(null)} style={{cursor:'pointer'}}>Strategic Canvas</h1>
        <div className="header-right">
          <span className="node-count">{project.graphData?.nodes?.length || 0} nodes</span>
          <button className="theme-toggle" onClick={() => setShowSettings(true)} title="Settings">&#9881;</button>
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
            {theme === "dark" ? "☀" : "☾"}
          </button>
        </div>
      </div>
      <div className="app-main">
        <ProjectSidebar
          projects={projects} activeId={activeId}
          onSelect={setActiveId} onNew={handleNewProject}
          onRename={(id, name) => setProjects(prev => prev.map(p => p.id === id ? { ...p, name } : p))}
          onDelete={(id) => { setProjects(prev => { const next = prev.filter(p => p.id !== id); if (activeId === id && next.length > 0) setActiveId(next[0].id); return next; }); }}
          flex={sf} onExpand={handleExpand} isExpanded={isExpanded} collapsed={collapsed[0]}
        />
        <ChatPanel messages={project.messages} onSend={handleSend} thinking={thinking}
          flex={cf} onExpand={handleExpand} isExpanded={isExpanded} collapsed={collapsed[1]}
        />
        <Graph3DPanel graphData={project.graphData} selectedNodeId={selectedNodeId} onNodeSelect={setSelectedNodeId}
          flex={gf} onExpand={handleExpand} isExpanded={isExpanded} collapsed={collapsed[2]}
        />
        <NodeSelectorPanel graphData={project.graphData} selectedNodeId={selectedNodeId} onNodeSelect={setSelectedNodeId}
          flex={nf} onExpand={handleExpand} isExpanded={isExpanded} collapsed={collapsed[3]}
        />
        <StrategyHousePanel graphData={project.graphData} theme={theme}
          flex={hf} onExpand={handleExpand} isExpanded={isExpanded} collapsed={collapsed[4]}
        />
      </div>
      <StatusBar
        stage={project.stage || "explore"} confidence={project.confidence || 0}
        connected={connected} projectName={project.name}
      />
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
