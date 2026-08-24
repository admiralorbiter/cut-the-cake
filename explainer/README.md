# Tactical Clearability: Interactive Geometry & Scheduling Explainer

A zero-build-step, standalone HTML/SVG/JavaScript visualization suite explaining how level geometry, reticle state, timing, trajectory choice, and prior spatial information determine FPS clearability within the declared scheduling model.

---

## 1. Structure & Entry Points

### 1. Unified Master Research Explainer ([`index.html`](index.html))
The authoritative, single-page interactive research application containing:
- **Sticky Navigation Bar:** Jump directly across all concepts, models, and evidence layers.
- **The 8 Core Concepts Studio:** High-impact studio hub launching the foundational tactical lessons.
- **Visual 1 (Two Rooms Counterexample):** Why static sightline counting ($K_{\text{static}}$) contradicts true temporal clearability.
- **Visual 2 (4-Step Pipeline):** Linking geometry polygons to job releases ($r_j$), deadlines ($D_j$), single-reticle rotational slew ($q_{ij}$), and composable contracts.
- **Visual 3 (Map Knowledge Lab & $\ell^*$):** Interactive discrete response step functions across canonical stimuli (`STIM_06`, `STIM_07`, `STIM_09`, `STIM_11`).
- **Visual 4 (Decoupling Principle):** Proving capacity gain ($\Delta\mathcal{M}$) is decoupled from warning urgency ($\ell^*$).
- **Visual 5 (Tactical Readability Atlas):** Chaptered 12-card spatial contrast explorer with live interactive geometry modulators (route choice, wall sliders, T-junction baffles, entry directions, and modular seams).
- **Visual 6 (Procedural Linter & Evidence Hierarchy):** Empirical proof from 25,000-candidate dungeon sweeps demonstrating the $C \equiv D$ local equivalence theorem and zero runtime simulation overhead.

### 2. The 8 Foundational Visual Concepts ([`concepts/index.html`](concepts/index.html))
Dedicated standalone visual lessons designed to isolate one physical mechanism at a time:
1. [`01-corner-distance.html`](concepts/01-corner-distance.html) — **Corner Distance:** Slicing the pie ($\theta = \text{atan}(x/d)$).
2. [`02-crosshair-placement.html`](concepts/02-crosshair-placement.html) — **Crosshair Placement:** Reticle centering and setup cost ($q = \Delta\theta/\omega$).
3. [`03-stagger-vs-crossfire.html`](concepts/03-stagger-vs-crossfire.html) — **Stagger vs Crossfire:** Release timestamps ($r_j$) breaking simultaneous workload.
4. [`04-clear-order.html`](concepts/04-clear-order.html) — **Priority Order:** Permutation sequencing ($\pi^*$) minimizing lateness ($L^*$).
5. [`05-tactical-margin.html`](concepts/05-tactical-margin.html) — **Tactical Margin:** The stopwatch duel ($\mathcal{M} = -L^*$).
6. [`06-map-knowledge.html`](concepts/06-map-knowledge.html) — **Map Knowledge Lab:** Pre-aiming behind cover before unocclusion ($a_j(\ell)$ and critical lead $\ell^*$).
7. [`07-route-choice.html`](concepts/07-route-choice.html) — **Trajectory Conditioning:** The shortcut thrash trap ($240^\circ$ zigzag) vs smooth outer arc ($60^\circ$).
8. [`08-composition.html`](concepts/08-composition.html) — **From Corner to PCG:** Quiescent seams ($Q_p$) and min-plus matrix composition ($C_{M1} \otimes C_{M2}$).

---

## 2. Technical Design Principles

- **Zero External Dependencies:** Built with pure HTML5, inline SVG, and vanilla JavaScript. Runs completely offline in any modern web browser with no Node.js or framework builds required.
- **Zero Broken Math:** All mathematical expressions render using clean, semantic HTML tags (`<i>`, `<sub>`, `<sup>`, `<b>`, `&gamma;`, `&minus;`, `&rarr;`, `&ge;`, `&le;`).
- **Exact Vector Trigonometry:** Dynamic crosshairs, aiming vectors, and sightline lasers calculate exact angular headings to real target coordinates.
- **Print & PDF Export:** Full support for publication-quality PDF exporting via standard browser print dialog (`window.print()`).

