# Design Doc: Strategic Narration — Guided Camera Storytelling

**Project:** Strategy Canvas
**Date:** 2026-03-30
**Status:** Draft

---

## What This Is

An AI coach that tells stories THROUGH a 3D strategy graph. Instead of just generating nodes and edges, the coach produces **camera choreography** — a sequence of fly-tos, orbits, highlights, and fades that turn a static 3D visualization into a narrative experience.

The user chats about their strategic situation. The AI applies strategy frameworks (Mintzberg, Porter, BCG, etc.), generates graph elements, AND scripts a camera sequence that walks the user through the insight.

"Let me show you something" becomes the product's signature moment.

## Why This Matters

- **Nobody has this.** AI chat exists. Strategy tools exist. 3D graphs exist. An AI narrator that flies a camera through your strategy to tell you a story? That's new.
- **Spatial reasoning is powerful.** Seeing that your three key assumptions are clustered together (fragile) vs. spread across the graph (resilient) communicates something text cannot.
- **The camera IS the insight.** Where the coach points the camera reveals what matters. A zoom into a disconnected node says "this is orphaned" better than any text summary.

## Core Data Model Addition

Each coach turn produces not just `GraphDiff` (nodes + edges) but also a `NarrationSequence`:

```python
@dataclass
class CameraMove:
    type: str          # fly_to | orbit | highlight_path | fade_except | pull_back | split_view
    target: str | None # node_id for fly_to
    targets: list[str] # node_ids for highlight/fade
    center: tuple[float, float, float] | None  # for orbit
    duration_ms: int   # animation duration
    narration: str     # coach voiceover text (displayed in blackboard)
    pause_ms: int      # pause after move before next

@dataclass
class NarrationSequence:
    title: str         # e.g. "Your Assumption Gap"
    moves: list[CameraMove]
    conclusion: str    # final verdict after sequence
```

## Camera Move Types

| Move | What It Does | When Coach Uses It |
|------|-------------|-------------------|
| `fly_to` | Camera swoops to a specific node | "Look at this assumption..." |
| `orbit` | Camera circles around a point | "Let's see the full picture from all angles" |
| `highlight_path` | Lights up a chain of connected nodes, fades everything else | "This causal chain is your weakest link" |
| `fade_except` | Fades all nodes except a subset | "Strip away the noise. Your core decision is between these two" |
| `pull_back` | Camera pulls to wide angle | "Now let's zoom out and see the whole strategy" |
| `cluster_focus` | Camera flies to the centroid of a node-type cluster | "All your risks are concentrated here" |

## UX Flow

### During Chat
1. User describes strategic situation in left panel
2. AI coach responds with text + generates nodes/edges
3. New nodes animate into the 3D graph with physics
4. A "Play Insight" button appears on the coach's response

### Narration Playback
1. User clicks "Play Insight" (or coach auto-plays for key moments)
2. Left panel shows narration text, highlighted phrase by phrase
3. 3D graph executes camera moves in sequence
4. Right panel (blackboard) builds the structured conclusion as narration progresses
5. Each section of the blackboard appears as the relevant camera move plays
6. User can pause, skip forward, replay

### Controls
- Play/Pause button on the 3D view
- Timeline scrubber showing narration progress
- Click any narration text segment to jump to that camera move
- Speed control (0.5x, 1x, 1.5x, 2x)

## Blackboard Integration

The blackboard becomes the **script view** during narration:

```
[Playing: "Your Assumption Gap"]

> 看到这三个假设吗？它们支撑着你整个战略...  ← highlighted, camera at assumptions
>
> 但没有一个有验证信号。                        ← camera highlights missing edges
>
> 你的计划远看很完整...                         ← camera pulls back
>
> 但近看，这个能力完全是孤立的。                 ← camera flies to disconnected resource

─────────────────────────────────

VERDICT (AI-generated):
你的战略有一个明显的"假设缺口"。三个核心假设
（技术优势、市场需求、时间窗口）都没有经过验证。
建议：在做任何大决策之前，设计三个最小实验来测试
这些假设。最紧急的是"市场需求"——因为如果没有
需求，技术优势毫无意义。
```

After playback, the blackboard retains the structured conclusion as a static document.

## Implementation Phases

### Phase 1: Camera API (Demo)
- Add `flyToNode(id, duration)`, `orbitPoint(xyz, radius, duration)`, `highlightPath(ids)`, `fadeExcept(ids)` to the 3D graph
- Pre-script 2-3 narration sequences for the existing demo data
- Play/pause UI on the 3D panel
- Narration text display in blackboard, synced to camera moves

### Phase 2: LLM-Generated Narrations
- Prompt engineering: coach returns `narration_sequence` JSON alongside text response
- Each strategy skill has a narration template (e.g., icarus-paradox always does "zoom to the strength, then show the rigidity trap")
- Verdict is LLM-generated, not string concatenation

### Phase 3: Interactive Narration
- User can interrupt: "Wait, go back to that assumption"
- Coach adapts narration based on what user clicks/highlights
- Branch narrations: "If you choose Option A, here's what happens..." (camera shows path A), "If Option B..." (camera shows path B)

## Strategy House (战略屋) View

A special camera sequence that reorganizes the 3D graph into a Strategy House formation:

```
        ┌─────────────────┐
        │   GOAL (roof)   │         ← y=top
        └────┬───────┬────┘
             │       │
      ┌──────┴──┐ ┌──┴──────┐
      │ Option A│ │ Option B│      ← y=mid, pillars
      └────┬────┘ └────┬────┘
           │           │
    ┌──────┴───────────┴──────┐
    │   Resources + Evidence  │    ← y=bottom, foundation
    └─────────────────────────┘

    Risks float outside as warning indicators
    Assumptions shown as cracks in the pillars
```

This is a camera move type: `{ type: "strategy_house" }` that:
1. Pauses force simulation
2. Smoothly repositions nodes into the house layout
3. Camera orbits slowly to show the 3D structure
4. Returns to free layout when user clicks "Free View"

## Technical Notes

- `3d-force-graph` supports `cameraPosition()` with animation via TWEEN
- Node highlighting: change material emissive + opacity on non-highlighted nodes
- Path highlighting: change link material + add particle flow on highlighted edges
- For smooth camera sequences, use a simple state machine that chains moves via setTimeout/requestAnimationFrame

## Open Questions

1. Should narration auto-play or require user click?
2. Audio narration (TTS) for the coach voiceover? Or text only?
3. Multiple simultaneous narrations when graph gets complex?
4. Export narration as video (screen recording of the camera sequence)?
