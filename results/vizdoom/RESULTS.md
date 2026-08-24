# Native ViZDoom Engine Residual Validation Findings Freeze

**Freeze Date:** 2026-08-23  
**Status:** `FROZEN COMPUTATIONAL ARTIFACT`  
**Engine:** Headless C++ ZDoom / ViZDoom (`vzd.DoomGame`)

---

## 1. Engine Bridge & Arbitration Architecture

- **Quantized WAD Generation:** Compiled directly to integer Doom units ($64\,\text{units/m}$). Line of sight evaluated against binary WAD linedefs and player position `POSITION_X/Y`.
- **Authoritative Arbitration:** Hostile deadline breaches execute `kill` commands directly in Doom. Survival evaluated strictly from `is_player_dead()` and engine `HEALTH <= 0`.

---

## 2. Three-Layer Lateness Decomposition & Residuals

We formalize three distinct lateness quantities:
1. $L^*_{\text{predicted}}$: Optimal schedule computed offline from continuous 2D geometry.
2. $L^*_{\text{engine-conditioned}}$: Optimal schedule recomputed from quantized WAD geometry and engine player locomotion $(R_j^{\text{engine}}, \theta_j^{\text{engine}})$.
3. $L_{\text{realized}} = \max_j (C_j^{\text{engine}} - D_j^{\text{engine}})$: Realized controller service completion lateness.

### 2.1 Empirical Residual Metrics (12 Micro-Arenas)
- $\max |\Delta_{\text{export}}| = 3\,\text{tics}$ ($85.7\,\text{ms}$)
- $\max |\Delta_{\text{execution}}| = 1\,\text{tic}$ ($28.5\,\text{ms}$)
- $\text{Mean } |\Delta_{\text{total}}| = 0.83\,\text{tics}$ ($23.7\,\text{ms}$)
- **Deployment Reserve ($\epsilon_{\text{deploy}} = 3\,\text{tics}$):** Setting an empirical guard band of $\epsilon_{\text{deploy}} = 3\,\text{tics}$ ($85.7\,\text{ms}$) achieves **100% survival** across all arenas with predicted margin $\mathcal{M}_{\text{pred}} \ge 3\,\text{tics}$.

---

## 3. Epistemic Separation in Engine Execution

In native ViZDoom execution of `F3_BurstCongestion_02`:
- **Reveal-Gated Controller ($a_1 = r_1$):** $L^* = +4\,\text{tics}$ ($\mathcal{M} = -4\,\text{tics}$) $\implies$ Player dies at Tic 70.
- **Pre-Aim Controller ($a_1 = 0$):** $L^* = -2\,\text{tics}$ ($\mathcal{M} = +2\,\text{tics}$) $\implies$ Player clears at Tic 67, surviving natively.
