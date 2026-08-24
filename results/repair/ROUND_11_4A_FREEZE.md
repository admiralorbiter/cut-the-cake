# Round 11.4A Scientific Freeze: Inverse Tactical Repair & External-Transfer Validation

**Status:** FROZEN  
**Date:** August 2026  
**Git Tag:** `round11.4a-freeze`  
**Scope Boundary:** End of Scientific Research Phase (Rounds 1–11.4A) / Start of Tactical CAD Development (Horizon 1+)  

---

## 1. Executive Summary & Canonical Audited Metrics

This document certifies the frozen computational and external-engine findings of **Round 11.4A** (Inverse Tactical Repair Audit & External-Transfer Hardening). All statistics reported below are derived dynamically from the canonical $N=50$ benchmark execution in [`results/repair/results.json`](./results.json) and [`results/repair/RESULTS.md`](./RESULTS.md).

| Canonical Metric | Audited Value | Scientific Definition & Interpretation |
| :--- | :---: | :--- |
| **Audited Broken Population ($N$)** | **50 / 50 (100.0%)** | All arenas verified to start strictly with initial tactical margin $\mathcal{M}_{\text{source}} < 0$ and die in baseline native ViZDoom execution ($100\%$ initial fatal rate). |
| **Source-Model Repair Success Rate** | **80.0% (40 / 50)** | Fraction of broken arenas where the offline optimizer finds a grid-minimal feasible translation achieving $\mathcal{M}_{\text{source}} \ge +2\,\text{tics}$ ($+57.1\,\text{ms}$). |
| **Native ViZDoom Engine Rescue Rate** | **60.0% (30 / 50)** | Fraction of total broken arenas that flip from baseline engine death ($0\,\text{HP}$) to verified engine survival ($100\,\text{HP}$) after exported level execution. |
| **Engine Transfer Efficiency** | **75.0% (30 / 40)** | Fraction of source-successful repairs that successfully transfer to verified native ViZDoom engine survival ($\text{Rescued} / \text{Source-Success}$). |
| **Median Edit Distance ($d^*$)** | **0.85 m** (Mean: $0.89\,\text{m}$) | Grid-minimal displacement evaluated across the declared translation operator set $\mathcal{T}_{\text{obs}}$. |
| **Median Repair Runtime** | **292.8 ms** (Mean: $357.2\,\text{ms}$) | Exhaustive search runtime evaluating candidate obstacles $\times$ candidate directions $\times$ grid steps. |
| **Mean Export Residual ($\Delta_{\text{export}} L$)** | **+1.64 tics** ($+46.9\,\text{ms}$) | Mean lateness shift between continuous 2D source raycasting and quantized 3D Doom WAD linedef geometry. |
| **Mean Execution Residual ($\Delta_{\text{execution}} L$)** | **-0.08 tics** ($-2.3\,\text{ms}$) | Mean lateness shift between engine observation and realized oracle controller completion in discrete engine physics. |

---

## 2. Formal Three-Layer Distinction & Evidence Vocabulary

To prevent conflation between theoretical models and real-time game engine execution, this project enforces a strict three-layer terminology:

1. **Source-Model Repair:** The offline mathematical optimizer operating on 2D continuous geometry certifies that schedule completion satisfies $\mathcal{M}_{\text{source}} = -L^*_{\text{source}} \ge \epsilon_{\text{target}}$ (+2 tics).
2. **Native Engine Rescue:** The exported WAD geometry is executed inside headless C++ ViZDoom (35 Hz tic clock, native physics and line-of-sight), and the player agent successfully clears all enemies and exits the room with $100\,\text{HP}$.
3. **Engine Transfer Efficiency:** The conditional probability $P(\text{Engine Rescue} \mid \text{Source-Model Success})$. A source-feasible repair can fail to rescue in native engine execution when positive export/execution residuals erode the theoretical margin reserve ($\Delta_{\text{total}} L > \mathcal{M}_{\text{source}}$).

### Residual Decomposition Identity
$$\Delta_{\text{total}} L = \Delta_{\text{export}} L + \Delta_{\text{execution}} L = (L^*_{\text{engine}} - L^*_{\text{source}}) + (L_{\text{realized}} - L^*_{\text{engine}})$$

---

## 3. Contingency Matrix: Source Repair vs. Native Engine Rescue

$$
\begin{array}{c|cc|c}
\text{Source Optimizer} \backslash \text{ViZDoom Engine} & \text{Engine Rescued (Survived)} & \text{Engine Fatal (Dead)} & \text{Total} \\
\hline
\text{Source Repair Success} & \mathbf{30} \text{ (60.0\%)} & \mathbf{10} \text{ (20.0\%)} & \mathbf{40} \text{ (80.0\%)} \\
\text{Source Repair Fail} & \mathbf{0} \text{ (0.0\%)} & \mathbf{10} \text{ (20.0\%)} & \mathbf{10} \text{ (20.0\%)} \\
\hline
\text{Total} & \mathbf{30} \text{ (60.0\%)} & \mathbf{20} \text{ (40.0\%)} & \mathbf{50} \text{ (100.0\%)}
\end{array}
$$

* **Source Success $\times$ Engine Rescued (30 arenas, 60.0%):** Robust geometric repairs where theoretical margin reserve transfers directly to engine survival.
* **Source Success $\times$ Engine Fatal (10 arenas, 20.0%):** Transfer gap where source-model $\mathcal{M} \ge +2\,\text{tics}$ is eroded by positive export residuals ($\Delta_{\text{export}} L$), primarily in Family 4 3-threat congestion.
* **Source Fail $\times$ Engine Fatal (10 arenas, 20.0%):** Correct negative where the layout is unrepairable within the declared single-obstacle translation operator set, and player remains dead in native Doom.
* **Source Fail $\times$ Engine Rescued (0 arenas, 0.0%):** Zero spontaneous false survivals without valid geometric repair.

---

## 4. Family-by-Family Audited Breakdown

| Mechanism Family | Arenas | Initial $\mathcal{M}$ | Source Success | Median Edit $d^*$ | Engine Rescue | Transfer Efficiency | Mean $\Delta_{\text{export}} L$ | Mean $\Delta_{\text{execution}} L$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Family 1: Stagger Deficit** | 10 | $-6 \dots -4\,\text{t}$ | 10/10 (100%) | 0.97 m | 10/10 (100%) | **100%** | $-0.1\,\text{t}$ | $-0.4\,\text{t}$ |
| **Family 2: Aperture Crossfire** | 10 | $-15 \dots -13\,\text{t}$ | 10/10 (100%) | 1.15 m | 8/10 (80%) | **80%** | $+0.4\,\text{t}$ | $+0.7\,\text{t}$ |
| **Family 3: Blind Spot** | 10 | $-7 \dots -2\,\text{t}$ | 0/10 (0%) | 0.00 m | 0/10 (0%) | **0%** | $+0.0\,\text{t}$ | $+0.0\,\text{t}$ |
| **Family 4: Triad Congestion** | 10 | $-12 \dots -8\,\text{t}$ | 10/10 (100%) | 0.60 m | 3/10 (30%) | **30%** | $+6.6\,\text{t}$ | $-0.1\,\text{t}$ |
| **Family 5: Flank Squeeze** | 10 | $-16 \dots -15\,\text{t}$ | 10/10 (100%) | 0.82 m | 9/10 (90%) | **90%** | $+1.3\,\text{t}$ | $-0.6\,\text{t}$ |

---

## 5. Declared Repair Operator Set $\mathcal{T}_{\text{obs}}$ & Invariant Preservation

The Round 11.4A optimizer solves for grid-minimal translations over a strictly declared operator set:
$$\mathcal{T}_{\text{obs}}(G) = \left\{ G' = \text{translate}(O_i, d \cdot \hat{u}) \;\middle|\; O_i \in \text{Obstacles}(G), \; \hat{u} \in \mathcal{U}, \; d \in [\delta, d_{\max}] \right\}$$
where:
* $\mathcal{U} = \{ \hat{n}, -\hat{n}, (+1, 0), (-1, 0), (0, +1), (0, -1) \}$ (diagnostic bottleneck normal and cardinal axes).
* Grid resolution $\delta = 0.05\,\text{m}$, maximum perturbation budget $d_{\max} = 1.80\,\text{m}$.
* **Rigorous Geometric Preservation Validator (`validate_repair_preservation`):**
  1. Room boundary immutability ($\text{Boundary}(G') \equiv \text{Boundary}(G)$).
  2. Obstacle count and individual polygon area invariance.
  3. Obstacle strict containment inside room boundary.
  4. Pairwise disjointness between obstacles.
  5. Threat anchor and bounding box non-intersection (obstacles cannot clip into or enclose monsters).
  6. Route waypoint immutability and non-clipping.
  7. Ingress/egress port geometry invariance.

---

## 6. Reproduction Protocol

To reproduce the frozen results from a fresh clone:

```bash
# 1. Environment Setup
git checkout round11.4a-freeze
pip install -e .

# 2. Run the Complete Verification Suite (80 tests)
pytest -v

# 3. Execute Canonical Round 11.4A Benchmark
python -m cut_the_cake.repair_benchmark

# 4. Verify Output Hashes
# Generates results/repair/results.json and results/repair/RESULTS.md
```

### Execution Telemetry
* **Python Version:** Python 3.12.0
* **External Engine:** ViZDoom 1.3.0 (ZDoom C++ core, 35 Hz tickrate)
* **OS Platform:** Windows 11 (AMD64)
* **Full Test Suite Runtime:** ~66 seconds (80 passed)
* **Benchmark Runtime:** ~14 seconds (50 micro-arenas $\times$ repair $\times$ dual ViZDoom episodes)

---

## 7. Known Scientific Limitations & Boundary Conditions

1. **Declared Operator Set Scope:** The optimizer performs 1D/2D translations of rigid obstacles. It does not morph obstacle topology, split polygons, or synthesize new walls.
2. **Fixed Authored Traversal Route:** Player movement is evaluated along a designated polyline trajectory $\gamma(s)$ at constant speed $v_{\text{move}} = 4.5\,\text{m/s}$.
3. **Prospective Human Validation:** Human cognitive experiments ([`human/PILOT_PROTOCOL.md`](../../human/PILOT_PROTOCOL.md)) are prospective and pre-registered; they are not required for the current computational schedulability and game engine transfer claims.
4. **Subsequent Engineering Boundary:** All subsequent product development (Tactical CAD, Phaser UI, scene manifests, interactive debuggers) builds on top of this frozen scientific foundation and does not alter the frozen empirical results unless an explicit new scientific research round is initiated.
