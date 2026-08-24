# Cut the Cake — Tactical CAD Roadmap

**Document type:** Living strategic roadmap  
**North star:** A Tactical CAD system for competitive games  
**Current research checkpoint:** Round 11.4A — Inverse Tactical Repair Audit & External-Transfer Validation  
**Last strategic review:** 2026-08-23

---

# 1. North Star

Cut the Cake should grow from a tactical-clearability research project into a **Tactical CAD environment for competitive games**.

The long-term experience is simple to describe:

> Import or gray-box a competitive FPS map, declare routes / tactical scenarios / player capability assumptions, compile the geometry into information and deadline workloads, inspect where tactical overload occurs, simulate transparent team policies through the map, ask **why** a transition fails, synthesize a minimal repair, and replay the same scenario before and after the change.

The defining demo should be understandable in roughly sixty seconds:

1. Load a 6v6 gray-box map.
2. Press **Analyze**.
3. See serviceable, boundary-sensitive, knowledge-sensitive, and overloaded transitions.
4. Press **Play** and watch agents traverse the map while LOS, reticle state, deadlines, and Tactical Margin animate.
5. Pause at a red transition and press **Why?**
6. See the exact reveal / angle / deadline bottleneck.
7. Press **Repair**.
8. Watch the geometry change.
9. Replay the identical scenario before / after.
10. Export a technical report showing what changed, why it changed, and the confidence tier of the result.

A major future case-study target is a **manually reconstructed or legally sourced gray-box of a contemporary competitive FPS map** — including Modern Warfare beta maps — without requiring redistribution of proprietary art or game assets.

---

# 2. Product Thesis

The core idea is bigger than a difficulty score:

```text
GEOMETRY
   ↓
INFORMATION RELEASE
   ↓
ATTENTION / RETICLE WORKLOAD
   ↓
DEADLINE FEASIBILITY
   ↓
DIAGNOSIS
   ↓
REPAIR
   ↓
REPLAY / VERIFY
```

The eventual product proposition is:

> **A level is not only geometrically valid. It has tactical contracts that can be compiled, inspected, tested, and repaired before expensive human playtesting.**

Cut the Cake should therefore become a combination of:

- tactical static analyzer;
- map debugger;
- tactical simulator;
- inverse-design assistant;
- PCG constraint engine;
- external-engine verification system;
- eventually, a mixed-initiative competitive level-design environment.

---

# 3. What Cut the Cake Is — and Is Not

## It is

- a geometry-to-tactical-workload compiler;
- a scheduling and information-availability model;
- a Tactical Margin evaluator;
- a compositional PCG contract system;
- a diagnostic engine that can attribute bottlenecks to geometry;
- an inverse tactical repair engine;
- an external-engine validation framework;
- a future tactical map editor and model-execution simulator.

## It is not

- a claim that the current model fully predicts human players;
- a human-like Call of Duty bot project;
- a replacement commercial FPS engine;
- a reason to rewrite the validated scientific core in JavaScript or Rust;
- a full arbitrary-3D competitive-game simulator today.

**Architecture rule:** Python owns scientific truth. Visualization clients may edit, animate, scrub, compare, and request analysis, but should not independently redefine LOS, scheduling, Tactical Margin, or repair semantics.

---

# 4. Where We Are Now

## 4.1 Capability map

| Capability | Readiness | Current state |
| --- | --- | --- |
| Geometry → reveal/deadline compilation | **Strong** | 2D polygonal geometry + authored traversal |
| Single-reticle scheduling model | **Strong** | Exact model-scoped scheduling abstraction |
| Tactical Margin | **Strong** | Core serviceability metric |
| Static-metric counterexamples | **Strong** | LOS/threat count shown insufficient |
| Transfer contracts / composition | **Strong** | Finite angular-state compositional abstraction |
| PCG certification | **Strong** | Large automated candidate / generation work |
| Population simulation | **Strong** | Controlled families + transparent controllers |
| External ViZDoom translation | **Moderate–Strong** | Residual decomposition established |
| Actionability / map knowledge `ell*` | **Strong** | Model-level information threshold |
| Inverse tactical repair | **Moderate–Strong** | Constructive repair works but transfer is family-dependent |
| Robust cross-engine repair guarantee | **Early** | 75% transfer among source-successful 11.4A repairs |
| Visual explanation | **Active** | Full explainer + isolated concept prototypes |
| Tactical CAD editor | **Not built** | North-star product layer |
| Top-down tactical playback | **Not built** | Immediate product opportunity |
| Multi-agent 6v6 execution | **Very early** | Existing controller concepts, no team simulator |
| Real commercial-map import | **Not built** | Requires ingestion / abstraction workflow |
| Multi-level / full 3D tactical geometry | **Early** | Current model is planar / extruded |
| Human population calibration | **Optional future** | No longer a gate for the current program |

## 4.2 Round 11.4A canonical checkpoint

Current audited repair evidence:

- **50/50** layouts genuinely unserviceable at baseline (`M < 0`) and fatal in native ViZDoom;
- **40/50 (80%)** source-model grid-minimal repair success within the declared obstacle-translation operator set;
- **30/50 (60%)** native ViZDoom death → survival rescue;
- **30/40 (75%)** engine transfer efficiency among source-successful repairs;
- median edit distance **0.85 m**;
- mean export residual **+1.64 tics**;
- mean execution residual **-0.08 tics**;
- large family dependence, especially dense triad congestion where source→engine export residual dominates.

The important scientific interpretation is not “repair always works.” It is:

> **Tactical Margin can drive constructive geometric intervention, and source-certified repair frequently transfers to an independent engine, but robust deployment requires explicit treatment of export / engine residuals.**

That distinction should become a product feature, not merely a caveat.

---

# 5. Core Architecture

```text
                           CUT THE CAKE

                  ┌──────────────────────┐
                  │  Python Science Core │
                  │                      │
                  │ Geometry / LOS       │
                  │ Scheduler / Margin   │
                  │ Contracts / PCG      │
                  │ Diagnostics / Repair │
                  │ Engine adapters      │
                  └──────────┬───────────┘
                             │
                  versioned scene / result API
                             │
             ┌───────────────┴───────────────┐
             │                               │
   ┌─────────▼────────────┐       ┌──────────▼─────────┐
   │ Tactical CAD Client │       │ Engine Validation  │
   │                      │       │                    │
   │ Phaser.js first      │       │ ViZDoom now       │
   │ top-down 2D          │       │ Unreal adapter    │
   │ editor + playback    │       │ later             │
   └──────────┬───────────┘       └────────────────────┘
              │
       optional later view
       first-person / 3D
       (Three.js or engine)
```

## Versioned scene contract

A future `scene_manifest.json` / API should expose, at minimum:

- boundary and obstacle polygons;
- height/layer metadata when available;
- routes and route alternatives;
- ports / reset regions;
- team / agent spawn states;
- threat or opponent anchors;
- player capability assumptions;
- reveal and actionable timestamps;
- deadlines and service costs;
- reticle orientation / schedule state;
- Tactical Margin and confidence tier;
- bottleneck attribution;
- proposed repair(s);
- source-model and engine-conditioned results;
- tic-by-tic playback telemetry.

The renderer should consume this contract rather than reproducing scientific logic.

---

# 6. Roadmap Horizons

## Horizon 0 — Freeze and package Round 11.4A

**Status: NOW / near completion**

Goal: make the audited computational result a stable foundation before product expansion.

### Deliverables

- [x] Rebuild the benchmark as 50 genuinely broken layouts.
- [x] Separate source repair from engine rescue.
- [x] Add source / engine contingency matrix.
- [x] Add export / execution residual decomposition.
- [x] Make repair grid-minimal within declared translation operators.
- [x] Add stronger repair-preservation checks.
- [ ] Complete final scientific review of 11.4A wording and claims.
- [ ] Reconcile README / manuscript / explainer claims with 11.4A.
- [ ] Run full package regression suite, not only repair-specific tests.
- [ ] Create a named/tagged **11.4A research freeze**.

### Exit gate

A new contributor can clone the repo, rerun the benchmark, and recover the frozen 11.4A table with no off-repo context.

---

## Horizon 1 — Tactical Debugger vertical slice

**Status: NEXT PRODUCT MILESTONE**

Goal: prove the research can become an understandable instrument before building a full editor or 6v6 simulation.

### Build only one end-to-end case

- one map / arena;
- one authored route;
- 1 player vs 2–3 threats;
- top-down Phaser.js canvas;
- play / pause / timeline scrub;
- player position + reticle orientation;
- live LOS lines;
- release / deadline events;
- Tactical Margin overlay;
- click a bottleneck to open **Why?**;
- toggle **Broken / Repaired**;
- replay identical telemetry before / after.

### Technical deliverable

Create a stable Python → JSON export boundary rather than hard-coding data in the client.

### Exit gate

A technically literate stranger can watch one broken encounter, inspect the diagnosis, toggle the repair, and explain the project correctly without reading the paper.

---

## Horizon 2 — Tactical CAD editor foundation

Goal: move from a playback demo to an actual design workbench.

### Editor capabilities

- draw / move walls and baffles;
- create openings / doors;
- place threat anchors;
- draw traversal routes;
- define entry orientation;
- place ports / reset regions;
- set player-model parameters;
- save / load a versioned map format;
- undo / redo;
- pan / zoom / layer visibility;
- run **Analyze** on demand.

### Analysis overlays

- LOS / reveal events;
- Tactical Margin by route segment;
- boundary-sensitive transitions;
- knowledge-sensitive transitions / `ell*`;
- critical threat and controlling geometry;
- source-certified vs engine-robust confidence tier.

### Exit gate

A user can create a small gray-box from scratch and discover a tactical problem they did not manually encode as a label.

---

## Horizon 3 — Repair Workbench

Goal: make inverse design a first-class interactive workflow.

### Product interaction

```text
ANALYZE → WHY? → REPAIR OPTIONS → PREVIEW → VERIFY → ACCEPT
```

### Expand repair carefully

Current operator family is obstacle translation. Add operators one at a time with explicit provenance:

1. obstacle translation;
2. obstacle extension / contraction;
3. aperture width adjustment;
4. baffle insertion;
5. route-entry adjustment;
6. threat-anchor adjustment only as a separate authored-gameplay operator.

Do not mix operators into one opaque optimizer before each has isolated tests.

### Robust repair objective

Move from source-only:

`M_source >= epsilon`

toward an explicitly robust objective such as:

`M_source >= epsilon_source + reserve(export_family)`

or direct engine-conditioned verification when available.

### Exit gate

The tool can offer multiple interpretable repair candidates, explain their tactical effect, and distinguish **source feasible** from **externally verified**.

---

## Horizon 4 — Transparent team simulation

Goal: make whole-map tactical structure visible without pretending to simulate human cognition.

### Build incrementally

1. **1vN scheduling animator** — one moving agent, multiple threats.
2. **3v3 lane skirmish** — fixed routes and explicit policies.
3. **6v6 whole-map playback** — multiple routes, objectives, anchors, rotations.

### Agent policies

Use transparent policies rather than human-like AI:

- FIFO;
- nearest angle;
- earliest deadline;
- optimal scheduling bound;
- route-following assault;
- anchor / lane hold;
- flank route;
- objective rotation.

Every agent action should be attributable to a declared policy.

### Visual goal

The audience should be able to see:

- where LOS opens;
- which lanes are contested;
- when multiple jobs arrive;
- what the reticle / attention bottleneck is;
- where deadlines breach;
- how a geometry repair changes the same scenario.

### Exit gate

A before/after 6v6 playback makes a tactical bottleneck and its repair visually obvious without claiming human behavioral realism.

---

## Horizon 5 — Real-map case study pipeline

Goal: test the system on recognizable competitive FPS geometry rather than only synthetic fixtures.

### First target

Choose one relatively planar Modern Warfare beta map or sub-region and reconstruct a **research gray-box** from legally available reference material / manual tracing.

Do not redistribute proprietary textures, models, or game files.

### Required ingestion workflow

- image / reference underlay;
- scale calibration;
- polygon tracing;
- height / floor tagging;
- spawn / objective annotation;
- route hypotheses;
- sightline sanity checks;
- uncertainty annotations for inferred geometry.

### Analysis sequence

1. analyze a small lane / room transition;
2. compare alternate entry routes;
3. identify model bottlenecks;
4. compare against player / designer discourse where available;
5. run counterfactual geometry repairs;
6. clearly separate **model findings** from claims about actual player experience.

### Exit gate

Cut the Cake can explain at least one recognizable real-map tactical interaction in a way that is useful even to someone who disagrees with the model assumptions.

---

## Horizon 6 — 2.5D / multi-level tactical geometry

Goal: remove the largest geometry limitation blocking serious analysis of modern competitive FPS maps.

### Do not jump directly to arbitrary 3D

Start with layered tactical geometry:

- floor / elevation layers;
- stairs / ramps as transitions;
- windows / head-height openings;
- balconies / catwalks;
- vertical occlusion;
- height-conditioned threat anchors;
- layer-aware routes and ports.

Then evaluate whether full mesh-level raycasting is actually necessary.

### Exit gate

A multi-level map interaction can be compiled without flattening away the tactical cause of the encounter.

---

## Horizon 7 — Studio workflow integration

Goal: make the system useful inside a real level-design pipeline.

Possible forms:

- Unreal Editor plugin;
- command-line CI linter for map exports;
- batch analyzer over nightly gray-box builds;
- before/after diff report for geometry commits;
- tactical regression tests;
- team-facing web dashboard.

### Ideal studio loop

```text
Designer edits map
      ↓
Build/export
      ↓
Cut the Cake tactical lint
      ↓
No regression / flagged transitions
      ↓
Interactive Why? / repair preview
      ↓
Human playtest
```

Human playtesting becomes complementary evidence rather than the first place tactical problems are discovered.

---

## Horizon 8 — Tactical intent → geometry

**Moonshot research / product horizon**

Move from analyzing existing geometry to synthesizing geometry from tactical intent.

Example specification:

```text
MODE: 6v6 Hardpoint

STRUCTURE
- 3 primary lanes
- 2 flank connectors
- central contest space
- anchor positions

TACTICAL CONTRACT
- no blind-overloaded primary entry
- first-contact margin >= target reserve
- selected flanks may be knowledge-sensitive
- bounded actionability requirement
- reset opportunity between major engagements
```

Then generate or co-design geometry satisfying those constraints.

The mature product becomes a **mixed-initiative Tactical CAD system** rather than an automatic map generator: the designer owns intent, the compiler owns verification, and the repair/generation system offers constrained alternatives.

---

# 7. Parallel Research Threads

These are valuable but should not block the Tactical CAD path.

## A. Capability envelopes

For geometry `G`, study the region:

`C_G = {(A, omega, p, ell, ...): M_G >= 0}`

This lets the system ask what modeled capability is required rather than labeling encounters simply “easy” or “hard.”

**Future human role:** empirical player data could later calibrate population distributions onto these envelopes.

## B. Robust transfer / deployment reserve

Round 11.4A shows one global guard band is probably too crude. Investigate:

- geometry-family-conditioned reserve;
- export-resolution sensitivity;
- robust optimization against quantization;
- engine-conditioned repair;
- confidence intervals / worst-case residual bounds.

## C. Tactical motif discovery

As the library grows, identify recurring structures:

- sequential slice;
- simultaneous divergent crossfire;
- deep baffle;
- seam leakage;
- knowledge trap;
- reset pocket;
- alternating reticle thrash.

Long term, these may become a computational **design grammar**.

## D. Human validation

Keep the existing protocol as prospective work. Do not require it to justify the current compiler / repair system.

A later human study should answer a narrower question:

> Where do actual player populations sit relative to model-derived capability and information boundaries?

---

# 8. Technology Decisions

## Keep

**Python** for:

- geometry compiler;
- scheduler;
- Tactical Margin;
- transfer contracts;
- diagnostics;
- repair;
- PCG;
- benchmark / statistics;
- engine adapters.

## Use next

**Phaser.js** for the first Tactical CAD / debugger because the immediate product is primarily:

- top-down;
- 2D / 2.5D;
- interactive;
- timeline-driven;
- overlay-heavy;
- easy to distribute in a browser.

## Add only when justified

**Three.js** for synchronized first-person / 3D views when top-down explanation is insufficient.

**Rust / Bevy** only if native performance, packaging, simulation scale, or long-term desktop-product requirements become actual bottlenecks. Do not rewrite validated science for architectural aesthetics.

**Unreal** as a future integration target, not as the scientific source of truth.

---

# 9. Near-Term Sequence

This is the recommended work order from the current checkpoint.

### Now

1. Finish review and freeze Round 11.4A.
2. Bring README / manuscript claims into exact alignment with the audit.
3. Continue the modular visual-explainer cleanup independently.

### Then

4. Define `scene_manifest` v1.
5. Build the **single-room Tactical Debugger vertical slice**.
6. Use one robust Round 11.4A repair pair as the canonical Broken → Diagnose → Repair → Replay demonstration.

### Only after the vertical slice feels right

7. Add basic editor operations.
8. Add repair preview / acceptance.
9. Add 1vN tactical playback.
10. Expand to 3v3 and then 6v6.

### After the simulator exists

11. Build the real-map ingestion workflow.
12. Analyze one Modern Warfare beta gray-box case study.
13. Decide from that experience whether layered 2.5D geometry is sufficient or whether a richer 3D compiler is necessary.

---

# 10. What Would Make This Project Defining?

The project becomes defining if it can demonstrate all four of these in one coherent system:

### 1. **Compile**
Turn spatial geometry into tactical information / deadline contracts.

### 2. **Explain**
Identify exactly why a transition is overloaded.

### 3. **Repair**
Generate a small, interpretable geometric intervention.

### 4. **Replay**
Show the identical tactical scenario before and after the repair.

The studio-level pitch is then:

> **Cut the Cake finds tactical geometry failures before a player enters the map, explains the mechanism, proposes a repair, and lets the designer replay the consequence.**

That is the north star against which future experiments, interfaces, and engineering work should be judged.
