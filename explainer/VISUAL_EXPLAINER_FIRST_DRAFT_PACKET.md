# Tactical Clearability — Visual Explainer First-Draft Packet

**Status:** first-draft design packet  
**Purpose:** handoff specification for the first public-facing visual explainer and reusable paper graphics.  
**Primary audience:** players, designers, technical readers, reviewers, and collaborators who should understand the core result before seeing the mathematics.

---

## 1. Communication Goal

The visual system should make one idea immediately intuitive:

> A map can be physically reachable and visually valid while revealing threat information faster than one player can act on it.

The explainer should progressively establish four ideas:

1. **Counting sightlines is not enough.**
2. **The reticle is a single serial resource.**
3. **Geometry determines when threat information arrives and how far the reticle must travel.**
4. **Prior map knowledge can let the player begin orienting before a threat becomes visible.**

The viewer should be able to understand the central result without knowing scheduling theory, PCG, ViZDoom, or real-time systems.

---

# 2. Shared Visual Language

All figures and animations should use the same symbols.

| Concept | Visual treatment |
|---|---|
| Player | filled circular marker with heading wedge |
| Player path | solid centerline with direction arrow |
| Wall / occluder | heavy dark polygon / line |
| Hidden threat | hollow threat marker |
| Visible threat | filled threat marker |
| Threat bearing | thin ray from player to target |
| Predicted / known-before-reveal bearing | dashed ray |
| Reticle direction | bold rotating arrow/wedge centered on player |
| Reveal event | pulse/ring on target + marker on timeline |
| Deadline | vertical bar on target timeline |
| Service interval | horizontal block on timeline |
| Successful service | check mark / completed block |
| Deadline breach | X / skull marker |
| Positive tactical margin | safe side of zero line |
| Negative tactical margin | overloaded side of zero line |
| Current time | vertical cursor shared between map and timeline |

Color should be secondary to shape and labels so figures remain understandable when printed grayscale or viewed with color-vision deficiencies.

### Typography / labeling rules

- Use plain-English label first, mathematical symbol second.
  - `Reveal time (r₁)`
  - `Deadline (D₁)`
  - `Tactical margin (M)`
- Avoid showing more than one equation in the first screenful.
- Never lead a general-audience panel with `L*`.
- Use milliseconds in public-facing explanatory panels, with tics in smaller technical annotations where useful.

---

# 3. Visual 1 — “Two Rooms: Counting Sightlines Predicts the Wrong Answer Twice”

## Purpose

This is the primary static infographic and the opening interactive example.

It demonstrates that peak physical LOS / threat count is neither sufficient nor necessary for tactical clearability.

## Composition

Use a horizontal split-screen layout.

### Left panel — LOW COUNT, UNSERVICEABLE

Headline:

> **Only two threats — but the fight is impossible under the model.**

Map:

- simple player approach toward a corner;
- two threat apertures become visible almost simultaneously;
- large angular separation between bearings;
- show reticle initially centered;
- both reveal rays appear together.

Timeline beneath map:

```text
Threat A    REVEAL ├──────────── DEADLINE
                  TURN → ACQUIRE → SERVICE ✓

Threat B    REVEAL ├──────────── DEADLINE
                                  TURN ─── X
```

Summary card:

```text
Visible threats:      2
Static heuristic:     PASS
Tactical margin:      NEGATIVE
Outcome:              UNSERVICEABLE
```

Plain-language caption:

> The room does not fail because two targets are visible. It fails because they become urgent at nearly the same time and require too much reticle travel to service sequentially.

### Right panel — HIGHER COUNT, SERVICEABLE

Headline:

> **Three threats — but the fight is clearable.**

Map:

- same visual grammar;
- threats reveal sequentially along player motion;
- bearings form a smooth sweep rather than an abrupt cross-screen switch.

Timeline:

```text
Threat A    REVEAL ├──────── DEADLINE
                  SERVICE ✓

Threat B          REVEAL ├──────── DEADLINE
                        SERVICE ✓

Threat C                REVEAL ├──────── DEADLINE
                              SERVICE ✓
```

Summary card:

```text
Visible threats:      3
Static heuristic:     FAIL
Tactical margin:      POSITIVE
Outcome:              CLEARABLE
```

### Final punchline

Centered beneath both panels:

> **Counting sightlines predicts the wrong answer twice. Timing and angular sequence matter.**

## Animation behavior

For HTML version:

1. Player dot advances automatically.
2. Reveal rays activate at their true reveal points.
3. Timeline jobs appear exactly when their threats reveal.
4. Reticle rotates at the declared rate.
5. Left case visibly misses one deadline.
6. Right case clears sequentially.
7. Animation can pause/replay.

## Acceptance criteria

A viewer unfamiliar with the research should be able to answer after viewing:

- Why can two threats be worse than three?
- Why is sightline count insufficient?
- What role does the crosshair play?

---

# 4. Visual 2 — “Geometry Creates a Scheduling Problem”

## Purpose

This is the main system/paper Figure 1 and the conceptual bridge from FPS geometry to scheduling.

## Layout

Four linked panels from left to right.

### Panel A — Geometry

Show:

- simple room polygon;
- walls / occluders;
- route `γ(s)`;
- 2–3 threat anchors;
- current player position;
- one critical grazing LOS ray.

Caption:

> **1. Geometry decides when each threat becomes visible.**

### Panel B — Reveal timeline

For each threat, show:

- reveal time `r_j`;
- deadline `D_j`;
- available response window.

Example:

```text
TIME →
T1       ●────────────────| 
         reveal           deadline

T2             ●──────────|

T3                  ●─────|
```

Caption:

> **2. Every reveal creates a time-sensitive job.**

### Panel C — Single reticle

Show a circular dial or simplified field-of-view arc with target bearings.

Animate or diagram:

```text
+65° → 0° → -55°
```

Reticle traversal consumes time.

Caption:

> **3. One crosshair must service those jobs one at a time.**

Small explanatory line:

> Turning farther takes longer; the next target depends on where the reticle ended previously.

### Panel D — Tactical margin / contract

Show:

```text
Required completion     620 ms
Available deadline      700 ms
--------------------------------
Tactical margin         +80 ms ✓
```

Then a small representation of the module contract matrix / port interface.

Caption:

> **4. The result becomes a reusable tactical contract for procedural composition.**

## Animated version

Use one shared time cursor across Panels A–C.

As time advances:

- player moves on map;
- threats reveal;
- jobs appear on timeline;
- reticle dial rotates;
- service bars complete;
- margin counter updates.

The fourth panel appears only after the encounter completes.

## General-audience explanatory text

> The map does not directly say “this room is fair.” It creates a sequence of information. We ask whether one player can process that sequence before the danger becomes lethal.

## Paper use

Static version can be rendered directly from the same SVG primitives and exported to SVG/PDF/PNG later.

---

# 5. Visual 3 — “How Much Knowledge Does This Room Require?”

## Purpose

This is the signature interactive visualization for the actionable-information concept and a natural home for the proposed finite lead-time experiment.

Core variable:

\[
a_j(\ell)=\max(0,r_j-\ell)
\]

where `ℓ` is advance knowledge / setup lead time.

The public-facing phrasing should be:

> **How early do you need to know where to aim?**

## Layout

Three vertical zones.

### Zone A — Encounter map

Show one knowledge-rescuable encounter, ideally the F3-style pivot.

Elements:

- player moving toward aperture;
- threat hidden until reveal;
- reticle direction;
- dashed predicted bearing when prior knowledge is available;
- solid LOS only after reveal.

### Zone B — Knowledge slider

Control:

```text
ADVANCE MAP KNOWLEDGE
0 ms ───────────────●────────────── 300 ms
```

Labels at useful positions:

- `0 ms — react only after reveal`
- `critical lead ℓ*`
- `full pre-aim`

The critical point should snap/highlight when crossed.

### Zone C — Live tactical result

Large margin display:

```text
TACTICAL MARGIN

-114 ms      UNSERVICEABLE
```

As slider increases:

```text
 -57 ms      UNSERVICEABLE
   0 ms      BOUNDARY
 +86 ms      CLEARABLE
```

Also show:

```text
Minimum advance knowledge required: 171 ms
```

if/when the lead-time probe generates `ℓ*`.

## Timeline behavior

At `ℓ = 0`:

```text
THREAT REVEALS
      ↓
      TURN ─────→ ACQUIRE → SERVICE
                              X deadline missed
```

At sufficient lead:

```text
TURN ─────────→
            THREAT REVEALS
                   ↓
                   ACQUIRE → SERVICE ✓
```

This should make the difference between **visibility** and **actionability** visually obvious.

## Three-class taxonomy panel

Below the slider, show three encounter classes:

### Blind-clearable

```text
M_reveal ≥ 0
No advance map knowledge required.
```

### Knowledge-rescuable

```text
M_reveal < 0
M_preaim ≥ 0
Familiarity can move the encounter across the boundary.
```

### Structurally overloaded

```text
M_preaim < 0
Even perfect pre-aim cannot rescue the encounter.
```

This taxonomy should become reusable in the manuscript and human-study materials if the lead-time probe is retained.

---

# 6. Optional Visual 4 — “The Crosshair Is a One-Lane Bridge”

## Purpose

Ultra-simple metaphor for talks, social posts, README, and nontechnical audiences.

Three threat-jobs are cars approaching a one-lane bridge.

- bridge = single reticle;
- car arrival = threat reveal;
- crossing time = turn + acquire + service;
- gate closing = deadline.

Panel A:

> Cars arrive one at a time → all cross.

Panel B:

> Cars arrive together with short deadlines → one cannot cross in time.

Punchline:

> **Your crosshair is the one-lane bridge. Geometry controls the traffic.**

This is not a paper figure. It is a communication asset.

---

# 7. Optional Visual 5 — Tactical Load Along a Route

## Purpose

Potential level-designer visualization.

Draw the authored route with a margin ribbon alongside it.

Example:

```text
ENTRY ───────── CORNER ───────── APERTURE ───── EXIT
 +420 ms          +90 ms        -65 ms          +180 ms
                                    ^
                              critical region
```

Clicking or hovering a route position should show:

- currently visible threats;
- newly revealed threats;
- reticle setup burden;
- current predicted margin.

This could evolve into a real design-tool overlay later, but is not required for v1.

---

# 8. Interactive Explainer Page — First Draft Storyboard

## Section 1 — Hero

Headline:

> **A map can be reachable and still be tactically impossible to read.**

Subhead:

> Geometry controls when threats become visible. One crosshair has to deal with them before their deadlines.

Visual: simplified animated player approaching a corner.

CTA/button:

> `See why counting sightlines fails →`

---

## Section 2 — Two Rooms

Use Visual 1.

Scroll behavior:

1. show room geometry only;
2. reveal threats;
3. animate reticle;
4. show outcome;
5. reveal static-count verdicts;
6. reveal Tactical Margin verdicts.

Do not show all labels at once.

---

## Section 3 — One Crosshair

Headline:

> **The problem is not how many threats exist. It is whether one reticle can service them in time.**

Use Visual 2 Panels B/C as a focused interactive.

Allow user to drag target bearings farther apart and see setup time grow.

Optional v1.1; not required for first prototype.

---

## Section 4 — Geometry Creates Work

Use full Visual 2 pipeline.

Narrative text:

> Walking through the room creates visibility events. Each event starts a deadline. The crosshair has to schedule the resulting work.

This is where mathematical labels can first appear.

---

## Section 5 — Knowing the Map Changes the Fight

Use Visual 3.

Headline:

> **What if you know where to aim before the enemy appears?**

This section should be highly interactive.

Slider changes:

- dashed pre-aim ray start time;
- reticle trajectory;
- completion time;
- tactical margin;
- survival outcome.

---

## Section 6 — Procedural Map Linter

Show several authored modules assembling like tiles.

Example:

```text
[A ✓] + [B ✓] + [C ✗] + [D ✓]
```

Then:

```text
TACTICAL LINTER
C rejected: creates an unserviceable crossfire at interface B→C.
```

Plain-language close:

> A generator can check this before a player ever sees the map.

---

## Section 7 — Evidence / Research Status

Compact evidence ladder:

```text
FORMAL MODEL        ✓
GEOMETRY COMPILER   ✓
PCG COMPOSITION     ✓
SIMULATION          ✓
VIZDOOM BRIDGE      ✓
HUMAN VALIDATION    NEXT
```

This prevents the explainer from implying completed human evidence.

---

# 9. Technical Implementation Recommendation

First version should be deliberately simple:

```text
research/tactical-clearability/explainer/
├── index.html
├── styles.css
├── app.js
├── data/
│   ├── two_rooms.json
│   └── knowledge_pivot.json
├── assets/
└── README.md
```

Recommended stack:

- semantic HTML;
- CSS custom properties;
- inline or DOM-generated SVG;
- vanilla JavaScript;
- no React/Vue/Svelte;
- no build step;
- GitHub Pages compatible;
- responsive down to tablet/mobile widths.

Use real frozen research values wherever practical. Do not fabricate “nice-looking” timings when a canonical fixture exists.

---

# 10. Data Contract for Visuals

The explainer should separate research data from rendering.

Suggested encounter JSON shape:

```json
{
  "id": "example_room",
  "label": "Low-count wide crossfire",
  "route": [[0,0],[1,0],[2,0]],
  "walls": [],
  "threats": [
    {
      "id": "T1",
      "position": [3,2],
      "reveal_ms": 500,
      "deadline_ms": 900,
      "bearing_deg": 70
    }
  ],
  "static_concurrency": 2,
  "tactical_margin_ms": -86,
  "outcome": "infeasible"
}
```

If actionability-lead results exist, add:

```json
{
  "knowledge_curve": [
    {"lead_ms": 0, "margin_ms": -114},
    {"lead_ms": 86, "margin_ms": -57},
    {"lead_ms": 171, "margin_ms": 0},
    {"lead_ms": 257, "margin_ms": 86}
  ],
  "critical_lead_ms": 171
}
```

---

# 11. First-Draft Deliverables

The v1 implementation should produce:

1. **One static Two-Rooms infographic** rendered as SVG.
2. **One animated Geometry → Schedule demonstration**.
3. **One interactive Map Knowledge slider**, using either existing endpoint values initially or the finite lead-time curve if those results are available.
4. **A single scrolling HTML explainer page** connecting those visuals.
5. Reusable SVG components so the same diagrams can later be exported for the manuscript.

Do not attempt polished publication graphics in the first draft.

---

# 12. Review Questions for v1

When reviewing the first draft, ignore visual polish initially and answer:

1. Can someone understand why two threats can be worse than three?
2. Is it visually obvious that the reticle is serial / stateful?
3. Is the difference between `visible` and `known/actionable` understandable?
4. Does the map-knowledge slider make the feasibility crossing intuitive?
5. Does the viewer understand that Tactical Margin is time reserve, not an arbitrary score?
6. Does the explainer avoid implying that human validation is already complete?
7. Can the core examples be exported cleanly as static paper figures?

If those seven questions are answered well, visual styling can be refined in v2.

---

# 13. Visual Tone

Aim for:

- technical but playful;
- closer to a high-quality game-design/debugging visualization than a generic academic infographic;
- strong geometric lines and motion;
- dark-field or neutral technical-panel aesthetic is acceptable, but information clarity comes first;
- avoid decorative military imagery;
- avoid mimicking a specific commercial game's HUD;
- the graphics should feel like a **tactical debugger for geometry**.

The central visual metaphor throughout should remain:

> **The map releases information. The reticle services it. Deadlines decide whether the encounter is clearable.**
