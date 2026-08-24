# Cut the Cake — Practical Application Guide

**Who this is for:** FPS players who want to understand *why* certain fights are unwinnable, and level designers / game developers who want to build fairer maps using math instead of guesswork.

---

## 🎮 For Players

### 1. Diagnose Why You Actually Died

Next time you die peeking a corner, the encounter falls into one of three categories:

| Category | What It Means | What You Should Do |
| :--- | :--- | :--- |
| **Blind-Clearable** | The room is fair even if you've never seen it before. | You got outplayed. Work on crosshair placement, clearing order, or reaction time. |
| **Knowledge-Rescuable** | The room is a death trap on first encounter, but completely survivable once you know the angles. | You need to learn the map. Pre-aim common positions *before* you peek. Study the angles. |
| **Structurally Overloaded** | The room is mathematically impossible to clear with gunplay alone, even with perfect map knowledge. | Don't take this fight dry. Smoke it, flash it, or take a different route. If the map is custom/PCG, it's a design bug. |

### 2. How Much Warning Do You Need Before Peeking?

The system calculates a **Critical Lead** ($\ell^*$) — the exact number of milliseconds of advance information you need before peeking a corner to survive.

**What this means in practice:**

- **$\ell^* = 0\,\text{ms}$** → You can swing this corner aggressively. Reaction speed alone is enough.
- **$\ell^* \approx 85\,\text{ms}$ (3 tics)** → You need a quick pre-aim. Jiggle-peek first, then commit.
- **$\ell^* \approx 115\,\text{ms}$ (4 tics)** → You need deliberate crosshair placement. Slow-peek or hold the angle.
- **$\ell^* \ge 170\,\text{ms}$ (6+ tics)** → Fast peeking *will* get you killed. You must pre-position your crosshair at the exact target bearing while still behind cover, then step out already aimed.

**Example from the research:** Two rooms (`STIM_07` and `STIM_11`) both give you +7 tics of advantage from knowing the map. But `STIM_07` only needs 114ms of pre-aim to survive, while `STIM_11` needs 171ms — 50% more time. Same knowledge benefit, very different peek speed requirements.

### 3. Stand Far From Corners

This is the mathematical proof of "slicing the pie":

- **Close to the corner:** Your angular spread is wide. You need to rotate your crosshair across a huge arc to sweep the room. More rotation = more time = tighter deadlines.
- **Far from the corner:** Your angular spread is narrow. The threats cluster into a smaller arc. Less rotation = more time = higher tactical margin.

> **Rule of thumb:** If you can give yourself 2–3 extra meters of distance from a doorway before peeking, do it. The math shows this can turn a lethal encounter into a clearable one.

### 4. Don't Always Clear the Closest Enemy First

Your instinct says: shoot the nearest target. The math says: **shoot the target with the tightest deadline first.**

Why? An enemy who appeared 200ms ago with a 350ms reaction window is about to shoot you — even if a closer enemy appeared just 50ms ago with a generous 500ms window. Clear the urgent threat, then swing to the close one.

This is the concept of **optimal clearing permutation** ($\pi^*$). The system computes the best order. In your gameplay, practice reading which angle is most urgent, not just which is closest.

### 5. Map Knowledge Is a Measurable Tactical Resource

The paper quantifies exactly how much value map familiarity gives you on every single room:

- A room with $\Delta\mathcal{M}_{\text{knowledge}} = 0$ plays the same whether you've seen it or not. Pure reaction.
- A room with $\Delta\mathcal{M}_{\text{knowledge}} = +7\,\text{tics}$ ($+200\,\text{ms}$) is **dramatically** easier once you've learned the angles.

**Practical takeaway:** On new maps, play slow and gather information. On maps you know, be aggressive — the math is on your side.

---

## 🛠️ For Level Designers & Game Developers

### 1. Lint Your Levels at Compile Time

**The core workflow:**
```
Your 2D gray-box floorplan
         │
         ▼
  Geometry-to-Contract Compiler  (< 0.1ms per room)
         │
         ▼
  Every room transition gets labeled:
    ✅ Blind-Clearable     → Ship it
    ⚠️ Knowledge-Rescuable → Intentional? Add visual cues for new players
    🚫 Structurally Overloaded → Fix it before playtesting
```

This replaces weeks of blind playtesting with **instant, deterministic feedback** on every sightline transition in your map. Run it in your CI pipeline. Run it in your editor. Run it every time geometry changes.

### 2. Automated Level Repair

When the linter flags a room as structurally overloaded:

1. **Diagnosis:** The system identifies the **controlling occluder** — the exact wall, crate, or pillar whose position creates the unsolvable crossfire.
2. **Search:** It explores small translations of that obstacle (grid steps of 0.05m, up to 1.8m).
3. **Fix:** It finds the smallest possible nudge that brings $\mathcal{M}$ above a safety threshold (+2 tics / +57ms).
4. **Review:** You see the proposed edit, accept or modify it.

**Key stats from the benchmark:**
- 80% of broken rooms were fixed by moving a single wall
- Median fix was just 0.85m (less than a meter)
- 75% of fixes transferred successfully to a real game engine (ViZDoom)

This is not AI redesigning your level. It's a minimal, targeted suggestion — like a spell-checker for sightlines.

### 3. Procedural Level Assembly (PCG)

If you're building levels from modular room prefabs:

**The problem:** Two individually fair rooms can create an unfair encounter when connected, because sightlines spill across the boundary.

**The solution:** Each room module compiles into a **transfer matrix** that captures how the player's crosshair state evolves from entry to exit. When rooms connect:

- Matrices compose via min-plus multiplication (exact, associative, no approximation errors)
- If the connecting doorway has a **quiescent reset zone** (a brief stretch of corridor shielded from all threats), then: **global level fairness = local room fairness** (the $C \equiv D$ theorem)
- This means you can check each room independently and guarantee the whole dungeon is fair — with zero runtime simulation cost

**Validated on:** 25,000 procedurally assembled candidates with 0 false certifications.

### 4. Difficulty Tuning via Capability Envelopes

Instead of binary "fair/unfair," the system computes the **minimum player skill requirements** for each room:

> *"This room requires aim speed ≥ 280°/s and reaction time ≤ 140ms to be blind-clearable."*

Use this to:

| Use Case | How |
| :--- | :--- |
| **Difficulty tiers** | Tag rooms by required skill floor. Casual lobbies get wide-margin rooms; ranked gets tight ones. |
| **Adaptive PCG** | Generate geometry tuned to the player's MMR. Lower-ranked players get rooms with higher $\mathcal{M}$. |
| **Accessibility** | Identify which rooms become clearable if you slow down enemy reaction times by 50ms (one slider change). |
| **Competitive integrity** | Prove to players that every ranked map has $\mathcal{M}_{\text{reveal}} \ge 0$ at the declared skill model. |

### 5. The Tactical CAD Workbench (Prototype)

A web-based interactive tool is included in the repo:

```bash
python -m cut_the_cake.cad_server --port 5000
# Open http://127.0.0.1:5000
```

What you can do:
- **Load** an arena layout
- **Drag** obstacles in real time
- **Watch** Tactical Margin update live as walls move
- **See** which specific threat becomes the scheduling bottleneck
- **Inspect** the optimal clearing sequence and deadline timeline

This is the prototype of the full Tactical CAD vision — where you author geometry, analyze sightlines, diagnose fairness issues, and apply repairs, all before a single playtest.

### 6. Using the Interactive Explainer for Team Onboarding

The repo includes an [8-module visual explainer](explainer/index.html) that teaches every concept interactively:

| Module | Concept | Who Benefits |
| :--- | :--- | :--- |
| 01 — Corner Distance | Why standing far from walls helps | Players & designers |
| 02 — Crosshair Placement | Reticle setup cost visualization | Players |
| 03 — Stagger vs. Crossfire | Why timing matters more than count | Designers |
| 04 — Clear Order | Permutation sequencing | Players & designers |
| 05 — Tactical Margin | The stopwatch duel | Everyone |
| 06 — Map Knowledge Lab | Interactive lead-time slider | Players & researchers |
| 07 — Route Choice | Why the shortest path isn't safest | Players & designers |
| 08 — Composition | From single corners to procedural dungeons | Developers |

Use it to onboard new level designers, train QA to identify scheduling bottlenecks, or teach competitive players the underlying tactical math.
