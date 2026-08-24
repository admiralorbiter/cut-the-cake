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
- **Milestone 2D / 2D.1 (M2D — Completed & Scientifically Frozen):** Scenario Authoring, Interactive Playback & Safe Solver Envelope:
  - Interactive scenario authoring: route creation, waypoint editing, route speed tuning ($v_{\text{move}}$), combat parameters ($\omega_{\text{slew}}, T_{\text{acq}}, T_{\text{serv}}$), and initial reticle azimuth.
  - Interactive time-indexed playback scrubbing with synchronized player cone and authoritative LOS visibility rays.
  - Fast path vs full simulation dual-mode analysis dispatch.
  - Safe Exact-Solver Envelope ($J \le 6$ `EXACT_INTERACTIVE`, $J=7$ `EXACT_SLOW`, $J \ge 8$ `EXACT_LIMIT_EXCEEDED` fail-closed dispatch).
- **Milestone 2E (M2E — Completed & Scientifically Frozen):** Mixed-Initiative "Auto-Fix" Integration & Closed-Loop Repair:
  - Envelope-aware CAD Auto-Fix search derived from and differentially certified against the validated `MinimalRepairOptimizer` operator/search contract.
  - Strict tri-state candidate classification: `EXACT_EVALUATED` ($J \le 6$), `UNSUPPORTED_ENVELOPE` ($J \ge 7$), `INVALID_GEOMETRY` (clearance/boundary violation).
  - Selected route ($v_{\text{move}}$) and authored initial reticle heading ($\theta_0$) parity throughout diagnosis and candidate evaluation.
  - Independent post-search authoritative re-certification on $G^*$ via frozen `analyze_cad_document()`.
  - Stale-proposal concurrency defense via SHA-256 source document hash checking (HTTP 409 `STALE_REPAIR_PROPOSAL`).
  - REST endpoint `POST /api/document/auto_fix` supporting both preview (`commit: false`) and atomic commit (`commit: true`) with snapshot history.
  - Web CAD workbench integration: interactive "Auto-Fix" button, keyboard shortcut [A], proposal banner with target margin badges, ghost obstacle rendering, and full undo/redo stack.
  - Full closed-loop verification: Canonical F1 baffle stagger repaired ($\mathcal{M}_0 = -6 \to \mathcal{M}_1 = +2\text{ tics}$ with minimal shift $1.10\,\text{m}$), 100% pass across deterministic unit tests, differential equivalence tests, metamorphic invariants, and Playwright browser E2E workflows.
- **Milestone 2F (M2F / M2F.2 — Completed, Verified, & Scientifically Frozen):** Live Spatial Heatmaps & Suffix Tactical Margin
  - **Counterfactual Suffix Formulation:** Defined discrete 35 Hz tic-aligned Suffix Tactical Margin $\mathcal{M}_{\text{suffix}}(s_k) = -L^*(\{\tilde{r}_j(s_k), \tilde{D}_j(s_k), \theta_j(s_k), p_j\}; \theta_0)$ evaluating encounters from movement sample $s_k$ to the route terminus.
  - **Route-Tic Stepping Alignment:** Suffix evaluation uses the compiler's discrete stepping rule ($s_k = k \cdot v\Delta t$, stopping when $s_k > L$), guaranteeing exact domain identity and eliminating fractional endpoint edge cases.
  - **Entrance Equivalence Identity by Construction:** Full floating-point angle preservation ($\theta_j(s_k) = \text{float}(\text{vis\_angle})$ without pre-solver rounding) guaranteeing exact structural and margin identity $\mathcal{M}_{\text{suffix}}(0) \equiv \mathcal{M}_{\text{authoritative}}$ at the route entrance across all fixtures.
  - **Exact Envelope Boundary ($J \le 6 \to \text{exact}$, $J \ge 7 \to \text{UNSUPPORTED}$):** Live spatial repeated scheduling fails closed on $J \ge 7$ encounters (`#a855f7`, `suffix_margin_tics = None`) to prevent multi-second factorial hangs across route traverses, while preserving geometric LOS concurrency $\mathcal{K}(s)$.
  - **5-Band Status Classification:** `QUIESCENT` ($J_{\text{suffix}} = 0$, `#64748b`), `SAFE` ($\mathcal{M}_{\text{suffix}} \ge +2$, `#22c55e`), `CONTESTED` ($0 \le \mathcal{M}_{\text{suffix}} < 2$, `#eab308`), `CRITICAL` ($\mathcal{M}_{\text{suffix}} < 0$, `#ef4444`), and `UNSUPPORTED` ($J_{\text{full}} \ge 7$, `#a855f7`).
  - **Original-Clock Deadline Headroom ($\delta_{\text{min}}(k)$):** Orthogonal temporal metric $\min_{j \in \mathcal{A}_k}(D_j - k)$ tracking remaining slack on the original route-entry clock alongside counterfactual suffix margin.
  - **Arena Floor LOS Exposure Density Grid:** Separately calculated 2D scalar field $\mathcal{K}(x,y) = |\{j : \text{LOS}((x,y), q_j) = 1\}|$ on navigable floor cells with strict obstacle and boundary masking.
  - **REST Spatial Analysis Endpoint:** Dedicated `POST /api/document/heatmap` and `GET /api/document/heatmap` serving route samples, $\delta_{\text{min}}(k)$, and optional 2D floor grid with SHA-256 provenance tagging, end-to-end browser SHA concurrency defense (`expected_doc_hash` $\to$ HTTP 409 `STALE_DOCUMENT_HASH`), client revision ordering, and resolution validation ($0.05 \le \Delta g \le 5.0$).
  - **Web CAD Interactive Layer:** Color-coded glowing segmented route ribbon, toggle button `[H]`, HUD legend overlay, floor grid checkbox, and hover tooltip displaying Suffix Margin, Original-Clock Deadline Headroom, and LOS Concurrency.
  - **Verification:** 100% pass across 11 deterministic unit/API tests (including fractional route endpoint parity, angular-boundary discretization parity, approach interval margin improvement, and parameterized 2D rotation/translation invariance) and Playwright browser E2E workflows (`e2e_spatial_heatmap.png`).

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

- **Milestone 5-A & 5-A.1 (Completed & Scientifically Frozen at `e35e3a8`):** Calibrated Real-Map Transfer Case Study (Dust II: A-Long to A-Site / Pit)
  - **Metric Graybox Reconstruction & Overview Affine Calibration:** Reconstructed metric `CADDocument` fixture of Counter-Strike Dust II A-Long engagement zone ($1.0\,\text{unit} = 1.0\,\text{meter}$, corridor width $\approx 6.0\,\text{m}$, length $\approx 28.0\,\text{m}$). Affine transform fitted against 5 Valve Source overview landmarks (`pos_x=-2476, pos_y=3239, scale=4.4`, declared hull conversion $0.01905\,\text{m/unit}$) achieves internal coordinate consistency residual $\mathrm{RMSE} = 0.0064\,\text{m} < 0.020\,\text{m}$.
  - **Strict 2D Navigability & Positive Clearance:** Enforced $\ge 0.50\,\text{m}$ positive clearance (actual min: $0.636\,\text{m}$) and zero geometric intersections with obstacle polygons across all 3 routes.
  - **Multi-Route Tactical Differentiation & Reveal Ordering:**
    - `route_pieing` (outer-wall angle slice): isolates Corner defender at $k=0$ and delays Pit until $k=47$ ($\Delta r = 47\text{ tics} = 1.34\,\text{s}$).
    - `route_wide_swing` (aggressive open choke entry): reveals Corner and Pit with tight collapse ($\Delta r = 26\text{ tics} = 0.74\,\text{s}$), producing acute simultaneous line-of-sight ($K_{\text{LOS}} = 2$).
  - **Scientific Protocol Finding (Global $\mathcal{M}$ vs Approach $\mathcal{M}_{\text{suffix}}(s)$):**
    - Pre-registered hypothesis of global scalar dominance $\mathcal{M}_{\text{pie}} \ge \mathcal{M}_{\text{wide}}$ was falsified at the baseline fixture ($\mathcal{M}_{\text{pie}} = +1, \mathcal{M}_{\text{wide}} = +2$) due to whole-route schedule slew geometry.
    - Preserved the narrower supported physical invariants: universal reveal stagger $\Delta r_{\text{pie}} > \Delta r_{\text{wide}}$ across all speeds ($v \in [3.0, 6.0]\,\text{m/s}$), and approach-interval suffix-margin superiority $\min_{s \in [2, 4]} \mathcal{M}_{\text{suffix}}^{\text{pie}}(s) > \min_{s \in [2, 4]} \mathcal{M}_{\text{suffix}}^{\text{wide}}(s)$ across all velocities.
  - **Paired Pocket Sightline Isolation:** High push reveals Plat defender past corner ($k=195$), while Pit branch strictly occludes Plat defender behind corner geometry.
  - **Full Joint Parameter Uncertainty Sweep:** Evaluated an 81-run factorial grid ($v \in [3.5, 4.5, 5.5]$, $\omega \in [270, 360, 450]$, $\Delta \mathbf{q} \in [-0.3, 0.0, +0.3]$, $\Delta D \in [-0.05, 0.0, +0.05]$) asserting effective route velocity mutation and verifying stagger inequality (81/81) and approach suffix superiority (81/81).
  - **Deterministic Result Packet:** Persisted exact snapshot to `results/m5a_dust2_a_long.json` (locked by SHA-256 hash `d425ce5a4df7ec35`).
  - **Verification:** 100% pass across 9 unit/API test gates and 5 Playwright browser E2E workflows (102 tests in CAD acceptance suite).

- **Milestone 5-B (Completed & Certified):** Pre-Registered Multi-Engagement Falsification Cross-Section
  - **Two-Stage Pre-Registration Protocol:** Sealed hypotheses, source citations, control points, and blinded route IDs (`route_A`, `route_B`) in `preregistration/m5b_preregistration.json` and committed at `9c59a38` *prior* to model execution.
  - **Cross-Section Mechanisms Evaluated:**
    1. **Valorant Ascent (A-Main / Wine)**: Off-angle serialization confirmed. Wine slice ($\mathcal{M}_{\min} = -20$) strictly outperforms direct center rush ($\mathcal{M}_{\min} = -24$). Stepping into Wine mouth achieves isolated $K=1, \mathcal{M}_{\text{suffix}} = +3$ while direct rush suffers $K=3, \mathcal{M}_{\text{suffix}} = -26$. A-Site Heaven/Rafters verticality acknowledged as explicit 2D model boundary limitation.
    2. **Counter-Strike Dust II (Upper B-Tunnels Exit)**: Multi-angle choke crossfire collapse confirmed as an expected negative. Both dry routes suffer immediate $K \ge 2$ crossfire at exit ($s \le 0.4\,\text{m}$) and severe exit deficit ($\mathcal{M}_{\min} = -7$), proving the model refuses to fabricate false serialization on compressed dry chokes.
    3. **Modern Warfare 4 (Transit 213 Center Lot)**: Occluder lattice confirmed. Bus lattice weave ($\mathcal{M}_{\min} = -4$) preserves superior cover over open lot push ($\mathcal{M}_{\min} = -19$).
  - **Deterministic Result Matrix:** Persisted aggregate unblinded matrix in `results/m5b_cross_section.json`.
  - **Verification:** 100% pass across 7 deterministic cross-section test gates and Playwright browser screenshot workflows (109 tests in CAD acceptance suite).

---

## Horizon 3: Multi-Operator Repair Workbench (M3)
- Expand repair operators informed by observed real-world failure demand:
  1. Aperture resize / choke narrowing;
  2. Small cover lip / occluder insertion;
  3. Obstacle translation (current $\mathcal{T}_{\text{obs}}$);
  4. Obstacle extension / contraction;
  5. Route waypoint / entry angle adjustment.
- Heterogeneous cost model: $\mathcal{C}(\mathcal{G}, \mathcal{G}') = w_{\text{move}} d_{\text{wall}} + w_{\text{resize}} \Delta A + w_{\text{insert}} N_{\text{new}} + w_{\text{route}} \Delta L$.

---

## Horizon 6: 2.5D Elevation & Layered Geometry (M6)
- **Milestone 6-A / 6-A.1 (Completed, Verified & Frozen):** 2.5D Elevation & Azimuth/Elevation Aim State Preflight & Contract Hardening
  - **Spherical Geodesic Slew Metric:** Generalized $1 \mid r_j, s_{ij} \mid L_{\max}$ transition cost oracle to spherical geodesic distance on the unit sphere: $\Delta \alpha_{ij} = \arccos(\operatorname{clamp}(\sin \phi_i \sin \phi_j + \cos \phi_i \cos \phi_j \cos(\theta_i - \theta_j), -1.0, 1.0))$.
  - **Structural Planar Identity & Differential Parity:** When $\phi_i = \phi_j = 0.0^\circ$, executes exact frozen 2D `angle_diff_deg()`. Differential baseline comparison across all 6 fixtures, 11 routes, and document hashes proves bit-for-bit identity of the frozen CAD analysis contract against pre-M6 `4e81dd7` outputs.
  - **Authority Semantics & Schema Bounds:** `CADThreat.elevation_deg` is authoritative in M6-A with strict schema and validator enforcement $\phi \in [-90.0^\circ, 90.0^\circ]$. `z_m` and `eye_height_m` are reserved metadata for geometric derivation in M6-B.
  - **Fail-Closed Elevated Telemetry:** Requesting simulation telemetry on elevated documents returns `telemetry_status = "ELEVATED_EXECUTION_UNSUPPORTED_M6A"` with unmixed fail-closed diagnostics.
  - **Ascent Mechanism Counterexample:** Demonstrates synthetically on an Ascent Heaven/Rafters-inspired fixture that elevation ($\phi = 35^\circ$) introduces real pitch slew latency ($s_{12} = 4\text{ tics}$), converting a falsely feasible 2D schedule ($M=+1$) into a critical deficit ($M=-3$), proving that the newly added elevation state is sufficient to produce the class of scheduling error identified by the Ascent M5-B boundary.
  - **Eight Verification Gates:** Passed 100% across differential planar identity, pure pitch slew, mixed $(\theta, \phi)$ non-equivalence vs naive decoupled metrics, boundary discretization, $\mathrm{SO}(3)$ 3D rotation invariance, Ascent mechanism counterexample, exact solver envelope preservation ($J \le 6$ interactive, $J=7$ slow, $J \ge 8$ fail-closed by default), and schema bounds / fail-closed telemetry (121 tests in CAD acceptance suite).

- **Milestone 6-B (Completed & Certified):** Height-Aware Geometric Compilation & 2.5D Sightline Occlusion
  - **2.5D Extruded Prism Model:** Generalized obstacles to vertical prism footprints $P_i \times [z_{i,\min}, z_{i,\max}]$, routes to 3D waypoints $(x, y, z_{\text{feet}})$, and threats to 3D target coordinates $\mathbf{q}_j = (x_j, y_j, z_j)$.
  - **Derived Dynamic Aim State:** Authored target elevation replaced with authoritative dynamic geometry formula $\phi_j(s) = \operatorname{atan2}(z_j - z_{\text{eye}}(s), d_{xy}(s))$ along player trajectory, feeding the frozen M6-A single-machine discrete scheduler seamlessly.
  - **Explicit Authority Migration:** Formally established `ElevationMode.GEOMETRIC` (M6-B default derived $\phi$) and `ElevationMode.AUTHORED` (legacy M6-A) without ambiguous competition.
  - **Eight Verification Gates:** Passed 100% across complete planar bit-for-bit identity, analytic vertical occlusion ($z_{\text{low}}$ blocked vs $z_{\text{high}}$ clear), obstacle-height monotonicity, derived pitch correctness ($+45^\circ, -45^\circ, 0^\circ$), dynamic ramp slew, height-induced reveal differentiation ($R_j^B < R_j^A$), rigid vertical translation invariance ($z \to z + c$), and calibrated Ascent Heaven fixture compilation (129 tests in CAD acceptance suite).

- **Milestone 6-C (Next Focus):** 3D Controller Execution & Real-Map Transfer (3D pitch controller execution, elevated telemetry verification, multi-story competitive graybox benchmark).

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
