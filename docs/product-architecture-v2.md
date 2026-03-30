# Strategy Canvas — Product Architecture V2

**Date:** 2026-03-30
**Status:** Definitive product vision

---

## One-Line

A convergence engine: AI-guided strategic dialogue that progressively crystallizes into a precise strategic architecture, named concepts, and actionable conclusions.

## Core Belief

Strategy is subtraction. The product's job is to take ambiguity and compress it into:
1. A name for the unnamed (consensus vocabulary)
2. A picture that makes 80% of people instantly understand (strategic diagram)
3. A sentence that drives action (golden phrase / declaration)

## Five-Panel Architecture

```
┌────────┬────────────┬─────────────┬────────────┬──────────┐
│ AGENT  │   CHAT     │  3D GRAPH   │ STRATEGY   │ EXPORT   │
│        │            │             │ HOUSE      │          │
│ Memory │ Skills-    │ Progressive │ Progressive│ External │
│ Track  │ guided     │ enrichment  │ clarity    │ render   │
│ Judge  │ dialogue   │ & weight    │ & naming   │ (NLM)   │
│        │            │             │            │          │
│ Panel 1│  Panel 2   │  Panel 3    │  Panel 4   │ Panel 5  │
└───┬────┴────────────┴─────────────┴────────────┴────┬─────┘
    └─────────────── CONTEXT LOOP ◄───────────────────┘
```

### Panel 1: Agent (Convergence Tracker)

**What it is:** A persistent meta-agent that observes the entire process. Not a chatbot — a judge and memory system.

**What it does:**
- Maintains a running "state of understanding" — what's been established, what's still vague, what's contradictory
- Tracks which of the 30 skills have been applied and which gaps remain
- Monitors convergence: are we getting clearer or going in circles?
- Provides proactive feedback: "We've discussed resources but haven't tested any assumptions. Consider running decision-bias-detection next."
- Builds long-term memory across sessions — knows the user's strategic context, past decisions, vocabulary preferences
- Feeds all context from panels 2-5 back into its understanding

**Key principle:** The agent must give DEFINITIVE feedback. "Based on what we've covered, your strategy has a clear gap in X. I recommend addressing it before proceeding." Not "you might want to consider..."

**Display:** Compact status panel showing:
- Convergence score (how crystallized is the strategy?)
- Skills coverage (which frameworks have been applied?)
- Open questions (what's still unresolved?)
- Agent's current assessment (1-2 sentences)

### Panel 2: Dialogue (Skills-Guided Deep Discussion)

**What it is:** Human-AI conversation guided by the 30 strategy skills.

**What it does:**
- AI coach applies professional strategy frameworks in structured sequence
- Each skill has a natural flow: some need external data (trigger research), some need user input (request uploads), some need market data (web search)
- The dialogue has STRUCTURE — not free-form chat. The agent (Panel 1) suggests which skill to apply next based on gaps
- When a skill requires external input, the system pauses and assists: "To apply Porter's Five Forces properly, I need industry data. Can you upload a market report, or should I search for recent analysis?"
- Key moments are flagged: when the user says something that could become a "named concept" or "golden phrase," the AI recognizes it and proposes crystallization

**Key principle:** The 30 skills are not a toolbox for browsing. They're a structured professional process. Skipping steps generates warnings.

**Interaction patterns:**
- Skill-guided questions (AI asks, user answers)
- Data requests (AI needs information, triggers search or upload)
- Naming moments ("You just described something important. Can we call this the 'assumption gap'?")
- Convergence checkpoints ("We've covered 4 of 6 key areas. Ready to synthesize?")

### Panel 3: 3D Graph (Progressive Enrichment)

**What it is:** A living 3D neural network that grows and refines as the conversation deepens.

**What it does:**
- New nodes appear with physics animation as the dialogue generates them
- Node weights adjust as more evidence accumulates (larger = more validated)
- Edge strengths change as relationships become clearer
- Quantitative data gets encoded: uploaded numbers become node properties visible on hover
- Multiple visual dimensions: color (type), size (weight/importance), brightness (confidence), position (time/certainty/influence axes)
- Guided camera narration: AI flies camera to relevant clusters during key insights

**Progressive behavior:**
- Turn 1-2: sparse graph, large uncertainty, nodes floating loosely
- Turn 3-4: clusters forming, some edges thickening, weights differentiating
- Turn 5-6: clear structure emerging, high-confidence core, peripheral uncertainties fading
- Final: a crystallized graph where the important stands out and the noise is suppressed

**Key principle:** The 3D graph is not decoration. It's a spatial argument. Where a node IS tells you something. What it's connected to tells you something. What's NOT connected tells you something.

### Panel 4: Strategy House (Progressive Crystallization)

**What it is:** The structured strategic output that progressively clarifies as the conversation and 3D graph evolve.

**What it does:**
- Starts empty or with a skeleton structure
- As dialogue covers more ground, sections fill in with increasing clarity
- Multiple output patterns available (auto-detected or user-selected):
  - **Strategy House (战略屋):** roof=vision, pillars=strategic options, foundation=resources/capabilities
  - **Four Quadrant Analysis (四象限):** 2x2 matrix positioning
  - **Decision Fork:** tension → options → criteria → recommendation
  - **Causal Chain:** if-then logic flow
  - **Risk Radar:** threats + mitigations
  - **Convergence Map:** from many inputs → few conclusions
- Each pattern includes THREE output layers:
  1. **The Diagram** — visual architecture (SVG/canvas, printable)
  2. **Named Concepts** — vocabulary created during the session ("假设缺口", "轻量验证", etc.)
  3. **Golden Phrases** — 1-3 conclusive sentences. CEO elevator pitch. Actionable. Definitive.

**Golden Phrase examples:**
- "先验证，后投入。用三个最小实验测试三个最大假设。"
- "我们的护城河不是技术，是对AI教育的深度理解。技术是工具。"
- "这不是创业决策，是一个可逆的探测行动。失败成本=两个月周末。"

**Key principle:** The diagram helps people UNDERSTAND. The golden phrases help people ACT. Both are required. A strategy house without a crisp conclusion is an unfinished analysis.

**AI generation:** The AI coach generates the Strategy House and golden phrases as a draft. The draft improves through continued dialogue — user can say "that phrase isn't right, the real point is..." and the AI refines. The output is the result of near-infinite conversational iteration, not a one-shot generation.

### Panel 5: Export / External Rendering

**What it is:** Takes Panel 4's output and renders it as a polished, shareable artifact.

**What it does:**
- Exports the Strategy House + golden phrases as structured input to external tools
- Primary target: NotebookLM-style tools that can generate clean, professional diagrams
- Also supports: PNG export, PDF export, print-ready format
- The exported artifact is self-contained: someone who wasn't in the session can look at it and understand the strategy

**Key principle:** The export is the "deliverable" — what gets shared in the boardroom, printed on the wall, sent to stakeholders. It must look like it came from a top-tier consulting firm.

## The Convergence Loop

```
SESSION START
    │
    ▼
[Agent assesses] → "Let's start with understanding your core tension"
    │
    ▼
[Dialogue: Skill 1] → [Nodes appear in 3D] → [Strategy House: skeleton]
    │
    ▼
[Agent: "Good. Now let's test your assumptions"]
    │
    ▼
[Dialogue: Skill 2] → [More nodes, edges thicken] → [House: pillars forming]
    │
    ▼
[Agent: "I need market data to proceed"] → [Web search / user upload]
    │
    ▼
[Dialogue: Skill 3 with data] → [Weights quantified] → [House: details filling]
    │
    ▼
[Agent: "I see a naming opportunity"] → "Let's call this the 'validation gap'"
    │
    ▼
[Dialogue: Skills 4-6] → [Graph crystallizing] → [House: nearly complete]
    │
    ▼
[Agent: "Convergence score: 8/10. Ready to synthesize?"]
    │
    ▼
[AI generates golden phrases] → [User refines] → [Final output]
    │
    ▼
[Export to NotebookLM] → [Polished diagram + conclusions]
    │
    ▼
[ALL CONTEXT → feeds back to Agent memory for next session]
```

## Product Principles

1. **Definitive > Perfect.** Give clear answers. "Based on current evidence, do X. If Y happens, reconsider." Never "there are many ways to think about this."

2. **Naming = Highest Value.** When the AI or user coins a term for something previously vague, that's the product's peak moment. Highlight it. Save it. Use it consistently from that point forward.

3. **Golden Phrase = Action Trigger.** Every completed analysis must produce 1-3 sentences that a CEO can repeat in an elevator. If you can't compress it to that, the analysis isn't done.

4. **Process = Quality.** The 30 skills define a professional process. The agent tracks coverage. Skipping steps = warnings. Thoroughness is not optional.

5. **Convergence, Not Divergence.** Strategy is subtraction. The product's job is to NARROW, not expand. Every dialogue turn should either add clarity or identify what's still unclear. Going in circles triggers agent intervention.

6. **The Diagram Explains, The Words Decide.** Visual output (strategy house, quadrant, etc.) makes people understand. Text output (golden phrases, named concepts) makes people act. Both required, always.

## Technical Architecture (High Level)

```
┌─────────────────────────────────────────┐
│            Frontend (Web)               │
│  5-panel layout, 3D graph, SVG output   │
├─────────────────────────────────────────┤
│          Agent Orchestrator             │
│  Session state, convergence tracking,   │
│  skill routing, memory management       │
├─────────────────────────────────────────┤
│           LLM Layer                     │
│  Dialogue generation, node extraction,  │
│  golden phrase synthesis, naming        │
├─────────────────────────────────────────┤
│         Strategy Skills (30)            │
│  Structured prompts, data requirements, │
│  output templates, skill sequencing     │
├─────────────────────────────────────────┤
│        External Integration             │
│  Web search, data upload, NotebookLM,   │
│  export rendering                       │
├─────────────────────────────────────────┤
│         Persistence                     │
│  Session history, agent memory,         │
│  named concepts registry, user profile  │
└─────────────────────────────────────────┘
```

## What We Have Now vs. What We Need

| Component | Current State | Target |
|-----------|--------------|--------|
| Panel 1 (Agent) | Not built | Convergence tracker + memory |
| Panel 2 (Chat) | Basic input box, static demo | Skills-guided dialogue loop |
| Panel 3 (3D Graph) | Working, force-directed | Progressive enrichment + camera narration |
| Panel 4 (Strategy House) | HTML cards, no golden phrases | Diagram patterns + naming + golden phrases |
| Panel 5 (Export) | Print window | NotebookLM integration + polished output |
| Skills | 30 .md files, not connected | Integrated into dialogue flow |
| LLM | Not connected | Core engine for all generation |
| Context Loop | Not built | Full closed loop 1→5→1 |

## Implementation Priority

**Phase 1 (Demo Enhancement):**
- Pre-scripted agent narration for existing demo data
- Strategy House diagram renderer (SVG) with proper architectural layout
- Golden phrase generation (pre-written for demo, template for LLM)
- Camera storytelling for 3D graph

**Phase 2 (Live AI Loop):**
- Connect LLM to dialogue (real chat, not static)
- Skill-guided conversation flow (agent suggests next skill)
- Real-time node generation from dialogue
- AI-generated Strategy House + golden phrases

**Phase 3 (Full Product):**
- 5-panel layout
- Agent memory and convergence tracking
- External data integration (search, upload)
- NotebookLM export pipeline
- Named concepts registry
- Multi-session persistence
