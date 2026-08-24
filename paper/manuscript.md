# From Reachable to Readable: Composable Tactical Clearability Contracts for Procedural First-Person Shooter Levels

**Research Manuscript & Findings Freeze**  
*Big Brain Time Research Collective*  
**Date:** August 2026  

---

## Abstract

Procedural Content Generation (PCG) in competitive first-person shooter (FPS) level design faces a fundamental legibility barrier. While graph grammars and tile synthesis algorithms reliably guarantee topological reachability and asset compatibility, dynamically assembled environments frequently degenerate into chaotic, multi-angle crossfires where skilled tactical play collapses into unmanageable gambling.

In this paper, we show that for a fixed movement trajectory $\gamma$, tactical clearability reduces to a **non-preemptive single-machine real-time scheduling problem with release times, due dates, and sequence-dependent setup times ($1 \mid r_j, s_{ij} \mid L_{\max}$)**, where the player's single reticle acts as a stateful processor bottleneck. We define **Optimal Maximum Lateness** $L^*(\gamma) = \min_\pi \max_j (C_j^\pi - D_j)$ and **Tactical Margin** $\mathcal{M} = -L^*$ as the formal criteria for temporal serviceability within the declared model.

Through a progression of formal counterexamples, we document the collapse of simpler spatial summaries: static line-of-sight cliques ($K_{\text{static}}$) discard release timing; scalar arrival curves discard angular orientation; and state-conditioned Demand Bound Functions (DBFs) fail under non-distributive infimum-supremum compositions. We prove that the exact composable abstraction is the **Exact State-Conditioned Spatial Transfer Map** $C_M[(p_{\text{in}}, a), (p_{\text{out}}, b)] \in \mathbb{R}_{\ge 0} \cup \{+\infty\}$, operating over $(\min, +)$ dioid algebra.

We validate this framework across an end-to-end computational pipeline:
1. **Geometry-to-Contract Compilation:** Automatically compiles continuous 2D polygonal map geometry into discrete angular transfer matrices ($K=8$) via critical-LOS ray-vertex events with sub-millisecond precision ($<0.1\,\text{ms}$).
2. **Precertified PCG Linter (Condition E):** Under the declared quiescent-interface assumptions, all accepted assemblies in the reported 25,000-candidate experiment were deadline-feasible, eliminating runtime scheduling overhead.
3. **Discrete Simulation Population Benchmark (Round 11S):** Evaluated across 60 parameterized micro-arenas spanning 6 distinct geometric mechanisms under 5 independent controllers ($9,000$ discrete simulation episodes on a 35 Hz logic clock using a paired common-random-number design). Tactical Margin achieves strong construct validity across held-out geometric families (**$\text{LOGFO-AUC} = 1.0000$, $\rho = +0.9282$**), outperforming peak physical line-of-sight concurrency ($K_{\text{static}}$, $\text{LOGFO-AUC} = 0.8098$, $+19.02\%$), cumulative Hamiltonian workload ($0.8260$, $+17.40\%$), and static minimum slack ($0.5742$, $+42.58\%$).
4. **Native Game Engine Translation (ViZDoom):** Evaluated across 12 binary WAD micro-arenas in headless C++ ZDoom. Measured three-layer lateness residuals yield a mean absolute residual of $0.83\,\text{tics}$ ($23.7\,\text{ms}$), with an empirical deployment reserve $\epsilon_{\text{deploy}} = 3\,\text{tics}$ ($85.7\,\text{ms}$) providing 100% survival on deployable arenas.
5. **Actionable-Information Parameterization ($a_j$):** Introducing the actionable-information timestamp $a_j$ connects map knowledge to the established scheduling distinction between non-anticipatory setup (reveal-gated: $a_j = r_j$) and anticipatory setup (pre-aim: $a_j = 0$), defining the **Tactical Value of Map Knowledge** $\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$.
6. **Inverse Tactical Repair & Automated Level Linter:** Formulates grid-minimal geometric repair over a declared obstacle-translation operator set $\mathcal{T}_{\text{obs}}$, isolating critical scheduling bottlenecks to directed occluder perturbations. Across an audited 50-arena benchmark of genuinely unserviceable micro-arenas ($100\%$ initial $\mathcal{M} < 0$, fatal baseline in native ViZDoom), the optimizer achieves an **80.0% source-model repair success rate** (40/50, median edit distance $0.85\,\text{m}$), a **60.0% native ViZDoom engine rescue rate** (30/50), and a **75.0% engine transfer efficiency** (30/40), with export and execution residual decomposition exposing family-dependent transfer limits.

---

## 1. Introduction

### 1.1 The Readability Problem in Competitive FPS PCG
Procedural content generation has transformed rogue-likes, action RPGs, and survival games. In high-consequence competitive first-person shooters (e.g., *Counter-Strike*, *Valorant*, *Call of Duty* Search and Destroy), however, PCG remains virtually absent from competitive play.

The barrier is not computational reachability or geometric validity. Modern search-based PCG and Wave Function Collapse (WFC) algorithms effortlessly ensure that every room connects, every objective is navigable, and assets fit seamless geometric boundaries. The failure is **epistemic and cognitive**: competitive FPS gameplay relies fundamentally on the player's ability to turn observation, positioning, and movement into reliable information.

When an algorithm generates spaces with unbounded, concurrent lines of sight, tactical reasoning collapses. Players entering a new space cannot isolate threats sequentially; they are exposed to multiple independent lethal angles simultaneously. At fast reaction regimes, this forces an un-isolatable gamble: whichever angle the player does not pre-aim kills them before they can acquire the target.

```text
[The Epistemic Hierarchy of Level Design]

      REACHABILITY        ──> "Can the player physically get there?"
           │                  (Solved: Navmesh / Graph Search)
           ▼
       VISIBILITY         ──> "What geometry renders from here?"
           │                  (Solved: Isovists / Rendering PVS)
           ▼
  TACTICAL CLEARABILITY   ──> "Can a player acquire the information required to 
                              navigate this space without being forced into an 
                              un-isolatable, multi-angle gamble?"
                              (The Geometrically-Induced Scheduling Problem)
```

### 1.2 The "Slicing the Pie" Tactical Primitive
In professional tactical doctrine and competitive shooter practice, spatial clearing is governed by the principle of **"slicing the pie"** (sequential angle isolation). A player approaching an occluded threshold creates distance from the corner and advances incrementally, revealing successive slices of the unknown room ($T_1 \to T_2 \to T_3$). This ensures that at any single instant, the player is exposed to at most one un-inspected threat sector.

When spatial geometry violates this primitive by simultaneously revealing non-contiguous threat sectors ($\emptyset \to \{T_1, T_2, T_3\}$), tactical skill collapses into arbitrary risk.

### 1.3 Case Study: Modern Warfare 4 "Kill Block"
In August 2026, Infinity Ward introduced *Kill Block* into the Modern Warfare 4 Beta. Kill Block dynamically recombines three authored, high-fidelity modular "Slabs" (End Slab A + Central Slab + End Slab B) into over 500 layout combinations under 10v10 single-life Gunfight rules.

Despite handcrafted internal cover, Kill Block suffered from widespread player frustration regarding chaotic sightlines, overwhelming verticality, and cross-map sniper dominance. Slabs officially designed for "combat from multiple angles" connect across open boundary interfaces, allowing sightlines to spill across the entire map. Kill Block demonstrates that **modular authoring does not solve the PCG readability problem**.

### 1.4 Central Intellectual Progression & Novelty Boundary
To our knowledge, prior FPS PCG work has evaluated generated maps using graph topology, design heuristics, simulated bot gameplay outcomes, player preferences, and static visibility measures, but has not modeled tactical traversal as a geometry-induced, deadline-constrained information-service problem.

The scientific arc developed in this work spans nine core insights:
1. **Reachability does not imply tactical readability:** Graph connectivity does not guarantee human clearability.
2. **Static visibility does not characterize clearability:** Simultaneous line-of-sight counts ($K_{\text{static}}$) and visible areas fail bidirectionally.
3. **Geometry induces a temporal information workload:** Locomotion unoccludes threats at release timestamps $r_j$ with response deadlines $D_j$.
4. **Reticle orientation makes that workload stateful and sequence-dependent:** A single reticle cannot point in two directions at once; motor slew $q_{i, j}$ depends on angular distance $\Delta\theta$.
5. **Tactical Margin $\mathcal{M} = -L^*$ characterizes serviceability within the declared model:** Evaluates the temporal reserve before hostile deadline breach.
6. **State-conditioned transfer contracts allow modular composition:** Operating over $(\min, +)$ dioid algebra over discrete angular sectors.
7. **Geometry can be compiled directly into contracts:** Continuous 2D visibility polygon sweeps extract exact transfer matrices.
8. **Prior knowledge alters information availability through $a_j$:** The unified recurrence $C_j = \max(r_j, \max(C_{j-1}, a_j) + q_{j-1, j}) + A + p_j$ separates reveal-gated ($a_j = r_j$, non-anticipatory setup) from pre-aim ($a_j = 0$, anticipatory setup) regimes.
9. **Tactical Value of Map Knowledge is quantified by $\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$:** Quantifying how the same physical layout changes serviceability across different information regimes.

---

## 2. Explicit Evidence Hierarchy

To maintain scientific rigor and avoid over-generalization, the claims in this paper are bounded by an explicit six-tier evidence hierarchy:

| Layer | Experimental Basis | Supported Claim | Claims Explicitly NOT Supported |
| :--- | :--- | :--- | :--- |
| **1. Formal** | Mathematical proofs & analytical counterexamples | Model-level single-reticle scheduling properties & $(\min, +)$ compositionality | Human psychological behavior or general player cognition |
| **2. Geometry** | Continuous 2D visibility bisection & 10 adversarial fixtures | Sub-millisecond polygonal geometry $\to$ discrete contract compilation ($K=8$) | Unstructured arbitrary 3D non-planar environments |
| **3. PCG** | 25,000-candidate corpus sweeps & $N=30$ paired-seed MAP-Elites | Model-scoped compositional certification & zero-overhead linting (Condition E) | Universal playability across un-modeled gameplay mechanics |
| **4. Simulation** | 60 micro-arenas $\times$ 5 controllers $\times$ 30 trials = $9,000$ episodes | Construct validity, baseline discrimination, and noise robustness | Population validity across arbitrary human player cohorts |
| **5. ViZDoom & Repair** | 12 reference arenas + 50-arena audited population repair benchmark in headless C++ ZDoom | Three-layer residual decomposition ($\Delta_{\text{export}} L, \Delta_{\text{execution}} L$) and external-transfer validation | Closed predictive validity across full commercial game engines |
| **6. Human (Prospective)** | Capability Envelope bounds $\mathcal{C} = \{(A, \omega, p) : \mathcal{M} \ge 0\}$ & frozen pilot protocol | Model-scoped boundary conditions and hypothesized familiarity transitions (H1–H4) | Empirical population calibration of human shooter cohorts |


---

## 3. Related Work & Literature Positioning

```text
                                [PRIOR ART TAXONOMY]

    FPS Search-Based PCG & Quality-Diversity     Modular & Path-Conditioned PCG
    • Cardamone et al. (2011), Cachia et al.     • Dormans (2010), Karth & Smith (WFC)
    • de Donato, Lanzi & Loiacono (2026)         • Path2Patrol (Zhang et al., CoG 2026)
    • Focus: Combat time, emergent bot metrics   • Focus: Tile matching, stealth path feasibility
                     │                                           │
                     └─────────────────────┬─────────────────────┘
                                           │
                                           ▼
                            Isovists, Space Syntax & Pursuit-Evasion
                            • Benedikt (1979), Summers (2014) - Counter-Strike VGA
                            • Pech, Lam & Masek (2020) - Tactical terrain classification
                            • Guibas et al. (1999) - Visibility-based pursuit-evasion
                                           │
                                           ▼
                            Real-Time Scheduling & Timing Interfaces
                            • Tanaka et al. (2021) - 1 | r_j, s_ij | L_max scheduling
                            • Morais, Bulhões, and Subramanian (2024) - Anticipatory vs non-anticipatory setup
                            • Shin & Lee (2003), RTC - Compositional timing interfaces
                                           │
                                           ▼
                       [THE NOVEL INTERSECTION: TACTICAL CLEARABILITY]
         Geometry-induced deadline-constrained information workload on a stateful single reticle
```

### 3.1 Search-Based PCG & Quality-Diversity in First-Person Shooters
Search-based procedural generation has evolved FPS layouts using genetic algorithms and automated bot play-testing. Cardamone et al. (2011) evolved maps optimizing for average combat encounter time. Cachia, Liapis, and Yannakakis (2015) evolved multi-floor shooter levels, balancing vantage points and sniper lanes using simulated agents. Lanzi, Loiacono, and Stucchi (2014) evolved maps optimizing for match balancing in first-person shooters. 

Most recently, de Donato, Lanzi, and Loiacono (2026) applied MAP-Elites to generate FPS levels, explicitly distinguishing *topological features* (computed directly from floorplan graphs) from *emergent gameplay features* (requiring full match simulations with AI agents).

*Scholarly Distinction:* We view our work as directly complementary to emergent gameplay PCG. Where de Donato et al. ask *"How does this generated map perform over a full simulated deathmatch?"*, our framework asks a prior, localized question: *"Before simulating an entire match, does a specific geometric transition force the player to process more threat information than is temporally serviceable?"* Rather than relying on post-hoc aggregate bot statistics, Tactical Margin provides a hard, analytical compile-time admissibility constraint.

### 3.2 Modular Assembly & Path-Conditioned PCG
Dormans (2010) and van der Linden, Lopes, and Bidarra (2014) established graph grammars to decouple high-level gameplay missions from spatial geometry. Karth and Smith (2017) popularized Wave Function Collapse (WFC) to ensure local geometric socket matching. In contemporary work, *Path2Patrol* (Zhang et al., IEEE CoG 2026) takes a designer-specified player solution trajectory and procedurally generates stealth guard patrol schedules that guarantee the intended trajectory remains feasible.

*Scholarly Distinction:* Path2Patrol establishes the precedent of designer-conditioned trajectory feasibility. However, while Path2Patrol solves the inverse problem of generating dynamic guard patrols around a stealth path ($\text{fixed path} + \text{guard generation} \to \text{path feasible}$), our framework solves the tactical combat problem where static geometry itself induces a release/deadline information workload on a single-reticle resource ($\text{fixed path} + \text{static geometry} \to \text{reticle schedulability}$). Furthermore, our framework compiles these guarantees into composable module transfer contracts.

### 3.3 Isovists, Space Syntax & Tactical Terrain Metrics
Benedikt (1979) established isovists (the continuous 2D/3D polygon of visible space from a viewpoint). Turner et al. (2001) expanded this into Visibility Graph Analysis (VGA), which Summers (2014) applied to spatial intelligibility in *Counter-Strike* maps. Pech, Lam, and Masek (2020) developed quantifiable isovist and graph-based metrics, surface connectivity, and raycasting to automatically classify and generate tactical terrain archetypes (vantage points, strongholds, chokepoints, hidden areas).

*Scholarly Distinction:* Pech et al. ask: *"What tactical archetype of place is this?"* (static geometric semantics). Our framework asks: *"Can a human player safely service the temporal sequence of visibility events this place reveals?"* (path-dependent cognitive schedulability). A large isovist, a 3-threat cluster, or a $150^\circ$ angular spread is not intrinsically unplayable; failure occurs only when the interaction of release timestamps, reticle slew distances, and hostile deadlines exceeds the single-reticle processing capacity.

### 3.4 Visibility-Based Pursuit-Evasion and Spatial Search
A foundational literature in computational geometry and robotics addresses visibility-based pursuit-evasion in polygonal environments (Guibas, Latombe, LaValle, Lin, & Motwani, 1999; LaValle et al., 2002; Sachs, LaValle, & Rajko, 2004). These algorithms construct finite information state spaces from critical visual line-of-sight inflection events (grazing rays across obstacle vertices) and determine whether one or more searchers can guarantee eventual detection of an arbitrarily fast evader.

*Scholarly Distinction:* Pursuit-evasion studies whether an environment can *eventually* be cleared ($\exists \text{ strategy that acquires all information}$). Tactical clearability addresses *time-critical serviceability*: visibility events generate discrete computational jobs that must be acquired and serviced before hostile reaction deadlines breach ($\exists \pi : C_j^\pi \le D_j \, \forall j$). A target may be visible, yet the encounter remains a lethal failure because a concurrent threat imposes an unserviceable deadline.

### 3.5 Single-Machine Scheduling & Anticipatory Setup Semantics
In operations research, non-preemptive single-machine scheduling with release dates, sequence-dependent setup times, and due dates ($1 \mid r_j, s_{ij} \mid L_{\max}$) is well established (Tanaka, Araki, & Fujikuma, 2021). 

Crucially, scheduling theory formally distinguishes between **anticipatory** and **non-anticipatory** setup times (Morais, Bulhões, & Subramanian, 2024). If machine setup for job $j$ can occur prior to job $j$'s release time $r_j$, the setup is *anticipatory*; if setup may only commence after job $j$ has arrived, the setup is *non-anticipatory*.

*Theoretical Mapping:* This distinction directly grounds our formulation of player information states:
- **Reveal-Gated Clearance ($a_j = r_j$):** Corresponds exactly to *non-anticipatory setup*, because the reticle cannot begin target-specific slew toward an unknown threat before its visual release $r_j$.
- **Pre-Aim Clearance ($a_j = 0$):** Corresponds exactly to *anticipatory setup*, because spatial prior knowledge allows the reticle to pre-align with the target aperture before the target itself becomes visually unoccluded.
Our introduction of the actionable-information timestamp $a_j$ parameterizes these dual scheduling semantics directly from the player's information state.

### 3.6 Compositional Real-Time Interfaces
In real-time embedded systems, compositional schedulability frameworks (Shin & Lee, 2003; Easwaran et al., 2006) and timed interfaces (de Alfaro & Henzinger, 2001) abstract complex subsystem workloads behind formal timing interfaces and compose them algebraically ($I_A \otimes I_B$) to establish global guarantees without whole-system re-analysis. Real-Time Calculus (Chakraborty et al., 2003; Thiele et al., 2000) formalizes event streams and bounded resource capacities over min-plus and max-plus dioid algebras.

*Scholarly Distinction:* We instantiate compositional timing-interface principles in a previously unmodeled spatial domain: component demand is generated by continuous 2D visibility geometry, and interface state is the player's physical reticle orientation angle $\theta$.

### 3.7 Cognitive Contextual Cueing & FPS Expertise
In visual cognition, Chun and Jiang's (1998) seminal work on *contextual cueing* demonstrated that repeated spatial configurations implicitly guide visual attention toward target locations, significantly reducing search latency even when observers have no explicit conscious recognition of the layout repetition. Contemporary eye-tracking and esports performance literature (e.g., 2025/2026 FPS aiming and gaze tracking studies) confirms that experienced shooter players exhibit faster motor execution, shorter saccadic latencies, and highly optimized spatial pre-positioning.

*Cognitive Framing:* Contextual cueing provides the theoretical basis for our familiarity model: repeated exposure to level geometry advances the player's actionable-information timestamp ($a_j < r_j$), shrinking reveal-time aim error. Our framework separates general sensorimotor capability ($A, \omega_{\text{aim}}$) from environment-specific spatial knowledge ($a_j$), providing a formal basis for the **Tactical Value of Map Knowledge** ($\Delta\mathcal{M}_{\text{knowledge}}$).


---

## 4. Mathematical Theory of Tactical Clearability

### 4.1 World Primitives and Persistent Threat Regions
Let level geometry be defined as a pair $M = (F, O)$, where $F \subset \mathbb{R}^2$ represents walkable floor space and $O \subset \mathbb{R}^2$ represents opaque, bullet-blocking obstacles.

We define a finite set of **persistent world-space threat regions**:
$$\mathcal{T} = \{ T_1, T_2, \dots, T_n \}$$
where each $T_j \subset F$ is a convex geometric region representing an authored or tactical hostile firing position (doorway threshold, window frame, head-glitch crate, sniper ledge) with a canonical firing anchor $q_j \in T_j$.

### 4.2 Traversal Kinematics & Line-of-Sight Exposure
A traversal route is defined as a parameterised polyline trajectory $\gamma: [0, S] \to F$ traversed at nominal forward velocity $v_{\text{move}} = 4.5\,\text{m/s}$, yielding player position $p(t) = \gamma(v_{\text{move}} \cdot t)$.

Line-of-sight between player position $p(t)$ and threat anchor $q_j$ is given by:
$$\text{LOS}(p(t), q_j) = 1 \iff [p(t), q_j] \cap O = \emptyset$$

The **unocclusion timestamp** (release time) $r_j$ is the earliest time the threat achieves line of sight:
$$r_j = \inf \{ t \ge 0 : \text{LOS}(p(t), q_j) = 1 \}$$

Each threat is associated with an authored response due window $n_j$, yielding an absolute survival deadline:
$$D_j = r_j + n_j$$

### 4.3 Single-Reticle Sequence-Dependent Setup Costs
The player is equipped with a single focal crosshair oriented at angle $\theta(t) \in [-\pi, \pi)$. Let target $j$'s relative aim bearing at unocclusion be $\theta_j = \text{atan2}(q_j.y - p(r_j).y, \, q_j.x - p(r_j).x)$.

Rotating the reticle from threat $i$ (at bearing $\theta_i$) to threat $j$ (at bearing $\theta_j$) incurs an angular slew duration:
$$q_{i, j} = \frac{\Delta\theta(\theta_i, \theta_j)}{\omega_{\text{aim}}}$$
where $\Delta\theta(\theta_i, \theta_j) = \min(|\theta_i - \theta_j|, 360^\circ - |\theta_i - \theta_j|)$ and $\omega_{\text{aim}} = 360^\circ/\text{s}$ is the nominal reticle slew velocity.

Once aligned within aim tolerance, servicing threat $j$ requires perceptual acquisition latency $A = 0.15\,\text{s}$ and inspection/fire dwell $p_j = 0.10\,\text{s}$.

### 4.4 Unified Epistemic Information Recurrence
To capture the role of map familiarity, we introduce the **actionable-information timestamp** $a_j$: the earliest time at which threat $j$'s location and bearing become known to the player.

Under a service ordering permutation $\pi = (\pi_1, \pi_2, \dots, \pi_N)$, completion timestamps $C_{\pi_k}$ are governed by the unified recurrence:
$$C_{\pi_k} = \max\Big(r_{\pi_k}, \, \max(C_{\pi_{k-1}}, a_{\pi_k}) + q_{\pi_{k-1}, \pi_k}\Big) + A + p_{\pi_k}$$

This recurrence unifies two fundamental information regimes:

1. **Reveal-Gated Information Regime ($a_j = r_j$, Non-Anticipatory Setup):**
   Unfamiliar / blind clearance. The player has no prior knowledge of threat locations. Reticle rotation toward target $\pi_k$ cannot begin until after visual unocclusion $r_{\pi_k}$:
   $$C_{\pi_k}^{\text{reveal}} = \max(C_{\pi_{k-1}}, r_{\pi_k}) + q_{\pi_{k-1}, \pi_k} + A + p_{\pi_k}$$

2. **Pre-Aim Information Regime ($a_j = 0$, Anticipatory Setup):**
   Maximal-information / full-from-entry target-direction bound. Reticle rotation toward target $\pi_k$ can begin during pre-reveal traversal, but perceptual acquisition and weapon engagement remain release-gated at $r_{\pi_k}$:
   $$C_{\pi_k}^{\text{preaim}} = \max\Big(r_{\pi_k}, \, C_{\pi_{k-1}} + q_{\pi_{k-1}, \pi_k}\Big) + A + p_{\pi_k}$$

### 4.5 Optimal Lateness, Tactical Margin, and Tactical Knowledge Advantage
The **Optimal Maximum Lateness** $L^*(\gamma)$ is the minimum lateness achieved across all valid clearing permutations:
$$L^*(\gamma) = \min_{\pi \in \Pi} \max_{j=1..N} \Big( C_j(\pi) - D_j \Big)$$

The **Tactical Margin** $\mathcal{M}(\gamma)$ is the signed temporal buffer before deadline breach:
$$\mathcal{M}(\gamma) = -L^*(\gamma)$$
- $\mathcal{M} \ge 0$: Feasible encounter. An optimal controller clears all threats before hostile deadline expiration.
- $\mathcal{M} < 0$: Infeasible encounter (lethal trap). At least one threat breaches its deadline before weapon service completes.

The **Tactical Value of Map Knowledge** ($\Delta\mathcal{M}_{\text{knowledge}}$) quantifies the exact tactical buffer gained by pre-aiming:
$$\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}} = L^*_{\text{reveal}} - L^*_{\text{preaim}} \ge 0$$

### 4.6 Critical Uniform Actionability Lead ($\ell^*_{\text{uniform}}$) & Monotonicity

To model intermediate degrees of spatial warning between complete blind reveal ($a_j = r_j$) and omniscient pre-aim knowledge ($a_j = 0$), we parameterize target actionability by a uniform advance-information lead time $\ell \ge 0$:
$$a_j(\ell) = \max(0, \, r_j - \ell)$$

Under this parameterization, reticle setup toward target $j$ is permitted to begin at timestamp $a_j(\ell)$, pre-aligning the crosshair toward the aperture bearing that threat $j$ will occupy upon visual unocclusion $r_j$.

#### Proposition 1 (Monotonic Actionability)
*Let $\gamma$ be a fixed traversal trajectory, $\mathcal{T}$ a set of persistent threat regions, and $\ell \ge 0$ a uniform advance actionability lead. For any $\ell_2 \ge \ell_1 \ge 0$, the optimal tactical margin satisfies:*
$$\mathcal{M}(\ell_2) \ge \mathcal{M}(\ell_1) \quad (	ext{equivalently, } L^*(\ell_2) \le L^*(\ell_1))$$

*Proof:* For any threat $j$, $\ell_2 \ge \ell_1 \implies a_j(\ell_2) = \max(0, r_j - \ell_2) \le \max(0, r_j - \ell_1) = a_j(\ell_1)$. For any fixed clearing permutation $\pi = (\pi_1, \dots, \pi_N)$, mathematical induction over completion timestamps $C_{\pi_k}$ in the unified recurrence yields:
$$C_{\pi_k}(\ell_2) \le C_{\pi_k}(\ell_1) \quad orall k \in \{1, \dots, N\}$$
Consequently, maximum lateness under permutation $\pi$ satisfies:
$$L^\pi(\ell_2) = \max_k (C_{\pi_k}(\ell_2) - D_{\pi_k}) \le \max_k (C_{\pi_k}(\ell_1) - D_{\pi_k}) = L^\pi(\ell_1)$$
Minimizing over all permutations $\pi \in \Pi$ preserves the inequality:
$$L^*(\ell_2) = \min_{\pi \in \Pi} L^\pi(\ell_2) \le \min_{\pi \in \Pi} L^\pi(\ell_1) = L^*(\ell_1)$$
and therefore $\mathcal{M}(\ell_2) = -L^*(\ell_2) \ge -L^*(\ell_1) = \mathcal{M}(\ell_1)$. $lacksquare$

*Implementation Verification:* Evaluated across all 72 experimental instances (12 pilot stimuli + 60 benchmark arenas), $\mathcal{M}(\ell)$ is verified to be monotone non-decreasing across all step intervals.

#### Epistemic Tripartite Taxonomy
Monotonicity partitions encounters into three canonical epistemic classes:
1. **Blind-Clearable ($\mathcal{M}(0) \ge 0$, $\ell^*_{\text{tic}} = 0$):** Clearable on first sight with zero advance knowledge.
2. **Knowledge-Rescuable ($\mathcal{M}(0) < 0 \land \mathcal{M}(\infty) \ge 0$, $0 < \ell^*_{\text{tic}} < \infty$):** A lethal trap on first encounter, but rendered tactically clearable with advance directional actionability $\ge \ell^*$.
3. **Structurally Overloaded under the Declared Player Model ($\mathcal{M}(\infty) < 0$, $\ell^*_{\text{tic}} = +\infty$):** Structurally infeasible even under maximal pre-aim under the declared traversal model.

#### Decoupling $\Delta\mathcal{M}_{\text{knowledge}}$ and $\ell^*$
The Critical Uniform Actionability Lead $\ell^*_{\text{uniform}} = \inf \{ \ell \ge 0 : \mathcal{M}(\ell) \ge 0 \}$ is not a redundant re-parameterization of $\Delta\mathcal{M}_{\text{knowledge}}$:
- $\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$ measures *total capacity gain* under omniscient pre-aiming.
- $\ell^*_{\text{uniform}}$ measures *temporal urgency* (how early directional information must arrive to prevent deadline failure).

*Disagreement Pair:* `STIM_07` and `STIM_11` share identical knowledge advantage $\Delta\mathcal{M}_{\text{knowledge}} = +7\,\text{tics}$ ($+200.0\,\text{ms}$). However, `STIM_07` crosses the feasibility threshold at $\ell^* = 4\,\text{tics}$ ($114.3\,\text{ms}$), whereas `STIM_11` requires $\ell^* = 6\,\text{tics}$ ($171.4\,\text{ms}$) — 50% more advance actionability than STIM_07 despite identical full-knowledge benefit (+7 tics).

---

## 5. The Collapse of Simplified Abstractions: A Constructive Progression

To demonstrate why state-conditioned transfer contracts are mathematically necessary, we trace the failure of four simpler candidate abstractions through constructive counterexamples:

```text
[Progression of Candidate Abstractions]

Peak Static Concurrency K_static  ──> Fails: Discards release timing and reticle travel
                │
                ▼
Scalar Arrival Curves α+(Δ)        ──> Fails: Discards reticle orientation memory
                │
                ▼
State-Conditioned DBFs             ──> Fails: Inf-sup non-distributivity in (R, max, +)
                │
                ▼
State-Conditioned Transfer Maps    ──> EXACT: Closed, associative, and sound under (min, +)
```

### 5.1 Failure 1: Peak Static Concurrency ($K_{\text{static}}$)
- **Candidate:** Abstract clearance difficulty by peak simultaneous line-of-sight count $K_{\text{static}} = \max_{p \in \gamma} |\mathcal{T}_{\text{vis}}(p)|$.
- **Counterexample (Disagreement Pair):**
  - *Arena 1 (Blind Spot Trap):* Two threats revealed at identical timestamps ($r_1 = r_2 = 0.5\,\text{s}$) at wide separation ($\Delta\theta = 150^\circ$) with tight deadlines ($n=0.35\,\text{s}$). Static concurrency is low ($K_{\text{static}} = 2 \le 2$), but sequential aim slew ($q = 0.42\,\text{s}$) causes lethal deadline breach ($L^* = +1\,\text{tic}$).
  - *Arena 2 (False Alarm Solvable):* Three threats revealed with generous staggered timing ($r_1=0.0\text{s}, r_2=0.8\text{s}, r_3=1.6\text{s}$). Peak static concurrency is high ($K_{\text{static}} = 3 > 2$), but deadlines are completely relaxed ($L^* = -23\,\text{tics}$, survives 100%).
- **Lost Information:** $K_{\text{static}}$ discards release timestamps $r_j$, deadline slacks $n_j$, and reticle slew distances $q_{ij}$.

### 5.2 Failure 2: Scalar Arrival Curves ($\alpha^+(\Delta)$)
- **Candidate:** Real-Time Calculus upper arrival curves counting maximum threat arrivals in any window $\Delta$: $\alpha^+(\Delta) = \sup_t N[t, t+\Delta]$.
- **Counterexample (Alternating Reticle Thrashing):**
  - Two encounters share identical scalar arrival curves $\alpha^+(\Delta)$ (3 threats arriving at $t = 0.0\text{s}, 0.3\text{s}, 0.6\text{s}$).
  - *Encounter A (Monotonic Arc):* Bearings sweep smoothly ($0^\circ \to 30^\circ \to 60^\circ$, total slew $= 60^\circ$). Feasible ($L^* \le 0$).
  - *Encounter B (Alternating Zigzag):* Bearings thrash across flanks ($-60^\circ \to +60^\circ \to -60^\circ$, total slew $= 240^\circ$). Infeasible ($L^* > 0$).
- **Lost Information:** Scalar curves discard spatial reticle orientation state $\theta$.

### 5.3 Failure 3: State-Conditioned Demand Bound Functions (DBFs)
- **Candidate:** Abstracting angular sectors into demand bound matrices $D(\Delta) \in \mathbb{R}^{K \times K}$ composed via inf-sup convolution.
- **Counterexample (Inf-Sup Non-Distributivity):**
  In the max-plus algebra $(\mathbb{R} \cup \{-\infty\}, \max, +)$, the infimum operator does not distribute over supremum:
  $$\inf_{u} \sup_{v} (f(u) + g(v)) \ne \sup_{v} \inf_{u} (f(u) + g(v))$$
  Associativity violates across 3-module chains ($D_1 \otimes (D_2 \otimes D_3) \ne (D_1 \otimes D_2) \otimes D_3$), causing false rejections.

### 5.4 The Exact Abstraction: State-Conditioned Spatial Transfer Maps
By shifting from workload bounds to **exact entry-to-exit traversal durations**, the transfer map $C_M[(p_{\text{in}}, a), (p_{\text{out}}, b)]$ maps entry port and sector $(p_{\text{in}}, a)$ to exit port and sector $(p_{\text{out}}, b)$. Composition reduces to standard matrix multiplication over the min-plus dioid $(\mathbb{R}_{\ge 0} \cup \{+\infty\}, \min, +)$, restoring exact algebraic associativity.

---

## 6. Exact Composable Spatial Transfer Contracts

### 6.1 Min-Plus Matrix Composition
Let an authored module $M$ define boundary ports $P_M$ and angular sectors $\{0, 1, \dots, K-1\}$. The transfer contract is represented as a matrix $C_M \in (\mathbb{R}_{\ge 0} \cup \{+\infty\})^{(|P_M| \cdot K) \times (|P_M| \cdot K)}$.

For two sequentially connected modules $M_1$ and $M_2$ joined at intermediate port $p_{\text{mid}}$, the composed transfer duration is given by the $(\min, +)$ product:
$$C_{M_1 \otimes M_2}[(p_{\text{in}}, a), (p_{\text{out}}, b)] = \min_{k \in \{0..K-1\}} \Big( C_{M_1}[(p_{\text{in}}, a), (p_{\text{mid}}, k)] + C_{M_2}[(p_{\text{mid}}, k), (p_{\text{out}}, b)] \Big)$$

### 6.2 Algebraic Associativity & Discretization Convergence ($K=8$)
- **Associativity Theorem:** Min-plus matrix multiplication over the dioid $(\mathbb{R} \cup \{+\infty\}, \min, +)$ is strictly associative:
  $$(C_{M_1} \otimes C_{M_2}) \otimes C_{M_3} \equiv C_{M_1} \otimes (C_{M_2} \otimes C_{M_3})$$
- **Production Angular Discretization ($K=8$):** Canonical angular resolution is established at $K=8$ ($45^\circ$ dyadic sectors). In exhaustive library audits against a continuous-angle reference oracle ($K=\infty$, 5,824 evaluations), $K=8$ completely eliminates dyadic conservatism artifacts, achieving **0 false rejections and 0 false acceptances** across the entire 16-module library.

### 6.3 Quiescent Boundary Ports & The $C \equiv D$ Local Equivalence Theorem
A boundary port $p$ is **quiescent** if its reset zone $Q_p$ is completely shielded from all hostile threat lines of sight:
$$\text{Quiescent}(Q_p) \iff \forall T_j \in \mathcal{T}: \text{dist}\Big(Q_p, \, V(T_j.q_j)\Big) \ge \epsilon_{\text{reset}}$$
where $\epsilon_{\text{reset}} = 0.05\,\text{m}$ is the safety clearance margin.

- **$C \equiv D$ Local Equivalence Theorem:** If all connecting ports between modules are certified quiescent, global assembly schedulability (Audit C) is mathematically equivalent to independent local module schedulability (Audit D):
  $$\text{GlobalSchedulable}(M_1 \circ M_2 \circ \dots \circ M_n) \iff \bigwedge_{i=1}^n \text{LocalSchedulable}(M_i)$$
  This theorem enables zero-overhead compile-time level linting.

---

## 7. Geometry-to-Contract Compilation Engine

The Geometry-to-Contract Compiler ($\mathcal{G} \to \mathcal{C}$) automatically compiles 2D floorplan polygons, obstacle contours, and authored threat regions into certified transfer matrices.

```text
[Geometry-to-Contract Compilation Engine Pipeline]

Raw 2D Level Polygons (Boundary, Obstacles, Threats, Routes)
                        │
                        ▼
Critical-LOS Ray-Vertex Event Candidate Generator (Sub-millimeter Slit Detection)
                        │
                        ▼
Dual-Oracle Adaptive Bisection (< 0.1 ms Precision against Dense March Oracle)
                        │
                        ▼
Exact Angular Slew & Setup Matrix Compiler (K = 8 Dyadic Sectors)
                        │
                        ▼
Certified Transfer Map C_M in R_>=0 U {+inf} (Reveal-Gated & Pre-Aim Caches)
```

### 7.1 Critical-LOS Ray-Vertex Event Dual-Oracle Engine
1. **Candidate Raycast Intersection:** Computes exact intersections between rays $(q_j, v_k)$ (from threat anchors through obstacle vertices) and route polyline segments. This guarantees detection of narrow flash slits down to $0.5\,\text{mm}$ regardless of spatial grid alignment.
2. **Dual-Oracle Adaptive Bisection:** Candidate intervals are bisected to sub-millimeter precision, achieving $<0.1\,\text{ms}$ discrepancy against a localized $100\,\mu\text{m}$ reference marching oracle.

### 7.2 Adversarial Geometric Fixture Suite
The compiler was validated against ten adversarial geometric benchmarks:
- **F01 Analytical Corner:** Reaches exact agreement with analytical line-of-sight grazing ray ($s_{\text{reveal}} = 3.250\,\text{m}$, bearing $\theta = 63.435^\circ$).
- **F02B Three-Angle Sector Sweep:** Verifies true multi-directional angular switching ($\theta_1 \approx +63.5^\circ, \theta_2 \approx 0^\circ, \theta_3 \approx -63.5^\circ$).
- **F06 Wall Perturbation Sweep:** Captures monotonic reveal translation and sharp $L^*=0$ threshold crossing ($x_{\text{wall}} \approx 0.85\,\text{m}$).
- **F07 Adversarial Slit Flash Fuzzing:** Detects narrow flash apertures from $0.5\,\text{mm}$ to $80.0\,\text{mm}$ across multiple phase offsets with zero missed unocclusions.

---

## 8. Procedural Generation & Combinatorial Amplification

### 8.1 Condition-Blind 25,000-Candidate Corpus Sweeps
We evaluated 25,000 randomly assembled 6-module levels drawn from Library 1 (authored baseline) and Library 2 (held-out generalization suite):

| Evaluation Metric | Library 1 (25k Assemblies) | Library 2 Held-Out (25k Assemblies) | Operational Interpretation |
| :--- | :---: | :---: | :--- |
| **Audit A (Graph Topology Valid)** | 25,000 (100.0%) | 25,000 (100.0%) | Valid connectivity and socket alignment. |
| **Audit B (Static $K_{\text{static}} \le 2$)** | 11,296 (45.18%) | 11,191 (44.76%) | Admitted by static concurrency heuristic. |
| **Audit C (Composed Transfer Map)** | 7,333 (29.33%) | 7,119 (28.48%) | Certified deadline-feasible under reticle slew. |
| **Audit D (Local-Only Transfer)** | 7,333 (29.33%) | 7,119 (28.48%) | Locally feasible across constituent modules. |
| **$A \cap B \cap \neg C$ ($K_{\text{static}}$ Blind Spot)** | **6,704 (26.82%)** | **6,789 (27.16%)** | **False Positive:** Accepted by $K_{\text{static}} \le 2$, but model-infeasible ($L^* > 0$). |
| **$A \cap \neg B \cap C$ ($K_{\text{static}}$ False Alarm)** | **2,741 (10.96%)** | **2,717 (10.87%)** | **False Alarm:** Rejected by $K_{\text{static}} > 2$, but solvably staggered. |
| **$C \equiv D$ Concordance** | **100.00% (0 diff)** | **100.00% (0 diff)** | Global feasibility decomposes locally under quiescence. |

**Combinatorial Amplification:** Local 4-class module contingency tables ($12: B \land C, 2: B \land \neg C, 1: \neg B \land C, 1: \neg B \land \neg C$) amplify into the observed macro-population error rates:
$$P(B \cap \neg C) = \left(\frac{14}{16}\right)^6 - \left(\frac{12}{16}\right)^6 \approx 27.08\% \quad (\text{Observed: } 27.16\%)$$

### 8.2 Integer Threshold Sweep ROC Analysis
Evaluating integer thresholds $K \in \{1, 2, 3, 4, 5\}$ over the 25,000 assemblies confirms that no static threshold achieves zero false positives and zero false alarms simultaneously:

| Threshold | True Positives | False Positives | False Negatives | True Negatives | Precision | Recall | Balanced Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$K_{\text{static}} \le 1$** | 816 | 1,799 | 6,517 | 15,868 | 31.2% | 11.1% | 50.5% |
| **$K_{\text{static}} \le 2$** | 4,592 | 6,704 | 2,741 | 10,963 | 40.7% | 62.6% | 62.3% |
| **$K_{\text{static}} \le 3$** | 7,333 | 17,667 | 0 | 0 | 29.3% | 100.0% | 50.0% |

### 8.3 Industrial Architecture: Precertified Library Linter (Condition E)
By virtue of the $C \equiv D$ theorem under quiescent reset pockets, local certification eliminates runtime transfer matrix evaluation during level generation:
- **Compile-Time Linter:** Filters the 16-module library down to the 13 locally feasible modules.
- **Runtime Generation:** 5,000 / 5,000 (100.0%) generated assemblies achieved certified deadline feasibility with lightweight structural auditing, bypassing 100% of runtime transfer matrix calculations.

### 8.4 Replicated Paired-Seed MAP-Elites ($N=30$ Paired Runs)
Running 30 paired-seed evolutionary searches (3,000 evaluations each) over the 2D behavioral space ($\text{Pace Proxy} \in [4\text{s}, 16\text{s}] \times \text{Route Redundancy} \in [0, 6]$):
- **Condition C vs. Condition A:** $\Delta\text{Coverage} = -0.19\%$ (95% CI: $[-1.25\%, +0.87\%]$). Because the lower bound exceeds $-\delta = -2.0\%$, **Condition C non-inferiority is confirmed**, demonstrating that hard tactical clearability constraints do not collapse behavioral archive diversity.
- **Condition E vs. Condition A:** $\Delta\text{Coverage} = +2.38\%$ (95% CI: $[+1.46\%, +3.30\%]$), confirming statistically significant superiority over unconstrained topology search.


---

## 9. Discrete 35 Hz Simulation Benchmark (Round 11S)

To evaluate construct validity and baseline discrimination without confounding external game engine artifacts, Round 11S executes a discrete-time stochastic simulation benchmark on Doom's native 35 Hz logic clock ($\Delta t = 1/35\,\text{s} = 28.5714\,\text{ms}$).

### 9.1 Population Benchmark Scope & Methodology
- **Suite:** 60 parameterized micro-arenas spanning 6 distinct geometric mechanisms (10 parameter settings per family):
  1. *Staggered Wall Baffles:* Reveal interval $r_2 - r_1$ via wall position $x \in [0.2\,\text{m}, 2.0\,\text{m}]$.
  2. *Angular Crossfire Separation:* Reticle setup travel cost $\Delta\theta \in [30^\circ, 160^\circ]$.
  3. *Aperture Burst Congestion:* Simultaneous arrival density / slit stagger $\Delta x \in [0.0\,\text{m}, 1.5\,\text{m}]$.
  4. *3-Threat Alternating Corridor:* Sequence-dependent reticle zigzagging overhead (spacing $\in [0.3\,\text{m}, 2.2\,\text{m}]$).
  5. *Deadline Compression:* Hostile reaction delay & TTK urgency ($D \in [0.40\,\text{s}, 1.10\,\text{s}]$).
  6. *Flank Sweep Smoothness:* Monotonic pie-slice vs jagged alternating angular clearing paths ($\theta_{\text{scale}} \in [20^\circ, 75^\circ]$).
- **Execution & Paired Common-Random-Number Design:** 60 arenas $\times$ 5 independent simulation controllers $\times$ 30 stochastic noise trials ($\sigma_{\text{acq}} = 0.02\,\text{s}, \sigma_\omega = 30^\circ/\text{s}$) = **9,000 discrete simulation episodes**. The 30 noise realizations are applied as a deterministic common-random-number design across conditions, isolating pure geometric differences by holding perceptual and motor perturbations constant across arena/controller pairs.
- **Non-Oracle Target Construction:** The primary classification label is defined strictly as the **mean survival rate across the four non-Oracle heuristic controllers** (`FIFO`, `Nearest Angle`, `EDF`, `Left-to-Right`) across 7,200 episodes. The integer-tic sequence-optimal `Oracle` controller is evaluated across 1,800 episodes solely as an un-confounded upper-bound reference.
- **Cross-Validation:** Leave-One-Geometry-Family-Out (LOGFO-CV) partitioning across the 6 structural mechanism families.

### 9.2 Canonical Benchmark Results

```text
[Round 11S Frozen Population Benchmark Results (Git Commit cb9cf7d)]

Predictor                     LOGFO ROC-AUC    Spearman rho    LOGFO Brier Score
────────────────────────────────────────────────────────────────────────────────
Tactical Margin M_tic           1.0000           +0.9282            0.0949
Peak Physical LOS K_static      0.8098           +0.5635            0.1568  (ΔAUC: +19.02%)
Hamiltonian Workload B_work     0.8260           +0.6650            0.1714  (ΔAUC: +17.40%)
Minimum Slack sigma_min         0.5742           -0.1960            0.2640  (ΔAUC: +42.58%)
```

| Difficulty Predictor | Spearman Rank ($\rho$) | In-Sample ROC-AUC | In-Sample Brier Score | LOGFO-CV ROC-AUC | LOGFO-CV Brier Score | $\Delta \text{LOGFO-AUC}$ Superiority |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tactical Margin ($\mathcal{M}_{\text{tic}}$)** | $\mathbf{+0.9282}$ | $\mathbf{0.9988}$ | $\mathbf{0.0912}$ | $\mathbf{1.0000}$ | $\mathbf{0.0949}$ | **Reference** |
| **Peak Physical LOS $K_{\text{static}}$ (Inverted)** | $+0.5635$ | $0.8493$ | $0.1524$ | $0.8098$ | $0.1568$ | $\mathbf{+0.1902}$ (+19.02%) |
| **Hamiltonian Workload $\mathcal{B}_{\text{work}}^{\text{Ham}}$ (Inverted)** | $+0.6650$ | $0.8684$ | $0.1585$ | $0.8260$ | $0.1714$ | $\mathbf{+0.1740}$ (+17.40%) |
| **Minimum Slack $\sigma_{\text{min}}$** | $-0.1960$ | $0.3260$ | $0.2178$ | $0.5742$ | $0.2640$ | $\mathbf{+0.4258}$ (+42.58%) |

### 9.3 Key Empirical Findings
1. **Model-Scoped Construct Validity ($\text{LOGFO-AUC} = 1.0000, \rho = +0.9282$):**
   Across the 6 controlled geometric mechanism families, Tactical Margin acts as a sufficient statistic for non-Oracle clearing performance under execution noise, generalizing across held-out geometric families without structural degradation.
2. **Substantial Baseline Superiority:**
   - Outperforms peak physical line-of-sight concurrency ($K_{\text{static}}$) by **+19.02% AUC** ($1.0000$ vs. $0.8098$).
   - Outperforms cumulative Hamiltonian workload ($\mathcal{B}_{\text{work}}^{\text{Ham}}$) by **+17.40% AUC** ($1.0000$ vs. $0.8260$). This confirms that even after accounting for total service burden and minimum angular travel, arrival release timing and sequencing order remain critical.
   - Outperforms static minimum slack ($\sigma_{\text{min}}$) by **+42.58% AUC** ($1.0000$ vs. $0.5742$).
3. **High Probability Calibration Accuracy:**
   Tactical margin reduces probability calibration error by $>39\%$ compared to spatial baselines ($\text{Brier} = 0.0949$ vs. $0.1568$).

---

## 10. External Game Engine Residual Validation (Native ViZDoom)

To cross the external process boundary into an authoritative 3D game engine, we evaluate the framework inside real headless C++ ViZDoom (`vzd.DoomGame`).

### 10.1 Quantized WAD Export & Engine-Authoritative Arbitration
- **Binary WAD Generator:** Compiles continuous geometry into integer Doom units ($64\,\text{units/m}$). Line-of-sight is evaluated strictly against the quantized WAD linedefs and measured player position `POSITION_X/Y`.
- **Engine-Authoritative Death:** Deadline breaches issue `kill` directly in Doom. Episode outcome is evaluated strictly from `is_player_dead()` and engine `HEALTH <= 0` with zero Python boolean fallback.

### 10.2 Three-Layer Lateness Residual Decomposition
We formalize three distinct lateness quantities:
1. $L^*_{\text{predicted}}$: Optimal schedule computed offline from continuous geometry.
2. $L^*_{\text{engine-conditioned}}$: Optimal schedule recomputed from quantized WAD geometry and engine player locomotion $(R_j^{\text{engine}}, \theta_j^{\text{engine}})$.
3. $L_{\text{realized}} = \max_j (C_j^{\text{engine}} - D_j^{\text{engine}})$: Realized controller service completion lateness.

The total error decomposes into export and execution residuals:
$$\Delta^L_{\text{export}} = L^*_{\text{engine-conditioned}} - L^*_{\text{predicted}}$$
$$\Delta^L_{\text{execution}} = L_{\text{realized}} - L^*_{\text{engine-conditioned}}$$
$$\Delta^L_{\text{total}} = L_{\text{realized}} - L^*_{\text{predicted}} = \Delta^L_{\text{export}} + \Delta^L_{\text{execution}}$$

### 10.3 Observed Residual Metrics & Deployment Guard Band ($\epsilon_{\text{deploy}}$)
Across 12 native Doom micro-arenas:
- $\max |\Delta^L_{\text{export}}| = 3\,\text{tics}$ ($85.7\,\text{ms}$)
- $\max |\Delta^L_{\text{execution}}| = 1\,\text{tic}$ ($28.5\,\text{ms}$)
- $\text{Mean } |\Delta^L_{\text{total}}| = 0.83\,\text{tics}$ ($23.7\,\text{ms}$)
- **Deployment Reserve ($\epsilon_{\text{deploy}} = 3\,\text{tics}$):** In the 12-arena validation suite, setting an empirical engineering guard band of $\epsilon_{\text{deploy}} = 3\,\text{tics}$ ($85.7\,\text{ms}$) verified that all arenas with predicted margin $\mathcal{M}_{\text{pred}} \ge 3\,\text{tics}$ survive native engine execution with **100% survival**.

### 10.4 Engine-Level Epistemic Separation
In native ViZDoom execution of `F3_BurstCongestion_02`:
- **Reveal-Gated Controller ($a_1 = r_1$):** $L^* = +4\,\text{tics}$ ($\mathcal{M} = -4\,\text{tics}$) $\implies$ Player dies at Tic 70.
- **Pre-Aim Controller ($a_1 = 0$):** $L^* = -2\,\text{tics}$ ($\mathcal{M} = +2\,\text{tics}$) $\implies$ Player clears at Tic 67, surviving natively.
This confirms that both information regimes represent valid, observable behavioral bounds in a live game engine.

### 10.5 Critical Actionability Lead in External Engine Execution
To evaluate whether the theoretical actionability threshold $\ell^*_{\text{source}}$ governs native external game engine execution, we performed a full integer-lead sweep ($\ell \in [0, 9]\,\text{tics}$) across all four selected knowledge-rescuable mechanism fixtures (`STIM_06`, `STIM_07`, `STIM_09`, `STIM_11`) inside headless C++ ViZDoom (4 fixtures $\times$ 10 parameter points = 40 deterministic engine executions).

We evaluate the three-stage threshold decomposition:
$$\ell^*_{\text{source}} \longrightarrow \ell^*_{\text{engine-model}} \longrightarrow \ell^*_{\text{survival}}$$
where $\ell^*_{\text{source}} = \min \{ \ell : \mathcal{M}_{\text{pred}}(\ell) \ge 0 \}$, $\ell^*_{\text{engine-model}} = \min \{ \ell : \mathcal{M}_{\text{eng}}(\ell) \ge 0 \}$, and $\ell^*_{\text{survival}} = \min \{ \ell : \text{ViZDoom player survives} \}$.

| Fixture ID | Source Threshold $\ell^*_{\text{source}}$ | Engine-Model Threshold $\ell^*_{\text{engine-model}}$ | Observed Survival $\ell^*_{\text{survival}}$ | Net Discrepancy $(\ell^*_{\text{survival}} - \ell^*_{\text{source}})$ |
| :--- | :---: | :---: | :---: | :---: |
| **STIM_06 (Double Baffle)** | $5\,\text{tics}$ ($142.9\,\text{ms}$) | $4\,\text{tics}$ ($114.3\,\text{ms}$) | **$4\,\text{tics}$ ($114.3\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |
| **STIM_07 (Spaced Baffle)** | $4\,\text{tics}$ ($114.3\,\text{ms}$) | $3\,\text{tics}$ ($85.7\,\text{ms}$) | **$3\,\text{tics}$ ($85.7\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |
| **STIM_09 (Aperture Burst)** | $4\,\text{tics}$ ($114.3\,\text{ms}$) | $3\,\text{tics}$ ($85.7\,\text{ms}$) | **$5\,\text{tics}$ ($142.9\,\text{ms}$)** | $+1\,\text{tic}$ ($+28.6\,\text{ms}$) |
| **STIM_11 (Zigzag Flank)** | $6\,\text{tics}$ ($171.4\,\text{ms}$) | $4\,\text{tics}$ ($114.3\,\text{ms}$) | **$5\,\text{tics}$ ($142.9\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |

Across all four selected knowledge-rescuable fixtures (4/4), the observed survival threshold $\ell^*_{\text{survival}}$ tracks the theoretical source prediction $\ell^*_{\text{source}}$ within $|\Delta \ell^*| \le 1\,\text{tic}$ ($28.6\,\text{ms}$), consistent with the previously observed small export/execution residual regime.

---

## 11. Inverse Tactical Repair & Automated Level Linter

Rather than treating Tactical Margin solely as an evaluative pass/fail metric, the scheduling formulation directly enables **constructive, gradient-directed level repair**.

### 11.1 Problem Formulation & Declared Operator Set
Given an unserviceable authored or generated geometry $G$ with initial margin $\mathcal{M}(G) < 0$, the inverse repair objective finds a grid-minimal perturbed geometry $G^*$ over a declared translation operator set $\mathcal{T}_{\text{obs}}$:
$$G^* = \arg\min_{G' \in \mathcal{T}_{\text{obs}}(G)} d(G, G') \quad \text{subject to} \quad \mathcal{M}_{\text{source}}(G') \ge \epsilon_{\text{target}}, \quad \text{ValidPreservation}(G, G')$$
where $d(G, G')$ measures minimal Euclidean obstacle displacement and $\epsilon_{\text{target}} \ge +2\,\text{tics}$ ($+57.1\,\text{ms}$) is the target margin reserve.

The declared operator set evaluates rigid obstacle translations:
$$\mathcal{T}_{\text{obs}}(G) = \left\{ G' = \text{translate}(O_i, d \cdot \hat{u}) \;\middle|\; O_i \in \text{Obstacles}(G), \; \hat{u} \in \mathcal{U}, \; d \in [\delta, d_{\max}] \right\}$$
where $\mathcal{U} = \{ \hat{n}, -\hat{n}, (+1, 0), (-1, 0), (0, +1), (0, -1) \}$, grid resolution $\delta = 0.05\,\text{m}$, and $d_{\max} = 1.80\,\text{m}$.

The diagnostic analyzer evaluates the scheduling bottleneck:
1. **Critical Threat Attribution:** Identifies threat $T_{\text{crit}}$ causing the maximum lateness breach $L^* = C_{\text{crit}} - D_{\text{crit}}$.
2. **Controlling Occluder Edge:** Isolates the active obstacle boundary segment $e^* = (\vec{v}_1, \vec{v}_2)$ whose vertex collinear raycast governs the critical first-reveal timestamp $r_{\text{crit}}$.
3. **Directed Multi-Axis Grid Search:** Evaluates directional translations along normal and cardinal axes, pruning searches when $d \ge d^*_{\text{current}}$.
4. **Strict Geometric Preservation:** Enforces invariant room boundaries, obstacle count/area conservation, obstacle containment, obstacle-threat non-clipping, and route non-clipping.

### 11.2 Audited Population Benchmark Results (N=50 Unserviceable Arenas)
We evaluated the audited repair pipeline across $N=50$ genuinely unserviceable micro-arenas ($100\%$ initial $\mathcal{M} < 0$, $100\%$ baseline death in native ViZDoom) spanning 5 distinct mechanism families:

| Metric | Audited Value | Interpretation |
| :--- | :---: | :--- |
| **Audited Broken Population** | **50/50** (100.0%) | All benchmark arenas verified to satisfy initial $\mathcal{M} < 0$ |
| **Source-Model Repair Success Rate** | **80.0%** (40/50) | Offline optimizer finds grid-minimal feasible translation achieving $\mathcal{M} \ge +2\,\text{tics}$ |
| **Native ViZDoom Engine Rescue Rate** | **60.0%** (30/50) | Broken layouts flipping from fatal engine death to verified survival ($100\,\text{HP}$) |
| **Engine Transfer Efficiency** | **75.0%** (30/40) | Source-successful repairs successfully transferring to native engine survival |
| **Median Edit Distance** | **0.85\,m** (Mean: 0.89\,m) | Grid-minimal displacement within declared translation operator set $\mathcal{T}_{\text{obs}}$ |
| **Median Repair Runtime** | **292.8\,ms** (Mean: 357.2\,ms) | Multi-directional grid search across candidate obstacles |
| **Mean Export Residual ($\Delta_{\text{export}} L$)** | **+1.64 tics** | WAD quantization and coordinate discretization effect |
| **Mean Execution Residual ($\Delta_{\text{execution}} L$)** | **-0.08 tics** | Engine reticle slew dynamics and sub-tic action latency |

### 11.3 Contingency Analysis & Three-Layer Residual Decomposition
We evaluate the contingency between source-model repair certification and realized external-engine rescue:

$$\begin{array}{c|cc|c}
\text{Source Optimizer} \backslash \text{ViZDoom Engine} & \text{Engine Rescued (Survived)} & \text{Engine Fatal (Dead)} & \text{Total} \\
\hline
\text{Source Repair Success} & \mathbf{30} \text{ (60.0\%)} & \mathbf{10} \text{ (20.0\%)} & \mathbf{40} \text{ (80.0\%)} \\
\text{Source Repair Fail} & \mathbf{0} \text{ (0.0\%)} & \mathbf{10} \text{ (20.0\%)} & \mathbf{10} \text{ (20.0\%)} \\
\hline
\text{Total} & \mathbf{30} \text{ (60.0\%)} & \mathbf{20} \text{ (40.0\%)} & \mathbf{50} \text{ (100.0\%)}
\end{array}$$

| Mechanism Family | Arenas | Initial $\mathcal{M}$ | Source Success | Median Edit $d^*$ | Engine Rescue | Transfer Efficiency | Mean $\Delta_{\text{export}} L$ | Mean $\Delta_{\text{execution}} L$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Family 1: Stagger Deficit** | 10 | $-6 \dots -4\,\text{t}$ | 10/10 (100%) | 0.97 m | 10/10 (100%) | **100%** | $-0.1\,\text{t}$ | $-0.4\,\text{t}$ |
| **Family 2: Aperture Crossfire** | 10 | $-15 \dots -13\,\text{t}$ | 10/10 (100%) | 1.15 m | 8/10 (80%) | **80%** | $+0.4\,\text{t}$ | $+0.7\,\text{t}$ |
| **Family 3: Blind Spot** | 10 | $-7 \dots -2\,\text{t}$ | 0/10 (0%) | 0.00 m | 0/10 (0%) | **0%** | $+0.0\,\text{t}$ | $+0.0\,\text{t}$ |
| **Family 4: Triad Congestion** | 10 | $-12 \dots -8\,\text{t}$ | 10/10 (100%) | 0.60 m | 3/10 (30%) | **30%** | $+6.6\,\text{t}$ | $-0.1\,\text{t}$ |
| **Family 5: Flank Squeeze** | 10 | $-16 \dots -15\,\text{t}$ | 10/10 (100%) | 0.82 m | 9/10 (90%) | **90%** | $+1.3\,\text{t}$ | $-0.6\,\text{t}$ |

The residual decomposition $\Delta_{\text{total}} L = \Delta_{\text{export}} L + \Delta_{\text{execution}} L = (L^*_{\text{engine}} - L^*_{\text{source}}) + (L_{\text{realized}} - L^*_{\text{engine}})$ illuminates where the transfer boundary holds:
* For single-baffle geometries (**Family 1** and **Family 5**), $\Delta_{\text{export}} L \approx 0$ and $\Delta_{\text{execution}} L \le 0$, yielding high engine transfer efficiency ($100\%$ and $90\%$).
* For dense multi-threat clusters (**Family 4**), continuous 3D linedef raycasting in Doom unoccludes secondary angles earlier than 2D grid raycasting ($\Delta_{\text{export}} L = +6.6\,\text{tics}$), causing transfer failure unless an empirical guard band of $\epsilon_{\text{deploy}} \approx 7\,\text{tics}$ is enforced.
* Where geometry cannot be repaired within the single-obstacle translation operator budget (**Family 3**), the optimizer correctly returns failure ($0\%$ source success) with zero false-positive claims.

---

## 12. Prospective Human Cognition & The Player Capability Envelope

With computational schedulability and game engine validity established, human empirical cognition shifts from an immediate gating requirement to a structured, prospective research program.

### 12.1 The Capability Envelope
Rather than assuming fixed population constants, we define the **Player Capability Envelope** $\mathcal{C}(G)$ as the multi-dimensional region of player sensorimotor parameters under which geometry $G$ remains serviceable:
$$\mathcal{C}(G) = \left\{ (A, \omega, p, v) \in \mathbb{R}^4_{>0} \;\middle|\; \mathcal{M}_G(A, \omega, p, v) \ge 0 \right\}$$
This inverts the evaluative paradigm: instead of asking whether a map is universally playable, the compiler characterizes the critical capability boundaries:
$$\omega^* = \inf \{ \omega : \mathcal{M}(\omega) \ge 0 \}, \quad A^* = \sup \{ A : \mathcal{M}(A) \ge 0 \}$$
A room does not merely yield a scalar score; it yields actionable skill requirements (e.g., *“Requires minimum slew $\omega \ge 280^\circ/\text{s}$ or acquisition latency $A \le 140\,\text{ms}$”*).

### 12.2 Pre-Specified Empirical Hypotheses & Calibration Protocol
A standardized human pilot protocol ([`human/PILOT_PROTOCOL.md`](../human/PILOT_PROTOCOL.md)) defines pre-registered hypotheses for future empirical calibration:
1. **Hypothesis H1 (Unfamiliar Play):** In unfamiliar geometry, lower reveal-gated tactical margin $\mathcal{M}_{\text{reveal}}$ predicts lower human survival and higher realized lateness.
2. **Hypothesis H2 (Familiar Play):** With repeated exposure to the same layout, human performance converges toward the pre-aim bound $\mathcal{M}_{\text{preaim}}$.
3. **Hypothesis H3 (Continuous Learning Benefit):** The theoretical knowledge gap $\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$ predicts continuous reduction in realized lateness ($\Delta L_{\text{realized}}$) and shrinkage in reveal-time reticle aim error ($\Delta E^{\text{reveal}}$).
4. **Hypothesis H4 (Psychometric Readability vs. Fairness):** Subjective encounter fairness ratings correlate with $\mathcal{M}_{\text{reveal}}$, while tactical readability ratings correlate with $\mathcal{M}_{\text{preaim}}$.

---

## 13. Limitations & Scientific Scope Boundary

To maintain clear scientific boundaries, the scope of this work is defined by the following model limitations:
1. **Fixed Authored Traversal Route:** Clearance is evaluated along a designated 1D polyline trajectory $\gamma(s)$. Tactical stopping, dynamic backpedaling, and multi-route branch choice are modeled as discrete route selections rather than continuous real-time velocity optimization.
2. **Planar 2D Tactical Geometry:** The geometry compiler operates on 2D polygonal floorplans extruded to uniform vertical heights. Full 3D verticality (slanted ramps, multi-tier balconies) is projected to planar line of sight.
3. **Authored Persistent Threat Regions:** Hostile targets are modeled as fixed firing positions $T_j$ rather than dynamic, navigating AI agents.
4. **Single-Reticle Focal Bottleneck:** The player model assumes a single crosshair with constant maximum angular slew $\omega_{\text{aim}}$. Peripheral firing, projectile weapons, and recoil patterns are outside the scheduling model.
5. **Discrete Sensorimotor Parameterization:** Perceptual acquisition $A$ and service duration $p$ are modeled as nominal constants rather than stochastic distributions during contract compilation.
6. **Engine Validation Scale:** External engine execution is validated on benchmark suites totaling 72 micro-arenas (12 reference mechanism arenas + 50 population repair arenas) covering canonical mechanism families.
7. **Human Data Status:** Human cognitive claims are formulated as model-bounded capability envelopes and testable hypotheses (H1–H4) with a pre-specified protocol, awaiting multi-participant calibration.

---

## 14. Conclusion

The fundamental challenge of procedural generation in competitive first-person shooters is not visual fidelity or topological reachability—it is preserving the **epistemic and cognitive structure of tactical combat**.

When procedural generation ignores sequential angle clearance and reticle slew constraints, tactical skill collapses into arbitrary risk. By transforming raw level geometry into **certified tactical state transitions**, diagnosing temporal bottlenecks, and synthesizing **minimal geometric repairs verified inside native game engines**, we bridge computational geometry, scheduling theory, and competitive level design.

Procedural competitive maps do not need to be simplistic hallways or chaotic gambles. By compiling, certifying, and automatically repairing tactical clearability directly from map geometry, developers can generate dynamic, endlessly diverse shooter environments that remain deeply, reliably, and beautifully playable.

---

## 15. References & Bibliography

A machine-readable BibTeX source is maintained at [`references.bib`](references.bib).

- **Benedikt, M. L. (1979).** To take view of: isovists and isovist fields. *Environment and Planning B: Planning and Design*, 6(1), 47–65. DOI: [10.1068/b060047](https://doi.org/10.1068/b060047).
- **Cachia, J., Liapis, A., & Yannakakis, G. N. (2015).** Procedural generation of multi-layer FPS levels. *IEEE Transactions on Computational Intelligence and AI in Games*, 9(2), 178–191. DOI: [10.1109/TCIAIG.2015.2494585](https://doi.org/10.1109/TCIAIG.2015.2494585).
- **Cardamone, L., Yannakakis, G. N., Togelius, J., & Lanzi, P. L. (2011).** Evolving competitive maps for first person shooters. *Proceedings of GECCO '11*, 1395–1402. DOI: [10.1145/2001576.2001765](https://doi.org/10.1145/2001576.2001765).
- **Chakraborty, S., Künzli, S., & Thiele, L. (2003).** Real-time calculus for system-level performance analysis. *ACM SIGPLAN Notices*, 38(7), 26–35. DOI: [10.1145/780732.780737](https://doi.org/10.1145/780732.780737).
- **Chun, M. M., & Jiang, Y. (1998).** Contextual cueing: Implicit learning and retrieval of visual context facilitates visual search. *Cognitive Psychology*, 36(1), 28–71. DOI: [10.1006/cogp.1998.0681](https://doi.org/10.1006/cogp.1998.0681).
- **de Alfaro, L., & Henzinger, T. A. (2001).** Timed interfaces. *International Conference on Embedded Software (EMSOFT)*, LNCS 2211, 108–122. DOI: [10.1007/3-540-45449-7_8](https://doi.org/10.1007/3-540-45449-7_8).
- **de Donato, S., Lanzi, P. L., & Loiacono, D. (2026).** Procedural Generation of First Person Shooter Maps using MAP-Elites. *arXiv preprint arXiv:2605.30570*.
- **Dormans, J. (2010).** Adventures in level design: Generating missions and spaces for action adventure games. *Proceedings of the 2010 Workshop on Procedural Content Generation in Games (PCG)*, 1–8. DOI: [10.1145/1814256.1814257](https://doi.org/10.1145/1814256.1814257).
- **Easwaran, A., Anand, M., & Lee, I. (2006).** A compositional scheduling framework for real-time systems. *12th IEEE RTAS*, 281–292. DOI: [10.1109/RTAS.2006.27](https://doi.org/10.1109/RTAS.2006.27).
- **Guibas, L. J., Latombe, J. C., LaValle, S. M., Lin, D., & Motwani, R. (1999).** A visibility-based pursuit-evasion problem. *International Journal of Computational Geometry & Applications*, 9(04n05), 471–493. DOI: [10.1142/S021819599900029X](https://doi.org/10.1142/S021819599900029X).
- **Karth, I., & Smith, A. M. (2017).** WaveFunctionCollapse is constraint solving in the wild. *Proceedings of the 12th FDG*, 1–10. DOI: [10.1145/3102071.3110566](https://doi.org/10.1145/3102071.3110566).
- **Lanzi, P. L., Loiacono, D., & Stucchi, R. (2014).** Evolving maps for match balancing in first person shooters. *2014 IEEE Conference on Computational Intelligence and Games (CIG)*, 1–8. DOI: [10.1109/CIG.2014.6932901](https://doi.org/10.1109/CIG.2014.6932901).
- **LaValle, S. M., Lin, D., Guibas, L. J., Latombe, J. C., & Motwani, R. (2002).** Pursuit-evasion in an unknown environment using minimal sensing. *IEEE Transactions on Robotics and Automation*, 18(5), 858–867. DOI: [10.1109/TRA.2002.803463](https://doi.org/10.1109/TRA.2002.803463).
- **Morais, V., Bulhões, T., & Subramanian, A. (2024).** Exact and heuristic algorithms for minimizing the makespan on a single machine scheduling problem with sequence-dependent setup times and release dates. *European Journal of Operational Research*, 315(2), 442–453. DOI: [10.1016/j.ejor.2023.11.024](https://doi.org/10.1016/j.ejor.2023.11.024).
- **Pech, A., Lam, C. P., & Masek, M. (2020).** Quantifiable Isovist and Graph-Based Measures for Automatic Evaluation of Different Area Types in Virtual Terrain Generation. *IEEE Access*, 8, 216491–216506. DOI: [10.1109/ACCESS.2020.3041276](https://doi.org/10.1109/ACCESS.2020.3041276).
- **Sachs, S., LaValle, S. M., & Rajko, S. (2004).** Visibility-Based Pursuit-Evasion in an Unknown Planar Environment. *The International Journal of Robotics Research*, 23(1), 3–26. DOI: [10.1177/0278364904041322](https://doi.org/10.1177/0278364904041322).
- **Shin, I., & Lee, I. (2003).** A compositional scheduling framework for real-time systems of periodic tasks. *IEEE RTSS*, 150–160. DOI: [10.1109/REAL.2003.1253262](https://doi.org/10.1109/REAL.2003.1253262).
- **Summers, A. (2014).** *Imageability and Intelligibility in 3D Game Environments*. Ph.D. thesis, University College London (UCL).
- **Tanaka, S., Araki, M., & Fujikuma, S. (2021).** An exact algorithm for single-machine scheduling with release dates, sequence-dependent setup times, and maximum lateness minimization. *European Journal of Operational Research*, 290(3), 845–857. DOI: [10.1016/j.ejor.2020.08.036](https://doi.org/10.1016/j.ejor.2020.08.036).
- **Thiele, L., Chakraborty, S., & Naedele, M. (2000).** Real-time calculus for scheduling hard real-time systems. *IEEE ISCAS*, 4, 101–104. DOI: [10.1109/ISCAS.2000.857418](https://doi.org/10.1109/ISCAS.2000.857418).
- **Turner, A., Doxa, M., O'Sullivan, D., & Penn, A. (2001).** From isovists to visibility graphs: a methodology for the analysis of architectural space. *Environment and Planning B: Planning and Design*, 28(1), 103–121. DOI: [10.1068/b2684](https://doi.org/10.1068/b2684).
- **van der Linden, R., Lopes, R., & Bidarra, R. (2014).** Procedural Generation of Dungeons. *IEEE Transactions on Computational Intelligence and AI in Games*, 6(1), 78–89. DOI: [10.1109/TCIAIG.2013.2290371](https://doi.org/10.1109/TCIAIG.2013.2290371).
- **Zhang, Y., Xu, K., Zhao, R., & Verbrugge, C. (2026).** Path2Patrol: Path-Conditioned Guard Generation in Stealth Games through MAP-Elites. *2026 IEEE Conference on Games (CoG)*.
