# Design Doc: Strategy Canvas — Product Vision

**Project:** Strategy Canvas
**Date:** 2026-03-30
**Status:** Draft v2 (post office-hours)

---

## Product in One Sentence

An AI strategic coach that turns conversation into a 3D strategy graph, and distills it into a precise, visual takeaway — a named diagram + sharp conclusion text — that makes 80% of people instantly understand what took hours to discuss.

---

## Three Design Principles (from founder)

### 1. Visualization as Compression

The goal is not "pretty graphs." The goal is: **take complex, multi-dimensional strategic information and compress it into a visual form so clear that people who couldn't understand the discussion can now understand the conclusion — and act on it.**

The output must be stable, precise, and substantive. Not decoration. A tool for thinking and communication.

### 2. Consensus = Naming

From real strategy consulting experience: the mark of a perfect strategy session is consensus. And the mark of consensus is **naming**.

- Giving a name to something vague ("we call this the 'assumption gap'")
- Defining a clear goal or boundary ("we only compete in X, not Y")
- A memorable slogan or declaration ("验证优先，投入在后")

When vague things get names, future communication becomes efficient. Organizations become efficient. The AI coach must be excellent at this: proposing precise names for fuzzy patterns.

### 3. Diagrams for Understanding, Text for Action

Visualization helps people **understand**. But conclusions are **text**.

The final takeaway is always: **one diagram + a few sharp sentences**. Never a diagram alone (people won't act). Never text alone (people won't understand). Both, together.

---

## Output Pyramid

```
         ┌──────────┐
         │  命名     │  ← Highest value
         │  + 结论   │     "We call it the 'assumption gap'"
         │  (text)   │     "Validate before you invest"
         ├──────────┤
         │  战略图   │  ← Makes complex things simple
         │  (diagram)│     Strategy House, quadrant, causal chain
         ├──────────┤
         │  元素     │  ← Raw analytical material
         │  (graph)  │     3D neural graph, nodes, edges
         └──────────┘
```

Current product only has the bottom layer. This design adds the middle and top.

---

## Core Product Loop

```
User speaks → AI generates/updates (graph + diagram + naming + conclusion)
    → User sees output on blackboard → User reacts ("这个名字不准确", "结论太模糊")
    → AI refines → ... (unlimited conversation depth)
```

The blackboard output is a **living document** that evolves with conversation. Each turn may:
- Sharpen a name ("'技术优势' is too vague → '深度AI素养教育壁垒'")
- Restructure the diagram (new pillar added to strategy house)
- Tighten a conclusion ("先验证三个假设" → "用30人小班课验证需求假设，4周出结果")

---

## Blackboard Output Structure

The blackboard shows a single, evolving **Strategic Takeaway** document:

```
┌─────────────────────────────────────────────┐
│  STRATEGIC TAKEAWAY                         │
│  ─────────────────                          │
│                                             │
│  ▎ 命名 (Named Concepts)                   │
│  ─────────────────────                      │
│  • "假设缺口" — 三个核心假设未经验证        │
│  • "不下牌桌探测" — 不辞职的最小验证策略     │
│  • "深度AI素养壁垒" — 区别于字节/网易的定位  │
│                                             │
│  ▎ 战略架构图                                │
│  ─────────────────────                      │
│                                             │
│       ┌─────────────────────┐               │
│       │ 成为AI素养教育第一品牌 │  ← 愿景      │
│       └──────┬────────┬─────┘               │
│         ┌────┴───┐ ┌──┴─────┐               │
│         │小班课验证│ │内容壁垒 │  ← 战略支柱   │
│         └────┬───┘ └──┬─────┘               │
│       ┌──────┴────────┴──────┐              │
│       │ AI技术积累 + 行业人脉  │  ← 资源基础  │
│       └──────────────────────┘              │
│                                             │
│   ⚠ 技术优势假设未验证  ⚠ 市场窗口不确定     │
│                                             │
│  ▎ 结论                                     │
│  ─────────────────────                      │
│  核心判断：条件具备，但有"假设缺口"。         │
│  行动指令：用4周小班课验证需求假设，            │
│  不辞职，不投入，先拿到数据再决策。            │
│                                             │
│  一句话：验证优先，投入在后。                  │
│                                             │
└─────────────────────────────────────────────┘
```

### Three Sections, Always Present

1. **命名 (Named Concepts)** — AI-proposed names for vague patterns discovered in conversation. Each name is a handle for a previously unnamed strategic insight. Marked with quotes and a one-line definition.

2. **战略架构图 (Strategic Diagram)** — One of several diagram types, auto-selected based on content:
   - **战略屋 (Strategy House)** — vision on top, pillars = strategic options, foundation = resources/capabilities, warning signs outside
   - **四象限 (Quadrant)** — 2x2 matrix for positioning/prioritization
   - **因果链 (Causal Chain)** — if A then B then C, for action sequences
   - **决策树 (Decision Fork)** — branching options with tradeoffs
   - **风险地图 (Risk Map)** — probability vs impact scatter

3. **结论 (Conclusion)** — 3-5 sentences max. Must include:
   - Core judgment (一句话判断)
   - Action directive (下一步做什么)
   - Memorable tagline (朗朗上口的一句话)

---

## Guided Camera Storytelling

The AI coach tells stories THROUGH the 3D graph. When the coach generates a new insight, it also produces a camera choreography:

| Move | What It Does | When Used |
|------|-------------|-----------|
| `fly_to` | Camera swoops to a node | "Look at this assumption..." |
| `orbit` | Camera circles a cluster | "Your risks are all concentrated here" |
| `highlight_path` | Lights up a chain, fades rest | "This is your weakest causal link" |
| `fade_except` | Shows only key nodes | "Strip the noise. Core decision = these two" |
| `strategy_house` | Reorganizes graph into 战略屋 | "Let me show you the structure" |
| `pull_back` | Wide angle, full view | "Now let's see the whole picture" |

The narration text appears on the blackboard, synced with camera moves. After narration, the blackboard retains the Strategic Takeaway as a permanent document.

---

## AI Coach Capabilities

The coach must be excellent at:

1. **Naming** — proposing precise, memorable names for vague patterns
   - Input: scattered assumptions mentioned across conversation
   - Output: "I'm going to call this the '假设缺口' — you have three core assumptions supporting your entire strategy, and none have been validated"

2. **Diagram selection** — choosing the right visual form for the content
   - 6+ node types present → Strategy House
   - Binary choice + tradeoffs → Decision Fork
   - Sequential actions → Causal Chain / Action Roadmap
   - Positioning question → Quadrant

3. **Conclusion writing** — sharp, actionable, memorable
   - Not summaries. Judgments.
   - "Your strategy has an assumption gap" (judgment)
   - "Validate demand with a 30-person pilot in 4 weeks" (action)
   - "验证优先，投入在后" (tagline)

4. **Iterative refinement** — improving output through conversation
   - User: "这个名字不好"
   - Coach: proposes alternatives, explains reasoning
   - User: "结论太保守"
   - Coach: sharpens the conclusion, adds edge

---

## Implementation Phases

### Phase 1: Static Demo with Pre-generated Takeaway
- Pre-write the Strategic Takeaway for the existing demo conversation
- Render the three sections (naming, diagram, conclusion) on the blackboard
- Implement Strategy House as an HTML/CSS diagram (not SVG boxes)
- Add camera fly-to and highlight-path functions to 3D graph
- Pre-script one narration sequence for the demo

### Phase 2: LLM-Generated Takeaway
- Prompt engineering: coach returns structured JSON with naming, diagram data, conclusion
- Each strategy skill has a takeaway template
- Verdict is LLM-generated with real strategic judgment
- Blackboard updates live as conversation progresses

### Phase 3: Interactive Refinement Loop
- User can click/edit any name, conclusion, or diagram element
- Coach responds to edits with refined alternatives
- Conversation history tracks how the takeaway evolved
- Export final takeaway as PDF/PNG with professional formatting

### Phase 4: Camera Narration
- Full camera choreography system
- Coach generates camera moves alongside insights
- Play/pause/scrub narration timeline
- Strategy House 3D view (graph reorganizes into house formation)

---

## Open Questions

1. Should the AI coach speak Chinese, English, or auto-detect from user language?
2. How to handle the "naming" quality — LLM-generated names tend to be generic. Need prompt engineering to make them sharp and specific.
3. Should the tagline/slogan be generated or offered as options for user to choose?
4. Export format: PDF with embedded diagram? Or interactive HTML that can be shared?
5. Can the Strategy House diagram be interactive (click a pillar to expand)?
