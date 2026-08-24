# Empirical Pilot Experimental Protocol: Tactical Clearability & Epistemic Familiarity

**Author:** Big Brain Time Research Collective  
**Status:** `INSTRUMENT VALIDATION`  
**Target:** N=1 Mechanistic Instrument & Cognitive Familiarity Pilot

---

## 1. Experimental Objectives

1. Evaluate whether **Tactical Margin** ($\mathcal{M}_{\text{reveal}}$) predicts human clearing performance and subjective fairness in unfamiliar layouts.
2. Evaluate whether repeated exposure to the same geometric layout induces an **epistemic transition** from reveal-gated clearing toward pre-aiming ($\mathcal{M}_{\text{preaim}}$).
3. Directly measure the intermediate cognitive mechanism: does layout familiarity shrink reveal-time reticle angular error ($E_j^{\text{reveal}} = |\theta_{\text{reticle}}(r_j) - \theta_j(r_j)|$)?
4. Evaluate whether the theoretical knowledge gap ($\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$) predicts continuous performance improvements ($\Delta L_{\text{realized}}$).

---

## 2. Experimental Design

### 2.1 3-Phase Blinded Protocol
- **Phase 1: UNFAMILIAR (Blind Exposure):** 12 micro-arenas presented in randomized order without prior layout preview.
- **Phase 2: LEARNING (Repeat Exposure):** 12 micro-arenas presented in an independently shuffled constrained order.
- **Phase 3: FAMILIAR (Pre-Aim Mastery):** 12 micro-arenas presented in an independently shuffled constrained order.
- **Total Experimental Trials:** 36 trials (3 blocks $\times$ 12 arenas).

### 2.2 Constrained Shuffling
To prevent back-to-back exposure confounds, the last 3 arenas of Block $N$ are constrained from appearing in the first 3 positions of Block $N+1$.

### 2.3 Locomotion & Input Control
- **Locomotion:** Automatic forward route movement at $v = 4.5\,\text{m/s}$ along $\gamma(s)$. No manual forward/backward keys or strafing to prevent invalidating spatial release timestamps $r_j$.
- **Human Controls:** Mouse reticle rotation (`TURN_LEFT_RIGHT_DELTA`) and primary weapon trigger (`ATTACK`) only.

### 2.4 Pre-Session Sensorimotor Calibration
A 2-minute pre-session calibration stage measures:
- Empirical perceptual acquisition latency: $A_{\text{player}}$ (ms).
- Empirical maximum aim velocity: $\omega_{\text{player}}$ (deg/s).
- Computes both $\mathcal{M}_{\text{canonical}}$ and $\mathcal{M}_{\text{personalized}}$ in the session manifest before Block 1 begins.

### 2.5 Practice / Shakedown Stage (Excluded from Analysis)
- 2 practice arenas (`PRACTICE_01_Corridor`, `PRACTICE_02_CornerBaffle`) allow checking mouse sensitivity, automatic movement, firing, and dual ratings before the 36-trial experiment begins.

### 2.6 Dual Post-Trial Psychometric Ratings
1. **Readability (1–7):** *"I could understand where the threats were coming from [1 = Unclear/Confusing, 7 = Completely Clear]"*
2. **Fairness (1–7):** *"The encounter felt fair / reasonably answerable [1 = Bullshit Ambush, 7 = Fair Tactical Fight]"*
