# Cut the Cake 🍰

**Composable Tactical Clearability Contracts and Automated Level Repair for Procedural First-Person Shooters**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 74 Passed](https://img.shields.io/badge/tests-74%20passed-brightgreen.svg)]()

---

## Overview

In competitive first-person shooter (FPS) level design, procedural generation faces a fundamental legibility barrier. While graph grammars and tile synthesis algorithms guarantee topological reachability, dynamically assembled environments frequently degenerate into chaotic, multi-angle crossfires where skilled tactical play collapses into unmanageable gambling.

**Cut the Cake** formalizes the tactical doctrine of **"Slicing the Pie"** (sequential angle isolation) as a **non-preemptive single-machine real-time scheduling problem ($1 \mid r_j, s_{ij} \mid L_{\max}$)**, where the player's single reticle acts as a stateful processor bottleneck.

### Core Capabilities:
1. **Geometry-to-Contract Compilation:** Automatically compiles continuous 2D polygonal map geometry into discrete angular transfer matrices over $(\min, +)$ dioid algebra via critical-LOS ray-vertex bisection ($< 0.1\,	ext{ms}$).
2. **Tactical Margin ($\mathcal{M} = -L^*$):** Computes the exact temporal reserve before hostile deadline breach, separating solvable sequential clears from lethal crossfire traps.
3. **Inverse Tactical Repair ($G 	o G^*$):** Given an unserviceable room ($\mathcal{M} < 0$), isolates the critical scheduling bottleneck and synthesizes minimal geometric perturbations ($\Delta x \le 0.90\,	ext{m}$) to guarantee $\mathcal{M}(G^*) \ge \epsilon$.
4. **External Game Engine Verification (ViZDoom):** Validated across $9,000$ simulation episodes and $72$ native C++ Doom WAD micro-arenas, proving that repaired layouts flip from fatal engine deaths to guaranteed survival.

---

## Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/admiralorbiter/cut-the-cake.git
cd cut-the-cake

# Install package in editable mode
pip install -e .
```

### Running the Test Suite (74 Verification Gates)

```bash
pytest -v
```

### Running the Inverse Repair Benchmark

```bash
python -m cut_the_cake.repair_benchmark
```

---

## Repository Structure

```
cut-the-cake/
├── src/cut_the_cake/           # Core Python engine, compiler, schedulers, and repair optimizer
├── tests/                      # 74 comprehensive unit, PCG, and native ViZDoom tests
├── paper/                      # Academic manuscript, SVGs, and BibTeX references
│   ├── manuscript.md
│   ├── references.bib
│   └── figures/
├── results/                    # Machine-readable benchmark data & summary tables
│   ├── round11s/               # 9,000-episode discrete simulation benchmark
│   ├── vizdoom/                # Native C++ ViZDoom bridge verification
│   ├── actionability-lead/     # Critical lead sweeps & threshold transitions
│   └── repair/                 # 50-arena population repair benchmark
├── explainer/                  # Interactive visual web explainer suite
└── human/                      # Prospective pilot protocol and telemetry instrument
```

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
