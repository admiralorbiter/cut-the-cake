# ~90-Second Narrated Demo Script: Tactical Clearability

**Target Audience:** Game Developers, Computational Level Designers, AI/Robotics Researchers, Conference Attendees  
**Total Runtime:** ~85–90 seconds  
**Visual Format:** Screen recording of the interactive explainer + native ViZDoom engine split-screen

---

## Storyboard & Narration Breakdown

### [00:00 – 00:15] The Hook: Reachability is Not Playability
- **Visual:** Split screen of *Room A* (Blind-Spot Trap) vs. *Room B* (Staggered Slices). A level generation algorithm places walls and doors.
- **Voiceover:**
  > *"When procedural level generators make a shooter map, they check if doors connect and count how many sightlines open at once. But counting static sightlines predicts the wrong outcome twice."*
- **On-Screen Text / Cue:** Highlight $K_{\text{static}} \le 2$ (Pass) on Room A, then show the unserviceable deadline failure.

---

### [00:15 – 00:35] The Computational Insight: Level Geometry is a Scheduling Problem
- **Visual:** The 4-panel pipeline animating in real-time ($Geometry \to Raycasting \to Reticle \to Schedulability$).
- **Voiceover:**
  > *"Every obstacle corner acts as an information shutter. When a threat appears, the player’s single crosshair has to physically rotate, acquire the target, and fire before the hostile combat deadline expires. Level geometry is a single-machine real-time scheduling problem with sequence-dependent setup times."*
- **On-Screen Text / Cue:** Highlight the reticle rotation arc ($\Delta\theta / \omega_{\text{aim}}$) and the deadline bar ($D_j = r_j + n_j$).

---

### [00:35 – 00:55] The $\ell^*$ Actionability Lead: How Much Warning Saves Your Life?
- **Visual:** The Map Knowledge Slider in Section 3 of the Explainer being dragged from $\ell = 0$ to $\ell = 4\,\text{tics}$ ($114\,\text{ms}$) on **STIM_07** (Spaced Baffle). Dynamic $\mathcal{M}(\ell)$ step curve climbs across the zero-line.
- **Voiceover:**
  > *"Take this blind corner in STIM_07. With zero advance warning, the player is late by 4 tics. Give them 86 milliseconds of information: the source model is still one tic short. Give them 114 milliseconds: the reticle pre-aligns during traversal, crossing the mathematical feasibility boundary at $\mathcal{M} = 0$."*
- **On-Screen Text / Cue:** 
  - $\ell = 0\,\text{ms} \to \text{UNSERVICEABLE } (\mathcal{M} = -4\,\text{tics})$
  - $\ell = 86\,\text{ms} \to \text{UNSERVICEABLE } (\mathcal{M} = -1\,\text{tic})$
  - $\ell = 114\,\text{ms} \to \textbf{FEASIBILITY BOUNDARY } (\mathcal{M} = 0, \ell^*_{\text{source}} = 114\,\text{ms})$

---

### [00:55 – 01:15] Native Game Engine Boundary Tracking
- **Visual:** Display the Three-Stage Threshold Decomposition table side-by-side with native C++ ViZDoom gameplay recordings across the 4 boundary-crossing fixtures.
- **Voiceover:**
  > *"A real game engine introduces small spatial translation and discrete motor execution effects. When we compiled these encounters into native C++ ViZDoom, the observed game engine survival transition tracked our source scheduling model to within a single 35-Hz logic tic—28.6 milliseconds."*
- **On-Screen Text / Cue:** 
  - *Three-Stage Threshold Sequence: $\ell^*_{\text{source}} \to \ell^*_{\text{engine-model}} \to \ell^*_{\text{survival}}$*
  - *Observed Engine Survival Agreement: $|\Delta \ell^*| \le 1\,\text{tic}$ ($28.6\,\text{ms}$) across all 4 fixtures.*

---

### [01:15 – 01:30] Conclusion: The Human Question
- **Visual:** Transition from the composable transfer matrix $\mathcal{C}_M$ to the clear question banner over the room floorplan.
- **Voiceover:**
  > *"So instead of asking only whether a generated room is connected, we can ask whether it gives the player enough information, early enough, to actually act."*
- **On-Screen Final Card:**
  - **HOW EARLY DO YOU NEED TO KNOW WHERE TO AIM?**
  - $\ell^* = 114\,\text{ms}$
  - `github.com/admiralorbiter/bigbraintime` · *Tactical Clearability in FPS PCG*
