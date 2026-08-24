# Cut the Cake — Tactical CAD Product Roadmap

This roadmap defines the transition of **Cut the Cake** from its peer-reviewed scientific core (Rounds 1–11.4A) into a full-scale **Tactical CAD System for Competitive First-Person Shooters**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          TACTICAL CAD PLATFORM                          │
│                                                                         │
│   ┌────────────────────────┐              ┌─────────────────────────┐   │
│   │   Web / Phaser Canvas  │ ◄──────────► │  Interactive Diagnostic │   │
│   │   (2D/3D Map Viewport) │              │  Inspector & Scrub Bar  │   │
│   └───────────▲────────────┘              └────────────▲────────────┘   │
│               │                                        │                │
│               └───────────────────┬────────────────────┘                │
│                                   │                                     │
│                     ┌─────────────▼─────────────┐                       │
│                     │   Scene Manifest Schema   │                       │
│                     │   (scene_manifest_v1.json)│                       │
│                     └─────────────▲─────────────┘                       │
│                                   │                                     │
│ ══════════════════════════════════╪════════════════════════════════════ │
│                     SCIENTIFIC CORE BOUNDARY (FROZEN)                   │
│                                   │                                     │
│                     ┌─────────────▼─────────────┐                       │
│                     │  Cut the Cake Python Core │                       │
│                     │  - Polygon LOS Compiler   │                       │
│                     │  - Discrete Tic Scheduler │                       │
│                     │  - MinimalRepairOptimizer │                       │
│                     │  - ViZDoom Engine Bridge  │                       │
│                     └───────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Horizons & Development Phases

### Horizon 0: Scientific Core Freeze (Rounds 1–11.4A) — ✅ COMPLETED
* **Goal:** Formalize, prove, and empirically validate tactical clearability scheduling.
* **Artifacts:**
  * Strict polynomial compiler converting 2D floorplans into $(\min, +)$ dioid transfer matrices.
  * Discrete 35 Hz scheduler with exact single-machine maximum lateness minimization ($1 \mid r_j, s_{ij} \mid L_{\max}$).
  * Population validation across $9,000$ discrete simulation episodes ($\text{LOGFO-AUC} = 1.0000$).
  * Audited 50-arena benchmark with $80\%$ source-model repair, $60\%$ native ViZDoom rescue, and $75\%$ engine transfer efficiency with full three-layer residual decomposition.
  * Tagged release: `round11.4a-freeze`.

---

### Horizon 1: Tactical CAD Milestone 1 (M1) — Single-Arena Tactical Debugger — 🚀 NEXT
* **Goal:** Deliver an end-to-end visual diagnostic and playback instrument for a single arena.
* **Scope & Boundary:**
  * **First Fixture:** Family 1 (Stagger Deficit) — 100% source repair, 100% engine rescue.
  * **Strict Data Flow:** `Python Core -> scene_manifest_v1.json -> Phaser Web Canvas`.
  * **Features:**
    * Top-down 2D map viewport with player path, obstacles, and threat anchors.
    * Real-time raycasting and line-of-sight cone visualization.
    * Interactive time-scrubbing bar with play/pause/step controls.
    * Discrete release ($r_j$) and deadline ($d_j$) event markers on the timeline.
    * "Why?" bottleneck explanation card highlighting critical occluder edges.
    * **Broken vs. Repaired Toggle:** Instant visual comparison showing the geometric shift ($d^*$) and resulting margin flip ($\mathcal{M} < 0 \to \mathcal{M} \ge +2$).
  * *No multi-arena suites, map editing, or 3D viewports in M1.*

---

### Horizon 2: Tactical CAD Milestone 2 (M2) — Interactive Map Editor & Constraint Linter
* **Goal:** Allow level designers to author, edit, and lint competitive map geometry in real time.
* **Features:**
  * Drag-and-drop wall/obstacle translation and rotation in browser.
  * Sub-10ms background clearability compilation on geometry modification.
  * Live heatmaps of tactical margin deficits along authored patrol paths.
  * "Auto-Fix" button invoking `MinimalRepairOptimizer` to suggest compliant obstacle placements.
  * Multi-family support (Apertures, Blind Spots, Triad Congestion, Flanks).

---

### Horizon 3: Tactical CAD Milestone 3 (M3) — Multiplayer 6v6 Schedulability & Global Routing
* **Goal:** Extend single-path clearability contracts to multi-agent team play and branched path graphs.
* **Features:**
  * Coordinated crossfire resolution and cross-lane peel timing.
  * Competitive defusal map analysis (A-site, B-site, Mid rotation timings).
  * Export bridges to standard game engine formats (Unreal Engine, Unity, Source 2, Doom WAD).
