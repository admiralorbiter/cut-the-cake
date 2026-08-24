# Cut the Cake — Tactical CAD Product Roadmap

**Document type:** Living strategic roadmap  
**North star:** A Tactical CAD platform for competitive first-person shooters  
**Current research checkpoint:** Round 11.4A — Inverse Tactical Repair Audit & External-Transfer Hardening (Frozen)  
**Last strategic review:** August 2026  

---

# 1. North Star & Vision

Cut the Cake is evolving from a tactical clearability research project into a **Tactical CAD Platform for competitive games**.

The core workflow:
> Import or gray-box a competitive FPS map, declare routes, tactical scenarios, and player capability assumptions, compile geometry into information and deadline schedules, inspect where tactical overload occurs, simulate transparent team policies through the map, ask **Why?** a transition fails, synthesize a minimal repair, and replay the same scenario before and after the change.

The defining 60-second workflow:
1. Load a competitive gray-box map.
2. Click **Analyze**.
3. Inspect serviceable, boundary-sensitive, knowledge-sensitive, and overloaded transitions.
4. Click **Play** and watch agents traverse the map while LOS, reticle state, deadlines, and Tactical Margin animate.
5. Pause at a red transition and click **Why?**
6. Inspect the exact reveal / angle / deadline bottleneck.
7. Click **Repair**.
8. Watch the geometry shift.
9. Replay the identical scenario before / after.
10. Export a technical report showing what changed, why it changed, and the confidence tier of the result.

A major future case-study target is a **manually reconstructed or legally sourced gray-box of a contemporary competitive FPS map** (e.g. Modern Warfare beta maps, Dust II, Ascent) without redistributing proprietary art or game assets.

---

# 2. Product Thesis

```text
GEOMETRY
   ↓
INFORMATION RELEASE (r_j)
   ↓
ATTENTION / RETICLE WORKLOAD (s_ij, p_j)
   ↓
DEADLINE FEASIBILITY (D_j, L*, M)
   ↓
DIAGNOSIS (T_crit, Controlling Occluder)
   ↓
REPAIR (d* in T_obs)
   ↓
REPLAY / VERIFY (Source + Engine Bridge)
```

The core product thesis:
> **A level is not only geometrically valid. It has tactical contracts that can be compiled, inspected, tested, and repaired before expensive human playtesting.**

Cut the Cake combines:
- Tactical static analyzer;
- Map debugger;
- Tactical simulator;
- Inverse-design assistant;
- PCG constraint engine;
- External-engine verification system;
- Mixed-initiative competitive level-design workbench.

---

# 3. System Scope & Architecture Rules

## What It Is:
- A geometry-to-tactical-workload compiler;
- A single-machine real-time scheduling and information-availability model;
- A Tactical Margin evaluator ($\mathcal{M} = -L^*$);
- A compositional PCG contract system;
- A diagnostic engine attributing scheduling bottlenecks to specific occluders;
- An inverse tactical repair engine over declared operator sets;
- An external-engine validation framework;
- A tactical map editor and execution simulator.

## What It Is Not:
- Not a claim that the current model fully predicts human psychology;
- Not a commercial FPS bot AI;
- Not a replacement commercial game engine;
- Not a reason to rewrite the validated Python scientific core in JavaScript;
- Not a full arbitrary-3D simulator today.

**Architecture Rule:** Python owns scientific truth. Visualization clients (Phaser / Web Canvas) render telemetry, animate, scrub, compare, and request analysis, but never independently compute LOS, scheduling, Tactical Margin, or repair semantics.

---

# 4. Capability Matrix & Frozen Evidence Checkpoint

## 4.1 Capability Status

| Capability | Readiness | Current State |
| --- | --- | --- |
| Geometry → reveal/deadline compilation | **Strong** | 2D polygonal geometry + authored traversal |
| Single-reticle scheduling model | **Strong** | Exact model-scoped scheduling abstraction |
| Tactical Margin ($\mathcal{M} = -L^*$) | **Strong** | Core serviceability metric |
| Static-metric counterexamples | **Strong** | $K_{\text{static}}$ / threat count shown insufficient |
| Transfer contracts / composition | **Strong** | Finite angular-state compositional abstraction |
| PCG certification (Condition E) | **Strong** | Large automated candidate / generation work |
| Population simulation (Round 11S) | **Strong** | 9,000 episodes, LOGFO-AUC = 1.0000 |
| Actionability / map knowledge ($\ell^*$) | **Strong** | Model-level information threshold |
| Inverse tactical repair | **Strong** | Grid-minimal over declared operator set $\mathcal{T}_{\text{obs}}$ |
| External engine transfer | **Validated** | 75% transfer efficiency among source repairs |
| Visual explanation | **Active** | Interactive concept pages |
| Top-down tactical playback | **Completed (H1)** | Authoritative 35 Hz telemetry player |
| Tactical CAD editor (M2A) | **Active (H2/M2A)** | Drag One Wall interactive source re-analysis |
| Multi-agent team execution | **Horizon 4** | Existing controller concepts, team simulator |
| Real commercial-map import | **Horizon 5** | Gray-box ingestion workflow |
| 2.5D / multi-level tactical geometry | **Horizon 6** | Planar/extruded now; layered next |
| Human population calibration | **Prospective** | Pre-registered protocol (H1–H4) |

## 4.2 Frozen Scientific Core Checkpoint (Round 11.4A)

Audited benchmark evidence (`round11.4a-freeze`):
- **50/50** layouts genuinely unserviceable at baseline ($\mathcal{M} < 0$) and fatal in native ViZDoom;
- **40/50 (80.0%)** source-model grid-minimal repair success within declared operator set $\mathcal{T}_{\text{obs}}$;
- **30/50 (60.0%)** native ViZDoom death → survival engine rescue;
- **30/40 (75.0%)** engine transfer efficiency among source-successful repairs;
- Median edit distance **0.85 m** (Mean: 0.89 m);
- Mean export residual $\Delta_{\text{export}} L = \mathbf{+1.64\,\text{tics}}$;
- Mean execution residual $\Delta_{\text{execution}} L = \mathbf{-0.08\,\text{tics}}$;
- Large family dependence (Family 4 dense triad congestion dominated by export residuals).

---

# 5. Core Platform Architecture

```text
                           CUT THE CAKE
                  ┌─────────────────────────────┐
                  │  Python Scientific Core     │
                  │  (FROZEN @ round11.4a)      │
                  │                             │
                  │ - Geometry / LOS Compiler   │
                  │ - Discrete Tic Scheduler    │
                  │ - Tactical Margin / DiDioid │
                  │ - Diagnostics & Bottlenecks │
                  │ - MinimalRepairOptimizer    │
                  │ - ViZDoom Engine Bridge     │
                  └──────────────┬──────────────┘
                                 │
                  versioned scene manifest & REST API
                  (scene_manifest_v1.json / POST /api/analyze)
                                 │
             ┌───────────────────┴───────────────────┐
             │                                       │
   ┌─────────▼──────────────┐             ┌──────────▼─────────┐
   │ Tactical CAD Client    │             │ Engine Validation  │
   │ (cad/web/)             │             │                    │
   │ - Canvas 2D telemetry  │             │ - ViZDoom (now)    │
   │ - Top-down map view    │             │ - Unreal adapter   │
   │ - Interactive timeline │             │   (future)         │
   │ - Drag One Wall (M2A)  │             └────────────────────┘
   │ - Diagnostic inspector │
   │ - Broken/Repaired diff │
   └────────────────────────┘
```

---

# 6. Strategic Product Horizons

## Horizon 0: Scientific Core Freeze (Rounds 1–11.4A) — ✅ COMPLETED
- Formalized single-reticle scheduling ($1 \mid r_j, s_{ij} \mid L_{\max}$).
- Verified on 9,000 discrete simulation episodes and audited 50-arena ViZDoom benchmark.
- Certified under annotated tag `round11.4a-freeze`.

---

## Horizon 1: Tactical Debugger Vertical Slice (M1) — ✅ COMPLETED
- **Milestone 1A (M1A):** Frozen Scene Contract + Single-Arena Playback (`cad_export.py` → `scene_manifest_v1.json` → `cad/web/`).
- **Milestone 1B (M1B / M1B.1):** Hardened provenance boundaries, fail-closed external evidence, What Changed causal card, exact timing audit parity, and 88 passing verification tests.
- **Fixture:** Canonical Family 1 Stagger Deficit (`RepairPop_F1_StaggerDeficit_00`).
- **Features:** 2D top-down canvas, play/pause/step/scrub timeline, authoritative LOS rays, Tactical Margin badge, What Changed causal table, Frozen Broken / Frozen Repair toggles.

---

## Horizon 2: Tactical CAD Editor Foundation (M2) — 🚀 ACTIVE
- **Milestone 2A (M2A — Completed):** Drag One Wall / Interactive Source Re-analysis:
  - Constrained X-axis horizontal dragging of Obstacle #0 with $0.05\,\text{m}$ grid snapping.
  - Real-time local Python Flask service (`POST /api/analyze`) serving authoritative geometry validation, raycasts, discrete scheduling, and Tactical Margin calculations.
  - Fail-closed external engine evidence (`transfer_status: "not_run"`).
  - 3 status bands (`UNSERVICEABLE`, `FEASIBLE — BELOW TARGET RESERVE`, `TARGET RESERVE MET`).
- **Milestone 2B (M2B — Completed):** Multi-obstacle translation, rotation, and custom corridor clearance validation.
- **Milestone 2C (M2C / M2C.1 — Completed & Accepted):** Transform Hardening & Monotonic Session History:
  - Local-basis oriented rectangle resize (preserving authored orientation).
  - Monotonic document/session wall sequence ID allocation (non-reusing deleted IDs across undo/redo).
  - Absolute target-angle vs relative delta rotation composition.
  - State-preserving undo/redo history stack across multi-element mutations.
- **Milestone 2D (M2D — Active / Verification Conditional):** Scenario Authoring, Interactive Playback & Automated Verification Harness:
  - Interactive scenario authoring: route creation, waypoint editing, route speed tuning ($v_{\text{move}}$), combat parameters ($\omega_{\text{slew}}, T_{\text{acq}}, T_{\text{serv}}$), and initial reticle azimuth.
  - Interactive time-indexed playback scrubbing with synchronized player cone and authoritative LOS visibility rays.
  - Fast path vs full simulation dual-mode analysis dispatch.
  - 4-Tier verification system: Tiered state-machine fuzzer, metamorphic property suite, Playwright browser E2E, and scaling benchmark matrix.
- **Milestone 2E (M2E — Planned):** "Auto-Fix" integration invoking `MinimalRepairOptimizer` to suggest compliant obstacle placements in authored layouts.
- **Milestone 2F (M2F — Planned):** Live spatial heatmaps of tactical margin deficits along authored patrol routes.

---

## Horizon 3: Multi-Operator Repair Workbench (M3)
- Expand repair operators with explicit invariant checking:
  1. Obstacle translation (current $\mathcal{T}_{\text{obs}}$);
  2. Obstacle extension / contraction;
  3. Aperture width adjustment;
  4. Baffle insertion / split;
  5. Route-entry / port adjustment;
  6. Threat anchor adjustment (authored gameplay operator).
- Robust deployment reserve objectives ($\mathcal{M}_{\text{source}} \ge \epsilon + \text{reserve}(\text{family})$).

---

## Horizon 4: Transparent Team Simulation (M4)
- **1vN Scheduling Animator:** Single player moving against multiple dynamic threats.
- **3v3 Lane Skirmish:** Coordinated crossfire resolution and cross-lane peel timing on fixed routes.
- **6v6 Whole-Map Playback:** Multi-lane team schedules across objective contest points.
- Explicit, transparent agent policies (FIFO, nearest-angle, earliest-deadline, optimal bound).

---

## Horizon 5: Real-Map Case Study Pipeline (M5)
- Ingest and analyze recognizable competitive FPS geometry:
  - Modern Warfare beta gray-box reconstructions;
  - Tactical defusal maps (Dust II, Ascent, Haven A/B/C rotations).
- Ingestion pipeline: image reference underlay, scale calibration, polygon tracing, route hypotheses, uncertainty tagging.

---

## Horizon 6: 2.5D Elevation & Layered Geometry (M6)
- Layered tactical geometry: stairs, ramps, elevation steps, balconies, vertical sightlines.
- Vertical aim cone slew and 3D pitch constraints ($s_{ij}$ with elevation $\Delta \theta$).
- Height-conditioned threat anchors and multi-tier room transitions.

---

## Horizon 7: Studio & Game Engine Workflow Integration (M7)
- Unreal Engine / Unity / Source 2 editor plugins.
- CI/CD automated tactical linting for nightly gray-box level commits.
- Before/after tactical diff reports on level geometry pull requests.
- Studio web dashboard for level designers and combat balance teams.

---

## Horizon 8: Inverse Tactical Synthesis (M8 — Moonshot)
- Mixed-initiative Tactical CAD: synthesize level geometry directly from high-level tactical specifications:
  - Declared primary lanes, flank timings, first-contact margin targets, reset pockets.
  - Generative co-design: designer specifies tactical intent, system generates compliant geometric options.

---

# 7. Parallel Research Threads

- **A. Capability Envelopes ($\mathcal{C}(G)$):** Characterizing required sensorimotor thresholds ($\omega^*, A^*, v^*$) for arbitrary geometry.
- **B. Robust Engine Transfer:** Dynamic, geometry-conditioned deployment guard bands ($\epsilon_{\text{deploy}}(G)$) and WAD quantization sensitivity.
- **C. Tactical Motif Discovery:** Formal catalog of recurring level design motifs (sequential slices, crossfires, deep baffles, reset pockets).
- **D. Prospective Human Validation:** Pre-registered empirical pilot protocol ([`human/PILOT_PROTOCOL.md`](human/PILOT_PROTOCOL.md)) for future human cognition calibration.
