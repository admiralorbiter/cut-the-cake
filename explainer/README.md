# Tactical Clearability: Interactive Geometry & Scheduling Explainer

A zero-build-step, standalone HTML/SVG/JavaScript visualization explaining how level geometry, reticle state, timing, and prior spatial information determine FPS clearability within the declared model.

---

## 1. Two Ways In

### Guided Explainer v2 — player intuition → research math

Open [`guided/index.html`](guided/index.html) for the recommended first-time learning path. It is organized as eight lessons:

1. **Angles / Slice the Pie** — why stand-off distance changes angular reveal.
2. **Crosshair Placement** — reticle state as angular setup cost.
3. **Geometry Creates Time** — visibility release timestamps and deadlines.
4. **Which Angle First?** — interactive target-order scheduling.
5. **Tactical Margin** — $L^*$ and $\mathcal{M}=-L^*$.
6. **Map Knowledge** — actionability $a_j(\ell)$ and critical lead $\ell^*$.
7. **Level Design** — route, wall, baffle, and entry-state effects.
8. **PCG Composition** — state-conditioned transfer contracts and min-plus composition.

The guided page deliberately uses paired vocabulary: familiar FPS concepts first, then the corresponding research construct. Its Angle School and clear-order exercises are pedagogical toy models; links take the reader into the canonical Atlas and frozen research artifacts when the lesson reaches those claims.

### Full Research Explainer / Tactical Readability Atlas

Open [`index.html`](index.html) for the complete interactive research explainer, including the Two Rooms counterexamples, geometry-to-schedule pipeline, canonical $\ell^*$ knowledge slider, decoupling result, 12-layout Tactical Readability Atlas, evidence ladder, and printable/PDF presentation surface.

No compilation, local Node server, or external build step is required for either experience.

---

## 2. Core Interactive Features

- **Counterexample Gallery ($K_{\text{static}}$ disagreement):** demonstrates why static sightline counts can fail in both directions.
- **Geometry → Schedule Pipeline:** links occlusion geometry to releases $r_j$, deadlines $D_j$, sequence-dependent slew $q_{ij}$, acquisition $A$, service $p_j$, and Tactical Margin.
- **Critical Actionability Lead ($\ell^*$):** uses the frozen discrete curves for the four canonical knowledge-rescuable stimuli (`STIM_06`, `STIM_07`, `STIM_09`, `STIM_11`).
- **Tactical Readability Atlas:** chaptered spatial contrasts covering threat count, route choice, exact wall perturbation sweeps, T-junctions, entry state, prior knowledge, overload, modular seams, and taxonomy.
- **Publication/print output:** the full explainer includes print/PDF-oriented styling and publication graphics.

---

## 3. Evidence Boundary

The explainer distinguishes instructional illustrations from frozen research evidence. Model verdicts are statements about the declared fixed-route/player/actionability abstraction. Human claims remain hypotheses until empirical player data are collected; the site should not equate model clearability with subjective fairness or universal human performance.
