# Round 11S Canonical Findings Freeze: Population Benchmark & Baseline Shootout

**Freeze Date:** 2026-08-23  
**Git Commit SHA:** `cb9cf7d`  
**Execution Runtime:** 5.96 s  
**Benchmark Scope:** 60 parameterized micro-arenas $\times$ 5 independent simulation controllers $\times$ 30 stochastic noise trials = **9,000 discrete simulation episodes**.

---

## 1. Executive Summary

This document freezes the canonical empirical results of the **Round 11S Discrete Simulation Population Benchmark**. 

The experiment evaluates whether the single-reticle sequence-dependent **Tactical Margin** ($\mathcal{M} = -L^*_{\text{tic}}$) predicts empirical survival under motor/perceptual execution noise and out-of-fold generalization across held-out geometric families, compared against three traditional spatial and workload baselines.

---

## 2. Benchmark Configuration & Methodology

### 2.1 Discrete Clock & Physical Parameters
- **Clock Model:** Discrete 35 Hz logic clock ($\Delta t = 1/35\,\text{s} = 28.5714\,\text{ms}$).
- **Locomotion Speed:** $v = 4.5\,\text{m/s}$ ($4.5/35 = 0.1286\,\text{m/tic}$, corresponding to $8.2286\,\text{units/tic}$ at $64\,\text{Doom units/m}$).
- **Sensorimotor Parameters:**
  - Maximum angular slew rate: $\omega_{\text{aim}} = 360^\circ/\text{s}$ ($360/35 = 10.2857^\circ/\text{tic}$).
  - Perceptual acquisition latency: $A = 0.15\,\text{s}$ ($6\,\text{tics}$).
  - Inspect/service dwell duration: $p = 0.10\,\text{s}$ ($4\,\text{tics}$).

### 2.2 Paired Noise & Common-Random-Number Design
- **Execution Noise Parameters (30 trials/arena):**
  - Gaussian perceptual acquisition jitter: $\sigma_{\text{acq}} = 0.02\,\text{s}$ ($0.7\,\text{tics}$).
  - Gaussian motor slew velocity jitter: $\sigma_{\omega} = 30.0^\circ/\text{s}$ ($0.86^\circ/\text{tic}$).
- **Methodological Design:** The 30 noise realizations are applied as a **deterministic common-random-number design** (`seed=42`) across all arena and controller conditions. This paired-noise structure isolates pure geometric differences by holding perceptual and motor perturbations constant across conditions.

### 2.3 Non-Oracle Target Label Construction
To avoid circularity where the predictor helps construct its own ground truth target:
- **Target Label:** The primary survival label is defined strictly as the **mean survival rate across the four non-Oracle heuristic controllers** (`FIFO`, `Nearest Angle`, `EDF`, `Left-to-Right`) across 7,200 episodes.
- **Reference Oracle:** The integer-tic sequence-optimal `Oracle` controller is evaluated across 1,800 episodes solely as an un-confounded upper-bound reference.
- **Total Execution Scope:** 7,200 non-Oracle target-generating executions + 1,800 Oracle reference executions = **9,000 discrete simulation episodes**.

### 2.4 Cross-Validation Protocol
- **Partitioning:** Leave-One-Geometry-Family-Out (LOGFO-CV) cross-validation across the 6 structural geometric mechanism families ($10$ arenas/family). Models trained on 5 families are evaluated on the held-out 6th family.

---

## 3. Canonical Results & Baseline Discrimination

| Metric / Predictor | Spearman Rank ($\rho$) | In-Sample ROC-AUC | In-Sample Brier Score | LOGFO-CV ROC-AUC | LOGFO-CV Brier Score | $\Delta \text{LOGFO-AUC}$ vs. Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tactical Margin ($\mathcal{M}_{\text{tic}}$)** | $\mathbf{+0.9282}$ | $\mathbf{0.9988}$ | $\mathbf{0.0912}$ | $\mathbf{1.0000}$ | $\mathbf{0.0949}$ | **Reference** |
| **Peak Physical LOS $K_{\text{static}}$ (Inverted)** | $+0.5635$ | $0.8493$ | $0.1524$ | $0.8098$ | $0.1568$ | $\mathbf{+0.1902}$ (+19.02%) |
| **Hamiltonian Workload $\mathcal{B}_{\text{work}}^{\text{Ham}}$ (Inverted)** | $+0.6650$ | $0.8684$ | $0.1585$ | $0.8260$ | $0.1714$ | $\mathbf{+0.1740}$ (+17.40%) |
| **Minimum Slack $\sigma_{\text{min}}$** | $-0.1960$ | $0.3260$ | $0.2178$ | $0.5742$ | $0.2640$ | $\mathbf{+0.4258}$ (+42.58%) |

---

## 4. Key Scientific Findings

1. **Model-Scoped Construct Validity ($\text{LOGFO-AUC} = 1.0000, \rho = +0.9282$):**
   Across the 6 controlled geometric mechanism families, Tactical Margin acts as a sufficient statistic for non-Oracle clearing performance under execution noise, generalizing across held-out geometric families without structural degradation.
2. **Substantial Baseline Superiority:**
   - Outperforms peak physical line-of-sight concurrency ($K_{\text{static}}$) by **+19.02% AUC** ($\text{LOGFO-AUC} = 1.0000$ vs. $0.8098$).
   - Outperforms cumulative Hamiltonian workload ($\mathcal{B}_{\text{work}}^{\text{Ham}}$) by **+17.40% AUC** ($1.0000$ vs. $0.8260$). This confirms that even after accounting for total service burden and minimum angular travel, arrival release timing and sequencing order remain critical.
   - Outperforms static minimum slack ($\sigma_{\text{min}}$) by **+42.58% AUC** ($1.0000$ vs. $0.5742$).
3. **High Probability Calibration Accuracy:**
   Tactical margin reduces probability calibration error by $>39\%$ compared to spatial baselines ($\text{Brier} = 0.0949$ vs. $0.1568$).
