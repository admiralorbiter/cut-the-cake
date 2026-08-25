# Cut the Cake — Tactical CAD Product Roadmap

**Document type:** Living strategic roadmap  
**North star:** A Tactical CAD platform for competitive first-person shooters  
**Current scientific checkpoint:** Horizon 6 Frozen (2.5D Elevation, Spherical Slew, Closed Prism Raycasting, 3D Controller Parity — 138 Acceptance Tests)  
**Last strategic review:** August 2026  

---

> [!NOTE]
> ### 📌 Current Project State (Horizon 6 Complete)
> The repository has successfully completed and scientifically frozen **Horizon 0 through Horizon 6**:
> - **Horizon 0:** Verified mathematical scheduling core ($1 \mid r_j, s_{ij} \mid L_{\max}$), 9,000 simulation episodes, 50-arena ViZDoom engine transfer (`round11.4a-freeze`).
> - **Horizon 1:** Tactical debugger vertical slice and 35-Hz authoritative playback (`cad_export.py` / `cad/web/`).
> - **Horizon 2:** Tactical CAD editor foundation (M2A–M2F.2): live wall transforms, scenario authoring, closed-loop Auto-Fix optimizer, and Suffix Tactical Margin ribbons ($\mathcal{M}_{\text{suffix}}(s)$).
> - **Horizon 5:** Pre-registered real-map graybox case studies (*Dust II* A-Long/B-Tunnels, *Valorant* Ascent Wine, *MW4* Transit 213).
> - **Horizon 6:** 2.5D elevation, vertical prism footprints, spherical great-circle geodesic aiming on the unit sphere ($S^2$), dynamic pitch derivation, and deterministic 3D Slerp controller execution ($t_j^{\text{event}} \equiv C_j - 1$).
>
> All 138 CAD acceptance tests (and 207 tests in the full suite) are passing with 100% determinism.

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
7. Click **Repair** (or press `[A]` for Auto-Fix).
8. Watch the geometry shift.
9. Replay the identical scenario before / after.
10. Export a technical report showing what changed, why it changed, and the confidence tier of the result.

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
REPLAY / VERIFY (Source + Engine Bridge + 3D Execution)
```

The core product thesis:
> **A level is not only geometrically valid. It has tactical contracts that can be compiled, inspected, tested, and repaired before expensive human playtesting.**

---

# 3. System Scope & Architecture Rules

## What It Is:
- A geometry-to-tactical-workload compiler;
- A single-machine real-time scheduling and information-availability model;
- A Tactical Margin evaluator ($\mathcal{M} = -L^*$ and $\mathcal{M}_{\text{suffix}}$);
- A compositional PCG contract system;
- A diagnostic engine attributing scheduling bottlenecks to specific occluders;
- An inverse tactical repair engine over declared operator sets;
- An external-engine validation framework;
- A tactical map editor and 3D execution simulator.

## What It Is Not:
- Not a claim that the current model fully predicts human psychology;
- Not a commercial FPS bot AI;
- Not a replacement commercial game engine;
- Not a reason to rewrite the validated Python scientific core in JavaScript;
- Not an arbitrary full 6-DOF game simulator.

**Architecture Rule:** Python owns scientific truth. Visualization clients (Web Canvas / Three.js) render telemetry, animate, scrub, compare, and request analysis, but never independently compute LOS, scheduling, Tactical Margin, or repair semantics.

---

# 4. Capability Matrix & Frozen Evidence Checkpoint

## 4.1 Capability Status

| Capability | Readiness | Current State |
| :--- | :--- | :--- |
| Geometry → reveal/deadline compilation | **Completed & Frozen** | 2D/2.5D polygonal & extruded prism geometry |
| Single-reticle scheduling model | **Completed & Frozen** | Exact $1 \mid r_j, s_{ij} \mid L_{\max}$ scheduling |
| Tactical Margin ($\mathcal{M} = -L^*, \mathcal{M}_{\text{suffix}}$) | **Completed & Frozen** | Point-wise and counterfactual suffix margin |
| Static-metric counterexamples | **Completed & Frozen** | $K_{\text{static}}$ shown insufficient; proven in PCG & sim |
| Transfer contracts / composition | **Completed & Frozen** | $(\min, +)$ dioid algebra ($C \equiv D$ theorem) |
| PCG certification (Condition E) | **Completed & Frozen** | 25,000 dungeon module candidate sweeps |
| Population simulation (Round 11S) | **Completed & Frozen** | 9,000 episodes, LOGFO-AUC = 1.0000 |
| Actionability / map knowledge ($\ell^*$) | **Completed & Frozen** | Pre-aim vs blind un-occlusion model |
| Inverse tactical repair | **Completed & Frozen** | Grid-minimal over declared operator set $\mathcal{T}_{\text{obs}}$ |
| External engine transfer | **Validated** | 75.0% transfer efficiency in native ViZDoom |
| Top-down tactical playback (H1) | **Completed & Frozen** | Authoritative 35 Hz telemetry player |
| Tactical CAD editor (H2/M2A–M2F) | **Completed & Frozen** | Real-time transforms, Auto-Fix, Suffix heatmaps |
| Real commercial-map grayboxes (H5) | **Completed & Frozen** | Dust II, Ascent, Transit 213 pre-registered case studies |
| 2.5D / 3D Controller Execution (H6) | **Completed & Frozen** | Spherical Slerp execution, $t_j^{\text{event}} \equiv C_j - 1$ |
| Multi-agent team execution (H4) | **Future (H4)** | Multi-lane team schedules across objectives |
| Studio & engine workflow (H7) | **Future (H7)** | Unreal / Unity / Source 2 editor plugins |
| Human population calibration | **Prospective** | Pre-registered protocol (`human/PILOT_PROTOCOL.md`) |

---

# 5. Core Platform Architecture

```text
                           CUT THE CAKE
                  ┌─────────────────────────────┐
                  │  Python Scientific Core     │
                  │  (FROZEN @ Horizon 6)       │
                  │                             │
                  │ - 2.5D Geometry & Compiler  │
                  │ - Spherical Geodesic Slew   │
                  │ - Discrete Tic Scheduler    │
                  │ - Suffix Tactical Margin    │
                  │ - MinimalRepairOptimizer    │
                  │ - 3D Simulation Controller  │
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
   │ - Canvas 2D telemetry  │             │ - ViZDoom (Doom)   │
   │ - Top-down map view    │             │ - Unreal adapter   │
   │ - Suffix heatmap ribbon│             │   (future)         │
   │ - Auto-Fix workbench   │             └────────────────────┘
   │ - Broken/Repaired diff │
   └────────────────────────┘
```

---

# 6. Strategic Product Horizons

## 6.1 Completed & Frozen Horizons

### Horizon 0: Scientific Core Freeze (Rounds 1–11.4A) — ✅ COMPLETED
- Formalized single-reticle scheduling ($1 \mid r_j, s_{ij} \mid L_{\max}$).
- Verified on 9,000 discrete simulation episodes and audited 50-arena ViZDoom benchmark.
- Certified under annotated tag `round11.4a-freeze`.

### Horizon 1: Tactical Debugger Vertical Slice (M1) — ✅ COMPLETED
- **Milestone 1A (M1A):** Frozen Scene Contract + Single-Arena Playback (`cad_export.py` → `scene_manifest_v1.json` → `cad/web/`).
- **Milestone 1B (M1B / M1B.1):** Hardened provenance boundaries, fail-closed external evidence, What Changed causal card, exact timing audit parity, and 88 passing verification tests.
- **Fixture:** Canonical Family 1 Stagger Deficit (`RepairPop_F1_StaggerDeficit_00`).

### Horizon 2: Tactical CAD Editor Foundation (M2) — ✅ COMPLETED & FROZEN
- **Milestone 2A (M2A):** Drag One Wall / Interactive Source Re-analysis with $0.05\,\text{m}$ grid snapping.
- **Milestone 2B (M2B):** Multi-obstacle translation, rotation, and corridor clearance validation.
- **Milestone 2C (M2C / M2C.1):** Transform hardening, monotonic session IDs, and undo/redo stack.
- **Milestone 2D / 2D.1 (M2D):** Scenario authoring, dynamic speed ($v_{\text{move}}$), combat parameters, and Safe Exact-Solver Envelope ($J \le 6$).
- **Milestone 2E (M2E):** Mixed-initiative closed-loop "Auto-Fix" repair integration (`POST /api/document/auto_fix`).
- **Milestone 2F / 2F.2 (M2F):** Live spatial heatmaps and Suffix Tactical Margin ribbons ($\mathcal{M}_{\text{suffix}}(s)$).

### Horizon 5: Real-Map Case Study Pipeline (M5) — ✅ COMPLETED & CERTIFIED
- **Milestone 5-A & 5-A.1:** Calibrated Real-Map Transfer Case Study (*Counter-Strike Dust II* A-Long to Pit).
  - Metric gray-box reconstruction ($\mathrm{RMSE} = 0.0064\,\text{m}$).
  - Multi-route differentiation (`route_pieing` vs `route_wide_swing`).
  - Discovery of Suffix Margin superiority over global whole-route averaging.
  - 81-run joint parameter uncertainty sweep.
- **Milestone 5-B:** Pre-Registered Multi-Engagement Falsification Cross-Section.
  - Pre-registered hypotheses sealed in `preregistration/m5b_preregistration.json`.
  - Evaluated *Valorant* Ascent (Wine off-angle), *Dust II* (B-Tunnels expected negative choke), and *MW4* Transit 213 (bus lattice).

### Horizon 6: 2.5D Elevation & Layered Geometry (M6) — ✅ COMPLETED & FROZEN
- **Milestone 6-A / 6-A.1:** 2.5D Elevation & Spherical Aim State Preflight (unit-sphere $S^2$ geodesic metric with planar fallback, verified under $\mathrm{SO}(3)$ rigid-body rotation invariance).
- **Milestone 6-B / 6-B.2:** Height-Aware Geometric Compilation (extruded prism footprints $P_i \times [z_{\min}, z_{\max}]$, closed volumetric raycasting, dynamic pitch derivation).
- **Milestone 6-C / 6-C.1:** 3D Unit-Sphere Controller Execution & Parity (spherical Slerp controller, realized service completion parity $t_j^{\text{event}} \equiv C_j - 1$, 138 CAD acceptance tests passed).

---

## 6.2 Future Strategic Horizons

### Horizon 3: Multi-Operator Repair Workbench (M3) — 🔮 FUTURE
- Expand repair operators with explicit invariant checking:
  1. Obstacle translation (current $\mathcal{T}_{\text{obs}}$);
  2. Obstacle extension / contraction;
  3. Aperture width adjustment;
  4. Baffle insertion / split;
  5. Route-entry / port adjustment;
  6. Threat anchor adjustment (authored gameplay operator).
- Heterogeneous cost model: $\mathcal{C}(\mathcal{G}, \mathcal{G}') = w_{\text{move}} d_{\text{wall}} + w_{\text{resize}} \Delta A + w_{\text{insert}} N_{\text{new}} + w_{\text{route}} \Delta L$.
- Robust deployment reserve objectives ($\mathcal{M}_{\text{source}} \ge \epsilon + \text{reserve}(\text{family})$).

### Horizon 4: Multi-Agent & Team-Resource Schedulers (M4) — 🔮 FUTURE
- **Team Resource Scheduling:** Multi-processor scheduling ($m \mid r_j, s_{ij} \mid L_{\max}$) where $m$ aiming reticles coordinate crossfires.
- **Cross-Lane Peeling & Trading:** Formal modeling of buddy trades, split-second cross-cover, and lane support.
- **3v3 & 5v5 Whole-Site Contests:** Multi-lane team schedules across bomb-site contest points.
- **Explicit Team Policies:** Coordinated angle assignment, cross-fire isolation, and designated primary peeker.

### Horizon 7: Studio & Game Engine Workflow Integration (M7) — 🔮 FUTURE
- Unreal Engine / Unity / Source 2 editor plugins.
- CI/CD automated tactical linting for nightly gray-box level commits.
- Before/after tactical diff reports on level geometry pull requests.
- Studio web dashboard for level designers and combat balance teams.

### Horizon 8: Inverse Tactical Synthesis (M8 — Moonshot) — 🔮 FUTURE
- Mixed-initiative Tactical CAD: synthesize level geometry directly from high-level tactical specifications:
  - Declared primary lanes, flank timings, first-contact margin targets, reset pockets.
  - Generative co-design: designer specifies tactical intent, system generates compliant geometric options.

---

# 7. Parallel Research Threads

- **A. Capability Envelopes ($\mathcal{C}(G)$):** Characterizing required sensorimotor thresholds ($\omega^*, A^*, v^*$) for arbitrary geometry.
- **B. Robust Engine Transfer:** Dynamic, geometry-conditioned deployment guard bands ($\epsilon_{\text{deploy}}(G)$) and WAD quantization sensitivity.
- **C. Tactical Motif Discovery:** Formal catalog of recurring level design motifs (sequential slices, crossfires, deep baffles, reset pockets).
- **D. Prospective Human Validation:** Pre-registered empirical pilot protocol ([`human/PILOT_PROTOCOL.md`](human/PILOT_PROTOCOL.md)) for future human cognition calibration.
