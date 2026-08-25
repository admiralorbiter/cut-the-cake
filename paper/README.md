# Cut the Cake — Research Manuscript & Scientific Scope

This directory contains the primary academic research manuscript for the *Cut the Cake* project.

---

## Document Scope: Round 11.4A Paper Freeze

The manuscript [`manuscript.md`](manuscript.md) documents the formal theoretical foundations, empirical validation pipeline, and engine translation benchmarks through the **Round 11.4A Scientific Freeze** (August 2026):

1. **Formal Scheduling Model:** Formulation of trajectory-conditioned tactical clearability as a single-machine real-time scheduling problem with release times, deadlines, and sequence-dependent setup costs ($1 \mid r_j, s_{ij} \mid L_{\max}$).
2. **Min-Plus Dioid Algebra:** The Exact State-Conditioned Spatial Transfer Map $C_M$ and the $C \equiv D$ composition theorem for modular level assembly.
3. **Synthetic PCG Verification (Condition E):** Zero false certifications across 25,000 candidate procedural dungeon assemblies.
4. **Controlled Discrete Simulation:** 9,000 discrete 35-Hz clearing episodes across 60 micro-arenas demonstrating Tactical Margin superiority over static visibility counts ($\text{LOGFO-AUC} = 1.0000$).
5. **Native Game Engine Translation (ViZDoom):** Empirical lateness residuals and deployment reserve calibration in native C++ Doom.
6. **Inverse Tactical Repair Optimizer:** Minimal geometric perturbation search achieving 80% source repair and 75% native ViZDoom engine transfer efficiency on 50 genuinely unserviceable arenas.

---

## Post-Manuscript Research Extensions

Subsequent research horizons expand beyond the core manuscript's 2D planar scope and are documented across the project repository:

| Extension | Key Milestones | Where Documented |
| :--- | :--- | :--- |
| **Real-Map Graybox Case Studies** | *Counter-Strike* Dust II (A-Long & B-Tunnels), *Valorant* Ascent (Wine), *CoD MW4* Transit 213; Suffix Tactical Margin ($\mathcal{M}_{\text{suffix}}$) | [**docs/WHAT_WE_DISCOVERED.md**](../docs/WHAT_WE_DISCOVERED.md) & [**results/m5a_dust2_a_long.json**](../results/m5a_dust2_a_long.json) |
| **2.5D Layered Elevation** | Finite-height obstacles, elevated platforms, and volumetric prism raycasting ($P_i \times [z_{\min}, z_{\max}]$) | [**docs/WHAT_WE_DISCOVERED.md**](../docs/WHAT_WE_DISCOVERED.md) & [`cad_document.py`](../src/cut_the_cake/cad_document.py) |
| **$S^2$ Spherical Aiming Dynamics** | Great-circle geodesic setup costs on unit sphere $S^2$ with $\mathrm{SO}(3)$ rotation invariance | [**ROADMAP.md**](../ROADMAP.md) & [`geometry.py`](../src/cut_the_cake/geometry.py) |
| **3D Unit-Sphere Slerp Controller** | Deterministic 35-Hz 3D controller execution achieving exact schedule parity ($t_j^{\text{event}} \equiv C_j - 1$) | [**docs/EVIDENCE_AND_LIMITS.md**](../docs/EVIDENCE_AND_LIMITS.md) & [`test_m6c_controller_3d_execution.py`](../tests/test_m6c_controller_3d_execution.py) |
| **Interactive Tactical CAD Workbench** | Live browser editor with real-time Suffix Margin ribbons and closed-loop Auto-Fix optimizer | [`cad_server.py`](../src/cut_the_cake/cad_server.py) |
| **Advanced Evidence Lab** | 4-pane Tactical MRI replaying frozen counterexamples (M08 vs M11, F1 repair, quantization staircases) | [**explainer/advanced/index.html**](../explainer/advanced/index.html) |
