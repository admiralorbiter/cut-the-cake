# Start Here: Navigating Cut the Cake 🍰

Welcome to **Cut the Cake**. This guide helps you find the right entry point based on your background and what you want to learn.

<p align="center">
  <img src="media/hero_clearability.gif" alt="Cut the Cake Clearability Hero Loop" width="750" />
</p>

---

## Choose Your Path

| Who You Are | What You Want | Start With | Next Step |
| :--- | :--- | :--- | :--- |
| **Non-Gamer / General Adult** | A clear, non-technical explanation of the core idea and why geometry controls information flow. | [**One-Page Overview**](ONE_PAGE_OVERVIEW.md) | [**What We Discovered**](WHAT_WE_DISCOVERED.md) |
| **Level / Game Designer** | Practical tools to lint sightlines, fix multi-angle crossfires, and build readable competitive maps. | [**What We Discovered**](WHAT_WE_DISCOVERED.md) | [**Practical Application Guide**](PRACTICAL_APPLICATION_GUIDE.md) & [**Tactical CAD Demo**](../README.md#launching-the-tactical-cad-workbench) |
| **Researcher / Academic** | Theoretical foundations, formal proofs, verification ladder, and scientific limits. | [**Evidence & Limits**](EVIDENCE_AND_LIMITS.md) | [**Academic Manuscript**](../paper/manuscript.md) |
| **Software Engineer** | Code architecture, schemas, real-time schedulers, and reproduction scripts. | [**README Quickstart**](../README.md#quickstart--installation) | [**Product Roadmap**](../ROADMAP.md) & [**Test Suite**](../README.md#running-the-test-suite) |
| **Competitive FPS Player** | Understanding corner distance, pre-aiming value, clearing orders, and movement angles. | [**Visual Explainer**](../explainer/index.html) | [**Model-Derived Player Intuitions**](MODEL_DERIVED_PLAYER_INTUITIONS.md) |

---

## The 30-Second Summary

**Cut the Cake** asks a simple question:
> *Does the physical geometry of a virtual room reveal threats at a pace that a single human decision-maker can actually process?*

- **The Crosshair as a Bottleneck:** A player has only one aiming reticle and can only process one threat at a time. Rotating between angles takes time.
- **Geometry Creates a Schedule:** Walls, corners, and elevation control *when* threats become visible (release times) and *when* they react (deadlines).
- **Tactical Margin ($\mathcal{M}$):** The mathematical reserve time remaining before a hostile deadline is breached. Positive margin means the encounter is clearable; negative margin means an unavoidable deadline failure.
- **Automated Repair:** When an encounter fails, the system can calculate minimal physical shifts (e.g. moving a wall by $1.10\,\text{m}$) to delay reveals and restore positive margin.

---

## Core Document Directory

- [**ONE_PAGE_OVERVIEW.md**](ONE_PAGE_OVERVIEW.md): Plain-language summary using an alarm/deadline analogy. Zero gaming jargon required.
- [**WHAT_WE_DISCOVERED.md**](WHAT_WE_DISCOVERED.md): Synthesis of 11 findings, falsifications, and surprises across the research.
- [**EVIDENCE_AND_LIMITS.md**](EVIDENCE_AND_LIMITS.md): Structured 7-tier evidence ladder and clear statement of what is and is not proven.
- [**MODEL_DERIVED_PLAYER_INTUITIONS.md**](MODEL_DERIVED_PLAYER_INTUITIONS.md): Player-facing tactical takeaways with clear model-scope qualifiers.
- [**PRACTICAL_APPLICATION_GUIDE.md**](PRACTICAL_APPLICATION_GUIDE.md): Developer and level designer guide for compile-time linting, automated repair, and CAD integration.
- [**VISUAL_STORYBOARD.md**](VISUAL_STORYBOARD.md): Storyboards for the 8 canonical visual animations and media assets.
- [**ROADMAP.md**](../ROADMAP.md): Multi-horizon strategic roadmap spanning Horizon 0 through Horizon 8.
- [**paper/manuscript.md**](../paper/manuscript.md): Full academic research paper.
