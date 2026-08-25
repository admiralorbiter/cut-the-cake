# Cut the Cake — Practical Application Guide for Level Designers & Developers

**Target Audience:** Level designers, gameplay programmers, PCG engineers, and combat balance teams building or analyzing competitive first-person shooter environments.

*(For player-focused tactical intuitions derived from the model, see [**docs/MODEL_DERIVED_PLAYER_INTUITIONS.md**](MODEL_DERIVED_PLAYER_INTUITIONS.md).)*

<p align="center">
  <img src="media/static/pipeline.svg" alt="Tactical CAD Pipeline Architecture" width="850" />
</p>

---

## 1. Compile-Time Tactical Level Linting

### The Problem
Traditional competitive level development relies on extensive, expensive human playtesting to discover problematic multi-angle crossfires, ambiguous sightlines, and degenerate chokes.

### The Solution
Cut the Cake compiles 2D and 2.5D gray-box geometry into exact information-release schedules in **under 0.1 milliseconds per room**. This enables automated tactical linting directly inside level editor plugins or continuous integration (CI/CD) pipelines.

```
[Author Gray-Box Geometry] ──> [Run Geometric Compiler] ──> [Deterministic Labels]
                                                                    │
         ┌──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┐
         ▼                                                          ▼                                                          ▼
  Blind-Clearable (M_reveal >= 0)                            Knowledge-Rescuable                                        Structurally Overloaded (M_preaim < 0)
  Ship or certify for ranked play                            Add visual cues, signage, or adjust lighting               Flag for auto-repair or geometric redesign
```

<p align="center">
  <img src="media/global_vs_local.gif" alt="Suffix Tactical Margin Heatmap" width="750" />
</p>

---

## 2. One-Click Automated Level Repair

When a room transition is flagged as structurally overloaded ($\mathcal{M} < 0$):

1. **Bottleneck Diagnosis:** The diagnostic engine identifies the **controlling occluder**—the specific obstacle boundary responsible for the simultaneous un-occlusion.
2. **Constrained Search:** The `MinimalRepairOptimizer` evaluates translations across declared operator sets ($\mathcal{T}_{\text{obs}}$) along discrete grid steps ($0.05\,\text{m}$).
3. **Safety Cushion Certification:** It identifies the minimal geometric displacement $d^*$ that guarantees $\mathcal{M}(G^*) \ge +2\text{ tics}$ ($+57\,\text{ms}$ safety cushion).
4. **Interactive Review:** Level designers inspect the proposed ghost obstacle in the CAD workbench and accept, reject, or fine-tune the change.

<p align="center">
  <img src="media/move_one_wall.gif" alt="Automated Level Repair" width="750" />
</p>

### Benchmark Performance
- **80.0%** of verified unserviceable benchmark rooms were repaired by shifting a single obstacle.
- Median required displacement was **$0.85\,\text{m}$** (preserving original architectural aesthetics).
- **75.0%** of source-model repairs transferred successfully to native game engine survival (*ViZDoom*).

---

## 3. Procedural Content Generation (PCG) & Modular Assembly

When assembling procedural dungeons or modular arenas from room prefabs:

### The Boundary Spill Problem
Two room modules may be individually fair when tested in isolation, but can create fatal crossfires when stitched together if sightlines bleed across doorways.

### Min-Plus Transfer Matrices ($C \equiv D$ Theorem)
Each module compiles into an algebraic **transfer matrix** over $(\min, +)$ dioid algebra:
- Matrices compose associatively via min-plus matrix multiplication: $C_{\text{global}} = C_1 \otimes C_2 \otimes \dots \otimes C_n$.
- When doorways feature **quiescent reset zones** (corridors shielded from internal sightlines), **global level clearability is mathematically equivalent to local module clearability**.
- Level generators can guarantee full-dungeon fairness at assembly time with **zero runtime simulation overhead**.

---

## 4. Tuning Difficulty via Capability Envelopes ($\mathcal{C}(G)$)

Rather than treating fairness as a binary property, designers can calculate the **Capability Envelope** $\mathcal{C}(G)$ required by a given layout:

$$\omega^* = \inf \{ \omega : \mathcal{M}(\omega) \ge 0 \}, \quad A^* = \sup \{ A : \mathcal{M}(A) \ge 0 \}$$

| Design Application | Implementation |
| :--- | :--- |
| **Matchmaking Difficulty Tiers** | Tag maps by required sensorimotor thresholds. Casual playlists receive wide-margin layouts; ranked esports receive tight-tolerance corridors. |
| **Dynamic PCG Adaptation** | Automatically shift obstacle positions to match the player's matchmaking rank (MMR). |
| **Accessibility Auditing** | Quantify how widening enemy reaction budgets ($D_j$) by $+50\,\text{ms}$ or adding high-contrast visual indicators rescues borderline transitions. |

---

## 5. Tactical CAD Workbench Integration

The repository includes a web-based Tactical CAD workbench for live interactive editing:

```bash
python -m cut_the_cake.cad_server --port 5000
```

Open `http://127.0.0.1:5000` to:
- Drag walls, partitions, and crates interactively with grid snapping.
- Inspect real-time sub-millisecond Suffix Tactical Margin ribbons along player paths.
- Trigger automated **Auto-Fix** proposals (`[A]` key) and review before/after diffs.
- Inspect dynamic 3D line-of-sight rays and pitch/azimuth reticle telemetry.
