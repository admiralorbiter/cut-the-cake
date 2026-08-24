# Critical Uniform Actionability Lead ($\ell^*_{\text{uniform}}$) & Native ViZDoom Near-Boundary Probe

**AUTOMATED SCIENCE FREEZE — 2026-08-23**  
**Status:** `COMPUTATIONALLY VERIFIED & ENGINE PROBED`  
**Data Files:** [`results.json`](results.json) | [`vizdoom_lead_sweep.json`](vizdoom_lead_sweep.json)

---

## 1. Theoretical Framework & Monotonicity Theorem

We parameterize target actionability by a **uniform advance-information lead** $\ell \ge 0$:
$$a_j(\ell) = \max(0, \, r_j - \ell)$$
$$C_{\pi_k}(\ell) = \max\Big(r_{\pi_k}, \, \max(C_{\pi_{k-1}}, a_{\pi_k}(\ell)) + q_{\pi_{k-1}, \pi_k}\Big) + A + p_{\pi_k}$$
$$\mathcal{M}(\ell) = -L^*(\ell)$$

### Proposition 1 (Monotonic Actionability)
*Let $\gamma$ be a fixed traversal route, $\mathcal{T}$ a set of persistent threat regions, and $\ell \ge 0$ a uniform advance actionability lead. For any $\ell_2 \ge \ell_1 \ge 0$, the optimal tactical margin satisfies $\mathcal{M}(\ell_2) \ge \mathcal{M}(\ell_1)$ (equivalently, $L^*(\ell_2) \le L^*(\ell_1)$).*

*Proof:* $\ell_2 \ge \ell_1 \implies a_j(\ell_2) \le a_j(\ell_1)$. For any fixed permutation $\pi$, induction over $C_{\pi_k}$ gives $C_{\pi_k}(\ell_2) \le C_{\pi_k}(\ell_1) \, \forall k$, so $L^\pi(\ell_2) \le L^\pi(\ell_1)$. Minimizing over all permutations yields $L^*(\ell_2) \le L^*(\ell_1)$ and $\mathcal{M}(\ell_2) \ge \mathcal{M}(\ell_1)$. $\blacksquare$

*Implementation Verification:* Verified across all 72 experimental instances (12 pilot stimuli + 60 benchmark arenas): 100% of discrete curves $\mathcal{M}(\ell)$ are monotone non-decreasing.

---

## 2. Decoupling $\Delta\mathcal{M}_{\text{knowledge}}$ from $\ell^*_{\text{uniform}}$

The Critical Uniform Actionability Lead $\ell^*_{\text{uniform}} = \inf \{ \ell \ge 0 : \mathcal{M}(\ell) \ge 0 \}$ is not a redundant transform of $\Delta\mathcal{M}_{\text{knowledge}}$:
- $\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$ measures *total capacity gain* under maximal pre-aim.
- $\ell^*_{\text{uniform}}$ measures *temporal urgency* (how early directional information must arrive to avoid deadline failure).

### Disagreement Pair Demonstration
| Stimulus ID | $\mathcal{M}_{\text{reveal}}$ | $\mathcal{M}_{\text{preaim}}$ | $\Delta\mathcal{M}_{\text{know}}$ | Critical Lead $\ell^*_{\text{tic}}$ | Critical Lead $\ell^*_{\text{ms}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **STIM_07 (Spaced Baffle)** | $-4\,\text{tics}$ | $+3\,\text{tics}$ | **$+7\,\text{tics}$** | **$4\,\text{tics}$** | **$114.3\,\text{ms}$** |
| **STIM_11 (Zigzag Flank)** | $-6\,\text{tics}$ | $+1\,\text{tic}$ | **$+7\,\text{tics}$** | **$6\,\text{tics}$** | **$171.4\,\text{ms}$** |

*Interpretation:* Despite identical full-knowledge benefit ($\Delta\mathcal{M} = +7\,\text{tics}$), `STIM_11` requires 50% more advance actionability ($171.4\,\text{ms}$ vs. $114.3\,\text{ms}$) than `STIM_07` to rescue its deficit.

---

## 3. Native ViZDoom Near-Boundary Actionability Probe (40 Deterministic Executions)

To evaluate how advance actionability behaves in real external game engine execution, we performed a full integer-lead sweep ($\ell \in [0, 9]\,\text{tics}$) across all four selected knowledge-rescuable fixtures in headless C++ ViZDoom (4 fixtures $\times$ 10 parameter points = 40 deterministic executions).

### Residual Convention (Lateness Domain)
$$\Delta^L_{\text{export}}(\ell) = L^*_{\text{eng}}(\ell) - L^*_{\text{pred}}(\ell)$$
$$\Delta^L_{\text{execution}}(\ell) = L_{\text{realized}}(\ell) - L^*_{\text{eng}}(\ell)$$
$$\Delta^L_{\text{total}}(\ell) = L_{\text{realized}}(\ell) - L^*_{\text{pred}}(\ell)$$

### Three-Stage Threshold Decomposition
| Fixture ID | Source Threshold $\ell^*_{\text{source}}$ | Engine-Model Threshold $\ell^*_{\text{engine-model}}$ | Observed Survival $\ell^*_{\text{survival}}$ | Discrepancy $(\ell^*_{\text{survival}} - \ell^*_{\text{source}})$ |
| :--- | :---: | :---: | :---: | :---: |
| **STIM_06 (Double Baffle)** | $5\,\text{tics}$ ($142.9\,\text{ms}$) | $4\,\text{tics}$ ($114.3\,\text{ms}$) | **$4\,\text{tics}$ ($114.3\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |
| **STIM_07 (Spaced Baffle)** | $4\,\text{tics}$ ($114.3\,\text{ms}$) | $3\,\text{tics}$ ($85.7\,\text{ms}$) | **$3\,\text{tics}$ ($85.7\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |
| **STIM_09 (Aperture Burst)** | $4\,\text{tics}$ ($114.3\,\text{ms}$) | $3\,\text{tics}$ ($85.7\,\text{ms}$) | **$5\,\text{tics}$ ($142.9\,\text{ms}$)** | $+1\,\text{tic}$ ($+28.6\,\text{ms}$) |
| **STIM_11 (Zigzag Flank)** | $6\,\text{tics}$ ($171.4\,\text{ms}$) | $4\,\text{tics}$ ($114.3\,\text{ms}$) | **$5\,\text{tics}$ ($142.9\,\text{ms}$)** | $-1\,\text{tic}$ ($-28.6\,\text{ms}$) |

*Mechanistic Findings:*
1. **Export Translation Shift:** Export-conditioned geometry shifts the intermediate scheduling boundary earlier than the source-model boundary in all four selected fixtures: by 1 tic for `STIM_06`, `STIM_07`, and `STIM_09`, and by 2 tics for `STIM_11`.
2. **Motor Execution Residual:** For `STIM_06` and `STIM_07`, observed engine survival matches the engine-conditioned model threshold exactly ($\ell^*_{\text{survival}} = \ell^*_{\text{engine-model}}$). For `STIM_09` and `STIM_11`, minor discrete motor turning latencies and angle tolerances shift the realized boundary by $+1$ to $+2$ tics.
3. **Threshold Agreement:** Across all four selected knowledge-rescuable fixtures (4/4), the observed survival threshold $\ell^*_{\text{survival}}$ tracks the theoretical source prediction $\ell^*_{\text{source}}$ within $|\Delta \ell^*| \le 1\,\text{tic}$ ($28.6\,\text{ms}$), consistent with the previously observed small export/execution residual regime.

---

## 4. Population Benchmark Breakdown ($N=60$ Arenas)

| Geometric Mechanism Family | Total Arenas | Blind-Clearable | Knowledge-Rescuable | Structurally Overloaded | Rescuable Lead Range $\ell^*_{\text{tic}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **F1: Staggered Baffles** | 10 | 10 | 0 | 0 | — |
| **F2: Crossfire Separation** | 10 | 3 | **3** | 4 | $1\text{--}2\,\text{tics}$ ($28.6\text{--}57.1\,\text{ms}$) |
| **F3: Burst Congestion** | 10 | 0 | **2** | 8 | $3\text{--}5\,\text{tics}$ ($85.7\text{--}142.9\,\text{ms}$) |
| **F4: Alternating Flanks** | 10 | 0 | **2** | 8 | $2\text{--}6\,\text{tics}$ ($57.1\text{--}171.4\,\text{ms}$) |
| **F5: Deadline Compression** | 10 | 7 | 0 | 3 | — |
| **F6: Flank Smoothness** | 10 | 0 | 0 | 10 | — |
| **Total** | **60** | **20 (33.3%)** | **7 (11.7%)** | **33 (55.0%)** | **$1\text{--}6\,\text{tics}$ ($28.6\text{--}171.4\,\text{ms}$)** |
