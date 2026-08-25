# Cut the Cake — Model-Derived Player Intuitions

> [!IMPORTANT]
> **Scope & Validation Boundary:**  
> The tactical principles described in this document are **theoretical implications of the deterministic scheduling and geometric model** under declared sensorimotor parameters ($\omega = 360^\circ/\text{s}$, $A = 150\,\text{ms}$, $p = 100\,\text{ms}$).  
> They are **not** yet empirically validated population-level coaching claims. Real competitive matches involve psychological anticipation, auditory cues, utility usage, team trading, and variable motor capabilities.

<p align="center">
  <img src="media/hero_clearability.gif" alt="Single-Reticle Scheduling Loop" width="750" />
</p>

---

## 1. Deconstructing Corner Encounters

Under our single-reticle scheduling model, an encounter around a corner falls into one of three structural categories:

```
                          ┌───────────────────────────┐
                          │   Encounter Structure     │
                          └─────────────┬─────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌──────────────────┐          ┌───────────────────┐           ┌───────────────────┐
│ Blind-Clearable  │          │Knowledge-Rescuable│           │ Structurally      │
│ (M_reveal >= 0)  │          │(M_preaim >= 0)    │           │ Overloaded        │
└────────┬─────────┘          └─────────┬─────────┘           │ (M_preaim < 0)    │
         │                              │                     └─────────┬─────────┘
         ▼                              ▼                               ▼
  Sufficient time                Requires pre-aiming             Cannot be cleared
  to react & clear               behind cover prior              by dry gunplay alone
  on dynamic sightline           to un-occlusion                 under declared model
```

### 1. Blind-Clearable ($\mathcal{M}_{\text{reveal}} \ge 0$)
- **Model meaning:** Even if you have never seen the room before ($a_j = r_j$), the geometry naturally staggers threat reveals or limits angular spread sufficiently that an optimal reticle can clear all targets before any hostile deadline expires.
- **Model implication:** If an encounter is modeled as blind-clearable but a player fails, the model attributes this to sub-optimal clearing permutation, delayed reaction, or motor variance.

### 2. Knowledge-Rescuable ($\mathcal{M}_{\text{reveal}} < 0, \mathcal{M}_{\text{preaim}} \ge 0$)
- **Model meaning:** The room creates simultaneous or near-simultaneous reveals on dynamic entry. However, if the player possesses advance spatial knowledge and pre-aims the primary threat angle behind cover prior to crossing the corner ($a_j = 0$), the reduced angular setup cost restores a positive margin.
- **Model implication:** This encounter cannot be cleared reliably on pure reaction; it strictly requires pre-aiming.

### 3. Structurally Overloaded ($\mathcal{M}_{\text{preaim}} < 0$)
- **Model meaning:** Even with perfect advance knowledge of all threat angles and an optimal clearing sequence, the angular divergence and overlapping response deadlines exceed the mechanical capacity of a single aiming reticle.
- **Model implication:** Under the declared single-agent gunplay model, this fight cannot be solved dry. It requires team coordination, cross-lane trading, or tactical utility (smokes, flashbangs).

<p align="center">
  <img src="media/same_count_timing.gif" alt="Stagger vs Simultaneous Crossfire" width="750" />
</p>

---

## 2. The Mechanics of Corner Distance ("Slicing the Pie")

A well-known heuristic in tactical shooters is to stand as far back from a corner as possible before peeking. The mathematical compiler illustrates the geometric mechanism:

```
[Close to Corner: Wide Angular Divergence]
Player ──> [Corner] ───/─── Threat 1 (Angle: -45°)
                      \____ Threat 2 (Angle: +45°)
Angular spread: Δθ = 90°  ──>  High rotational slew cost (q_ij)  ──>  Tight Margin

[Far from Corner: Narrow Angular Divergence]
Player ─────────> [Corner] ──/── Threat 1 (Angle: -15°)
                           \___ Threat 2 (Angle: +15°)
Angular spread: Δθ = 30°  ──>  Low rotational slew cost (q_ij)   ──>  Generous Margin
```

- **Close to the corner:** The player's angular separation between threats is wide, requiring substantial rotational time ($s_{ij} = \Delta\theta / \omega$).
- **Far from the corner:** The angular separation narrows. The reticle spends fewer milliseconds in transit between targets, increasing the remaining Tactical Margin.

---

## 3. Clearing Order: Deadline Urgency vs. Proximity

Intuition often tempts players to shoot the closest visible enemy first.

The mathematical scheduling model shows that the **optimal clearing permutation ($\pi^*$) prioritizes the most urgent deadline, not necessarily the nearest distance**.

$$\text{Urgency} = D_j - \text{Current Time}$$

If Threat A has an aggressive firing window ($D_A = 8\text{ tics}$) and Threat B has a slower reaction window ($D_B = 14\text{ tics}$), clearing Threat A first prevents an unrecoverable deadline breach on Threat B, even if Threat B is physically closer to the corner.

---

## 4. Understanding Critical Lead ($\ell^*$)

The model defines **Critical Lead ($\ell^*$)** as the minimum advance warning (in milliseconds or time tics) a player needs before un-occlusion to turn an unserviceable encounter into a clearable one:

- **$\ell^* = 0\,\text{ms}$:** The angle can be peeked dynamically on pure visual reaction.
- **$\ell^* \approx 85\,\text{ms}$ (3 tics):** Requires deliberate crosshair placement near the corner edge before peeking.
- **$\ell^* \ge 170\,\text{ms}$ (6+ tics):** Fast dynamic peeking will fail under model parameters. The crosshair must be pre-positioned at the exact target bearing while still behind cover.

---

## 5. Summary Table

| Tactical Principle | Geometric / Scheduling Mechanism | Model Takeaway |
| :--- | :--- | :--- |
| **Slice from deep cover** | Narrows angular divergence $\Delta\theta$ | Reduces reticle slew transit time ($s_{ij}$) |
| **Prioritize tight deadlines** | Earliest Deadline First (EDF) scheduling | Minimizes maximum deadline lateness ($L^*$) |
| **Pre-aim known angles** | Absorbs rotational slew before un-occlusion ($a_j \to 0$) | Rescues negative-margin knowledge-sensitive corners |
| **Recognize overloaded chokes** | Multiple un-staggered sightlines ($K_{\text{LOS}} \ge 2, \Delta r \to 0$) | Avoid dry gunplay; deploy utility or coordinate team crossfires |
