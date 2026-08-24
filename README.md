# Cut the Cake 🍰

**Composable Tactical Clearability Contracts and Automated Level Repair for Procedural First-Person Shooters**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 80 Passed](https://img.shields.io/badge/tests-80%20passed-brightgreen.svg)]()
[![Freeze: Round 11.4A](https://img.shields.io/badge/scientific%20core-Round%2011.4A%20Frozen-blue.svg)](results/repair/ROUND_11_4A_FREEZE.md)

---

## Product Vision & Scientific Foundation

The long-term **North Star** for this project is a **Tactical CAD Platform** for competitive shooter level design—an interactive authoring instrument that analyzes sightlines, compiles clearability schedules, flags unfair multi-angle crossfires, and offers automated geometric repairs in real time.

See [**ROADMAP.md**](ROADMAP.md) for the multi-horizon product development plan.

The current Python repository forms the **verified scientific core (Horizon 0)** underneath that future platform. It provides the mathematical theory, polynomial-time polygon-to-contract compiler, single-machine real-time scheduling solvers, and external game-engine validation bridges.

---

## Overview

In competitive first-person shooter (FPS) level design, procedural generation faces a fundamental legibility barrier. While graph grammars and tile synthesis algorithms guarantee topological reachability, dynamically assembled environments frequently degenerate into chaotic, multi-angle crossfires where skilled tactical play collapses into unmanageable gambling.

**Cut the Cake** formalizes the tactical doctrine of **"Slicing the Pie"** (sequential angle isolation) as a **non-preemptive single-machine real-time scheduling problem ($1 \mid r_j, s_{ij} \mid L_{\max}$)**, where the player's single reticle acts as a stateful processor bottleneck.

### Core Capabilities:
1. **Geometry-to-Contract Compilation:** Automatically compiles continuous 2D polygonal map geometry into discrete angular transfer matrices over $(\min, +)$ dioid algebra via critical-LOS ray-vertex bisection ($< 0.1\,\text{ms}$).
2. **Tactical Margin ($\mathcal{M} = -L^*$):** Computes the exact temporal reserve before hostile deadline breach, separating solvable sequential clears from lethal crossfire traps.
3. **Inverse Tactical Repair ($G \to G^*$):** Given an unserviceable room ($\mathcal{M} < 0$), isolates the critical scheduling bottleneck and synthesizes grid-minimal geometric translations ($d^* \approx 0.85\,\text{m}$) over declared operator sets to guarantee source $\mathcal{M}(G^*) \ge \epsilon$.
4. **External Engine Transfer Validation (ViZDoom):** Validated across $9,000$ discrete simulation episodes and an audited 50-arena unserviceable benchmark in headless C++ Doom, achieving **80.0% source-model repair**, **60.0% native ViZDoom rescue**, and **75.0% engine transfer efficiency** with full three-layer residual decomposition.

---

## Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/admiralorbiter/cut-the-cake.git
cd cut-the-cake

# Install package in editable mode (with optional CAD server dependencies)
pip install -e ".[cad]"
```

### Running the Test Suite

```bash
# Run full test suite (96 tests at current HEAD)
pytest -v
```

> **Note on Verification**: The frozen scientific core contains **80 tests** tagged at `round11.4a-freeze`. Current HEAD contains **96 tests** including Tactical CAD scene manifest schemas, adapter parity, live X-axis wall drag sweeps, deadline regression audits, and Flask CAD server endpoints.

### Launching the Tactical CAD Workbench (Milestone 2A)

```bash
python -m cut_the_cake.cad_server --port 5000
```
Open `http://127.0.0.1:5000/` in any modern web browser to interactively drag arena obstacles and inspect real-time authoritative Tactical Margin calculations.

### Running the Canonical Inverse Repair Benchmark (Round 11.4A)

```bash
python -m cut_the_cake.repair_benchmark
```

See [**ROUND_11_4A_FREEZE.md**](results/repair/ROUND_11_4A_FREEZE.md) for the frozen scientific evidence and reproduction protocol.

---

## Repository Structure

```
cut-the-cake/
├── src/cut_the_cake/           # Core Python engine, compiler, schedulers, adapter, and CAD server
├── tests/                      # 96 comprehensive unit, PCG, ViZDoom, and CAD adapter tests
├── cad/                        # Tactical CAD schemas, exports, and top-down 2D playback client
├── paper/                      # Academic manuscript, SVGs, and BibTeX references
│   ├── manuscript.md
│   ├── references.bib
│   └── figures/
├── results/                    # Machine-readable benchmark data & summary tables
│   ├── round11s/               # 9,000-episode discrete simulation benchmark
│   ├── vizdoom/                # Native C++ ViZDoom bridge verification
│   ├── actionability-lead/     # Critical lead sweeps & threshold transitions
│   └── repair/                 # 50-arena population repair benchmark & freeze certificate
├── explainer/                  # Interactive visual web explainer suite
└── human/                      # Prospective pilot protocol and telemetry instrument
```

## Guides & Documentation

- [**Plain-Language Paper Overview**](docs/PLAIN_LANGUAGE_GUIDE.md) — Non-technical explanation of the core research and key findings.
- [**Practical Application Guide**](docs/PRACTICAL_APPLICATION_GUIDE.md) — Concrete guidance for FPS players (how to read fights, when to pre-aim, clearing order) and level designers/developers (compile-time linting, automated repair, PCG, difficulty tuning).
- [**Interactive Visual Explainer**](explainer/index.html) — 8-module browser explainer with interactive corner, reticle, and scheduling widgets.
- [**Product Roadmap**](ROADMAP.md) — Multi-horizon tactical CAD platform roadmap.
- [**Scientific Manuscript**](paper/manuscript.md) — Full formal research paper.

---

## Interactive Visual Explainer

The repository includes a complete interactive visual explainer at `explainer/index.html`. Open it directly in any modern browser:

```bash
# Open in browser (Windows PowerShell)
Start-Process explainer/index.html
```

---

## Citation

```bibtex
@article{cutthecake2026,
  title={From Reachable to Readable: Composable Tactical Clearability Contracts for Procedural First-Person Shooter Levels},
  author={Big Brain Time Research Collective},
  journal={arXiv preprint},
  year={2026}
}
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
