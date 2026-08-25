# Cut the Cake — Visual Communication & GIF Storyboard

**Goal:** Communicate the core discoveries of *Cut the Cake* in 6–12 second looping animations that require zero audio narration to understand.

**Production Rule:** Every visual asset must answer exactly **one** question and derive its numbers from verified, frozen scientific fixtures.

---

## 1. Visual Asset Portfolio

### Asset 0 — Hero: "A Room Creates a Schedule" ✅ `[PRODUCED]`
- **Files:** [`media/hero_clearability.gif`](media/hero_clearability.gif) | [`media/hero_clearability.webm`](media/hero_clearability.webm)
- **Purpose:** Root README hero, talk slides, social preview.
- **Question:** How does physical architecture turn into a time-sensitive schedule?
- **Source Fixture:** Canonical Family 1 Baffle Stagger (`RepairPop_F1_StaggerDeficit_00`).
- **Storyboard:**
  - `0.0–1.5s`: Top-down corridor. Player approaches corner. Two hidden sentries. Caption: *The map decides when information appears.*
  - `1.5–3.0s`: Threat A un-occludes. Countdown ring appears over Threat A.
  - `3.0–4.0s`: Threat B un-occludes from different angle. Reticle arc rotates to A.
  - `4.0–6.0s`: Timeline below shows release marks ($r_A, r_B$), service windows, and deadlines ($D_A, D_B$).
  - `6.0–8.0s`: Reticle finishes A and sweeps to B. Margin badge displays $\mathcal{M} = +2\text{ tics}$.
  - `Footer`: `Geometry → Timing → Reticle Workload → Tactical Margin`

---

### Asset 1 — "Same Count, Different Fight" ✅ `[PRODUCED]`
- **Files:** [`media/same_count_timing.gif`](media/same_count_timing.gif) | [`media/same_count_timing.webm`](media/same_count_timing.webm)
- **Purpose:** Demonstrating why static enemy counting fails.
- **Question:** Why isn't the number of visible enemies enough to judge difficulty?
- **Source Fixture:** Two Rooms Counterexample (`explainer/data/two_rooms.json`).
- **Storyboard:**
  - `Layout`: Split-screen side-by-side comparison.
  - `Left Pane`: Simultaneous crossfire. 2 threats appear at the exact same tic. Reticle attempts to rotate; deadline fails. Label: *2 Threats — Timing Overload ($\mathcal{M} = -4$)*.
  - `Right Pane`: Staggered partition. 2 threats appear 1.2 seconds apart. Reticle clears first, then second. Label: *2 Threats — Serviceable Sequence ($\mathcal{M} = +3$)*.
  - `Footer`: *Same enemy count. Completely different outcome.*

---

### Asset 2 — "Move One Wall" ✅ `[PRODUCED]`
- **Files:** [`media/move_one_wall.gif`](media/move_one_wall.gif) | [`media/move_one_wall.webm`](media/move_one_wall.webm)
- **Purpose:** Demonstrating automated inverse level repair.
- **Question:** Can a minor architectural edit fix an unserviceable encounter?
- **Source Fixture:** Minimal Repair Optimizer Canonical Case (`results/repair/ROUND_11_4A_FREEZE.md`).
- **Storyboard:**
  - `Phase 1 (Broken)`: Original layout plays. Player peeks corner, simultaneous exposure, deadline breach ($\mathcal{M} = -6\text{ tics}$).
  - `Phase 2 (Repair)`: Wall highlights. Ghost outline translates $+1.10\,\text{m}$ to the right. Green arrow indicates shift.
  - `Phase 3 (Resolved)`: Replay identical player path. Threat 2 un-occlusion is delayed by 8 tics. Reticle clears both comfortably ($\mathcal{M} = +2\text{ tics}$).
  - `Footer`: `Obstacle +1.10 m → Delayed Reveal → Reserve +2 tics`

---

### Asset 3 — "Global Score Can Hide the Choke" ✅ `[PRODUCED]`
- **Files:** [`media/global_vs_local.gif`](media/global_vs_local.gif) | [`media/global_vs_local.webm`](media/global_vs_local.webm)
- **Purpose:** Explaining why Suffix Tactical Margin was developed.
- **Question:** Why isn't a single score for the whole path enough?
- **Source Fixture:** *Dust II* A-Long (`results/m5a_dust2_a_long.json`) or *Transit 213*.
- **Storyboard:**
  - `Main View`: Player traversing long route. Top-right badge shows overall path score ($\mathcal{M}_{\text{global}} = +2$).
  - `Under Player`: Colored route ribbon displays local Suffix Margin ($\mathcal{M}_{\text{suffix}}(s)$).
  - `Decisive Moment`: Player reaches the 2-meter choke. Ribbon pulses bright red ($\mathcal{M}_{\text{suffix}} = -7$), showing the acute danger interval before recovering.
  - `Footer`: *A route can look safe overall while hiding a fatal local choke.*

---

### Asset 5 — "Height Changes Information" ✅ `[PRODUCED]`
- **Files:** [`media/height_reveal.gif`](media/height_reveal.gif) | [`media/height_reveal.webm`](media/height_reveal.webm)
- **Purpose:** Explaining the necessity of 2.5D/3D geometry (Horizon 6).
- **Question:** Why does vertical elevation change tactical clearability?
- **Source Fixture:** M6-B Height-Induced Reveal Fixture (`test_m6b_height_aware_compilation.py`).
- **Storyboard:**
  - `Perspective View`: Dual perspective showing a ground-level path vs. an elevated catwalk path.
  - `Inset`: Top-down 2D map showing identical $(x, y)$ coordinates.
  - `Animation`: Ground player remains blocked by finite-height wall until tic 86. Elevated player sees target over wall at tic 0.
  - `Footer`: *Identical 2D floorplan. Completely different information release.*

### Asset 4 — "The Model Can Say No"
- **Purpose:** Showing that the model does not hallucinate false solutions.
- **Question:** Does the algorithm always find an easy way to walk through a room?
- **Source Fixture:** *Dust II* Upper B-Tunnels exit (`results/m5b_cross_section.json`).
- **Storyboard:**
  - `Path A (Left Exit)`: Player crosses threshold. Immediate multi-angle exposure. Margin collapses to $\mathcal{M} = -7$.
  - `Path B (Right Exit)`: Player crosses threshold along opposite wall. Same simultaneous collapse ($\mathcal{M} = -7$).
  - `Conclusion`: Linter badge stamps: *NO DRY GUNPLAY SOLUTION*.
  - `Footer`: *A verified model must be able to reject the premise.*

---

### Asset 5 — "Height Changes Information"
- **Purpose:** Explaining the necessity of 2.5D/3D geometry (Horizon 6).
- **Question:** Why does vertical elevation change tactical clearability?
- **Source Fixture:** M6-B Height-Induced Reveal Fixture (`test_m6b_height_aware_compilation.py`).
- **Storyboard:**
  - `Perspective View`: Dual perspective showing a ground-level path vs. an elevated catwalk path.
  - `Inset`: Top-down 2D map showing identical $(x, y)$ coordinates.
  - `Animation`: Ground player remains blocked by finite-height wall until tic 86. Elevated player sees target over wall at tic 0.
  - `Footer`: *Identical 2D floorplan. Completely different information release.*

---

### Asset 6 — "3D Change, Same Discrete Outcome"
- **Purpose:** Demonstrating simulation clock quantization.
- **Question:** Why doesn't every geometric change alter tactical difficulty?
- **Source Fixture:** *Valorant* Ascent A-Site Pitch Quantization Null (`test_m6a_elevation_aim_scheduling.py`).
- **Storyboard:**
  - `Visual`: Target elevation raises from $0^\circ \to 5.35^\circ$.
  - `Reticle Work`: Slew cost meter shows required pitch transition.
  - `Quantization Bucket`: $5.35^\circ \le 10.29^\circ/\text{tic} \implies 1\text{ tic}$.
  - `Outcome`: Schedule and Tactical Margin remain identically $\mathcal{M} = -1$.
  - `Footer`: *Geometry changed. Discrete timing bucket did not.*

---

### Asset 7 — "The Schedule Actually Executes"
- **Purpose:** Proving that Tactical Margin is an executable contract.
- **Question:** Is Tactical Margin just theoretical math, or can an agent execute it?
- **Source Fixture:** M6-C Multi-Threat 3D Execution Fixture (`test_m6c_controller_3d_execution.py`).
- **Storyboard:**
  - `3D View`: 3D agent moves along path, aiming via spherical geodesic arcs.
  - `Timeline`: Predicted schedule markers ($C_1, C_2, C_3$).
  - `Execution Events`: Physical `SERVICE_COMPLETE` pulses fire exactly on schedule markers ($t_j^{\text{event}} \equiv C_j - 1$).
  - `Footer`: *Predicted schedule = realized 3D controller execution.*

---

### Asset 8 — The Evidence Ladder
- **Purpose:** Visual summary of research rigor and prospective boundaries.
- **Type:** Static SVG / Lightly Animated Infographic.
- **Content:** The 7-tier ladder from Formal Dioid Algebra to Prospective Human Calibration.

---

## 2. Capture Implementation Specification

In **Pass 2**, visual assets will be rendered directly from verified Python test fixtures using a dedicated capture script:

```
tools/
└── communication_capture.py    # Deterministic headless frame capture & ffmpeg GIF assembler
docs/
└── media/
    ├── README.md               # Asset manifest & format specifications
    ├── hero_clearability.gif   # Asset 0
    ├── same_count_timing.gif   # Asset 1
    ├── move_one_wall.gif       # Asset 2
    ├── global_vs_local.gif     # Asset 3
    ├── model_says_no.gif       # Asset 4
    ├── height_reveal.gif       # Asset 5
    ├── quantization_null.gif   # Asset 6
    ├── execution_parity.gif    # Asset 7
    └── static/
        ├── evidence_ladder.svg
        └── pipeline_diagram.svg
```

### Video & GIF Encoding Standards
- **GIF Resolution:** `1200 x 675` (16:9) or `1000 x 750` (4:3).
- **Framerate:** 20 fps, optimized with Lanczos scaling and global color palettes.
- **WebM Video:** H.264 / VP9 high quality for documentation websites and fast browser loading.

---

## 3. Visual Review Checklist

Before any visual asset is published, it must pass this checklist:
- [ ] **Instant takeaway:** Can a non-gamer state the main conclusion in 10 seconds without audio?
- [ ] **Single message:** Does the animation focus on exactly one concept?
- [ ] **Authoritative numbers:** Are all timestamps, angles, and margins derived directly from frozen fixtures?
- [ ] **No client-side math:** Does the animation render true telemetry rather than recomputing approximations?
- [ ] **No unexplained jargon:** Are symbols clearly labeled (e.g. *Reserve Time* instead of raw $\mathcal{M}$)?
- [ ] **Honest representation:** Are negative and null results highlighted with equal prominence?
