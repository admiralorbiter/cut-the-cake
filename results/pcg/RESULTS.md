# PCG Level Generation & Modular Composition Findings Freeze

**Freeze Date:** 2026-08-23  
**Status:** `FROZEN COMPUTATIONAL ARTIFACT`

---

## 1. 25,000-Candidate Corpus Sweeps

We evaluated 25,000 randomly assembled 6-module level graphs across authored (Library 1) and held-out (Library 2) module suites:

| Evaluation Metric | Library 1 (25k Assemblies) | Library 2 Held-Out (25k Assemblies) | Interpretation |
| :--- | :---: | :---: | :--- |
| **Audit A (Topological Reachability)** | 25,000 (100.0%) | 25,000 (100.0%) | Valid graph grammar / socket alignment. |
| **Audit B (Static $K_{\text{static}} \le 2$)** | 11,296 (45.18%) | 11,191 (44.76%) | Admitted by static line-of-sight heuristic. |
| **Audit C (Global Composed Contract)** | 7,333 (29.33%) | 7,119 (28.48%) | Certified deadline-feasible under reticle slew. |
| **Audit D (Independent Local Transfer)** | 7,333 (29.33%) | 7,119 (28.48%) | Locally feasible constituents. |
| **$A \cap B \cap \neg C$ ($K_{\text{static}}$ Blind Spot)** | **6,704 (26.82%)** | **6,789 (27.16%)** | **False Positive:** Admitted by $K \le 2$, but model-infeasible ($L^* > 0$). |
| **$A \cap \neg B \cap C$ ($K_{\text{static}}$ False Alarm)** | **2,741 (10.96%)** | **2,717 (10.87%)** | **False Alarm:** Rejected by $K > 2$, but solvably staggered. |
| **$C \equiv D$ Concordance** | **100.00% (0 diff)** | **100.00% (0 diff)** | Local quiescence implies global feasibility. |

---

## 2. Precertified Library Linter (Condition E)

Precertifying constituent modules at authoring time guarantees:
- **Feasibility Rate:** 5,000 / 5,000 (100.0%) generated assemblies are globally deadline-feasible.
- **Runtime Schedulability Overhead:** **0.0 ms** (bypasses 100% of runtime transfer matrix multiplication).

---

## 3. Replicated Paired-Seed MAP-Elites ($N=30$)

30 paired-seed evolutionary runs (3,000 evaluations each) over 2D behavioral space ($\text{Pace Proxy} \times \text{Route Redundancy}$):
- **Condition C vs. Condition A:** $\Delta\text{Coverage} = -0.19\%$ (95% CI: $[-1.25\%, +0.87\%]$). Confirms **non-inferiority** ($> -2.0\%$).
- **Condition E vs. Condition A:** $\Delta\text{Coverage} = +2.38\%$ (95% CI: $[+1.46\%, +3.30\%]$), confirming statistically significant superiority over unconstrained topology search.
