# Cut the Cake — Media Assets Directory

This directory contains the canonical visual loops, animations, and vector infographics generated for the *Cut the Cake* research project.

---

## 🎞️ Active Visual Assets (`docs/media/`)

| Asset ID | Title | Provenance Class | Source Fixture | Deliverables |
| :--- | :--- | :--- | :--- | :--- |
| **`adv01_three_vs_two`** | ADV-01: Three Threats Are Easier Than Two | `EVIDENCE_REPLAY` | `M08_HighConcurrencySolvable` vs `M11_RapidCrossfireAperture` | [`.gif`](adv01_three_vs_two.gif) \| [`.webm`](adv01_three_vs_two.webm) |
| **`hero_clearability`** | Hero: A Room Creates a Schedule | `EVIDENCE_REPLAY` | Canonical F1 Stagger Deficit (`RepairPop_F1_StaggerDeficit_00`) | [`.gif`](hero_clearability.gif) \| [`.webm`](hero_clearability.webm) |
| **`same_count_timing`** | Same Count, Different Timing | `ILLUSTRATIVE_EXPLAINER` | Simultaneous Crossfire vs Staggered Baffle | [`.gif`](same_count_timing.gif) \| [`.webm`](same_count_timing.webm) |
| **`move_one_wall`** | Minimal Geometric Repair in Action | `EVIDENCE_REPLAY` | Canonical F1 Auto-Fix Search (`ROUND_11_4A_FREEZE`) | [`.gif`](move_one_wall.gif) \| [`.webm`](move_one_wall.webm) |
| **`global_vs_local`** | Global Route Score vs Local Suffix Margin | `ILLUSTRATIVE_EXPLAINER` | Choke Transition Counterfactual Suffix | [`.gif`](global_vs_local.gif) \| [`.webm`](global_vs_local.webm) |
| **`height_reveal`** | Height Changes Information | `EVIDENCE_REPLAY` | M6-B Height-Induced Reveal Fixture | [`.gif`](height_reveal.gif) \| [`.webm`](height_reveal.webm) |

---

## 📊 Static Vector Infographics (`docs/media/static/`)

- [**`evidence_ladder.svg`**](static/evidence_ladder.svg): 7-tier scientific hierarchy separating formal dioid algebra, simulation validation, engine transfer, and prospective human boundaries.
- [**`pipeline.svg`**](static/pipeline.svg): Geometry-to-contract compilation, real-time scheduling, spatial diagnosis, and closed-loop inverse repair pipeline.

---

## ⚙️ Provenance & Generation

All media files are generated deterministically via:

```bash
python tools/communication_capture.py
```

Metadata schema is maintained in [`capture_manifest.json`](capture_manifest.json).
