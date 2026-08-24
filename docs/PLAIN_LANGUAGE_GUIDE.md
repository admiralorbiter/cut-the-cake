# Cut the Cake — Plain-Language Overview & Practical Usage Guide

---

## Part 1: The Research Paper in Plain Language

### 1. What Problem Does This Solve?
Every competitive shooter player knows this moment: you step around a corner and find three enemies looking at you from three completely different angles. Even if your aim is world-class, you can only shoot one at a time. The other two kill you before your crosshair can physically rotate over to them. You die feeling cheated—because the encounter was literally unwinnable.

Modern procedural level generators (algorithms that build random maps) are great at ensuring rooms connect and floors are walkable. But they have **zero understanding of whether a room is actually fightable**. They frequently generate geometry that exposes players to multiple lethal angles at the exact same millisecond. 

The paper formalizes this missing dimension as **tactical clearability**: moving from *"Can the player walk here?"* (reachability) to *"Can a player acquire and shoot every threat without being forced into an unwinnable gamble?"* (readability).

---

### 2. The Core Insight: Your Crosshair is a Single-Threaded CPU
The paper’s core mathematical insight is simple: **your crosshair behaves exactly like a single-core computer processor.**

* You can only process **one target at a time** (non-preemptive single machine).
* Turning your aim between angles takes time (sequence-dependent setup cost $q_{ij} = \Delta\theta / \omega$).
* Enemies become visible as you move through doorways (release times $r_j$).
* Each enemy will shoot you after a reaction window (deadlines $D_j = r_j + n_j$).

```text
[The Single-Reticle Bottleneck]

         ┌────────────────┐
         │  Unocclusion   │ ──> Target 1 appears (Release timestamp r₁)
         └───────┬────────┘
                 │
                 ▼
         ┌────────────────┐
         │ Reticle Slew   │ ──> Crosshair rotates to bearing θ₁ (Setup cost q)
         └───────┬────────┘
                 │
                 ▼
         ┌────────────────┐
         │ Target Service │ ──> Acquire (A = 150ms) + Fire Dwell (p = 100ms)
         └───────┬────────┘
                 │
                 ▼
     Must finish BEFORE Enemy Reaction Deadline (D₁ = r₁ + n₁) !
```

---

### 3. What is "Tactical Margin" ($\mathcal{M}$)?
By calculating the optimal clearing order ($\pi^*$), the system computes a single number called **Tactical Margin** ($\mathcal{M} = -L^*$):

* **$\mathcal{M} \ge 0$ (Clearable):** An optimal player has enough time to acquire and neutralize every enemy before any enemy can shoot back.
* **$\mathcal{M} < 0$ (Lethal Trap):** The room is mathematically unsolvable within the movement and aim model. At least one enemy will breach their reaction deadline before you can finish aiming.

---

### 4. What About Map Knowledge (Pre-Aiming)?
The paper proves that a room's fairness depends heavily on the player's information state:

1. **Blind Clearing ($\mathcal{M}_{\text{reveal}}$):** You have never seen the map before. You can only start turning your crosshair *after* an enemy visually appears ($a_j = r_j$).
2. **Pre-Aim Clearing ($\mathcal{M}_{\text{preaim}}$):** You know the map by heart. You can pre-rotate your crosshair behind the wall toward the exact angle where the enemy will be ($a_j = 0$).

The difference between these two values is the **Tactical Value of Map Knowledge** ($\Delta\mathcal{M}_{\text{knowledge}} = \mathcal{M}_{\text{preaim}} - \mathcal{M}_{\text{reveal}}$). It measures how much advance map memory rescues an otherwise lethal room.

---

### 5. Key Research Numbers at a Glance

| Metric | Measured Value | What It Proves |
| :--- | :---: | :--- |
| **Discrete Simulation Benchmark** | **9,000 episodes** | Tested across 60 arenas; Tactical Margin achieved **$\text{AUC} = 1.0000$**, outperforming raw sightline counting by **+19%**. |
| **Native Game Engine Validation** | **ViZDoom (C++ Doom)** | Mean timing discrepancy between the math model and real Doom physics was only **$24\,\text{ms}$ ($0.83\,\text{tics}$)**. |
| **Inverse Level Repair** | **80.0% Success** | On 50 verified death-trap rooms, nudging a single obstacle by just **$0.85\,\text{m}$** converted the layout into a fair, clearable fight. |
| **PCG Compile-Time Linter** | **25,000 candidates** | Evaluated dungeon module assemblies with **0 false certifications** at compile time. |

---
---

## Part 2: How Players and Developers Can Use This System

---

### 🎮 For Players: How to Use This Info to Win Fights

#### 1. Diagnose Why You Died (Skill Issue vs. Broken Geometry)
When you die peeking a corner, you can categorize the encounter:
* **Blind-Clearable ($\mathcal{M}_{\text{reveal}} \ge 0$):** Fair fight. You missed a shot, reacted slowly, or cleared in the wrong sequence.
* **Knowledge-Rescuable ($\mathcal{M}_{\text{reveal}} < 0, \mathcal{M}_{\text{preaim}} \ge 0$):** You died because you didn't know the angle. You *must* pre-aim this corner behind cover before peeking.
* **Structurally Overloaded ($\mathcal{M}_{\text{preaim}} < 0$):** Impossible with raw gunplay alone. You *must* use utility (smoke/flashbang) or take a different route.

#### 2. Know Your "Critical Lead" ($\ell^*$)
The Critical Lead tells you **how many milliseconds in advance** you need to know an enemy's position to survive:
* **Short Lead ($\ell^* \le 100\,\text{ms}$):** A fast peek or dynamic reaction will work.
* **Long Lead ($\ell^* \ge 170\,\text{ms}$):** Fast peeking will get you killed. You must pre-position your crosshair at the exact angle *before* un-occluding yourself.

#### 3. Slicing the Pie: The Math of Corner Distance
The paper mathematically demonstrates why standing far from a corner gives you an advantage:
* Moving further away from a doorway reduces the angular spread ($\Delta\theta$) between threats.
* Smaller angular spread means your crosshair spends fewer milliseconds rotating ($q_{ij}$), giving you higher tactical margin.

#### 4. Clearing Order Matters More Than Proximity
The optimal clearing sequence ($\pi^*$) is not always the closest enemy. Clearing the target with the **tightest deadline** first often prevents an unserviceable deadline breach on the second target.

---

### 🛠️ For Level Designers & Developers: How to Use the System

#### 1. Compile-Time Tactical Level Linting
Instead of relying on months of expensive human playtesting to find bad sightlines, run your 2D gray-box geometry through the compiler ($< 0.1\,\text{ms}$ per room):

```text
[Author 2D Gray-Box] ──> [Run Compiler] ──> [Auto-Label Transitions]
                                                   │
         ┌─────────────────────────────────────────┼────────────────────────────────────────┐
         ▼                                         ▼                                        ▼
  Blind-Clearable                         Knowledge-Rescuable                     Structurally Overloaded
  (Ship directly)                         (Label as expert site / add visual cues)  (Auto-repair or redesign)
```

#### 2. One-Click Automated Level Repair
When a room is flagged as structurally overloaded ($\mathcal{M} < 0$):
1. The solver identifies the **controlling occluder** (the specific wall or crate causing the simultaneous sightline).
2. It tests minimal translations along the grid ($0.05\,\text{m}$ steps, median displacement $0.85\,\text{m}$).
3. It finds the minimal geometric adjustment that guarantees $\mathcal{M} \ge +2\,\text{tics}$ ($+57\,\text{ms}$ safety cushion).
4. The designer accepts or adjusts the suggested fix in the CAD workbench.

#### 3. Safe Procedural Dungeon & Modular Assembly
If building procedural levels out of modular rooms (e.g. *Kill Block*, *Spelunky*, *The Binding of Isaac*, or competitive rogue-lites):
* Each module generates an algebraic **transfer matrix** over $(\min, +)$ algebra.
* By ensuring connection doorways have "quiescent reset zones" (shielded from sightlines), **global level fairness is mathematically guaranteed by checking individual rooms locally** ($C \equiv D$ theorem), with zero runtime simulation cost.

#### 4. Designing to Player "Capability Envelopes"
Instead of guessing whether a map is "too hard," calculate its **Capability Envelope** $\mathcal{C}(G)$:
$$\omega^* = \inf \{ \omega : \mathcal{M}(\omega) \ge 0 \}, \quad A^* = \sup \{ A : \mathcal{M}(A) \ge 0 \}$$
* You can tune maps for casual matchmaking ($\omega = 180^\circ/\text{s}, A = 250\,\text{ms}$) vs. esports tournament play ($\omega = 360^\circ/\text{s}, A = 140\,\text{ms}$).
* Procedural systems can dynamically adjust wall positions to scale the required aim speed to match the player's matchmaking rank (MMR).

#### 5. Interactive CAD Workbench
Launch the built-in CAD server to drag walls and inspect sightlines in real time:
```bash
python -m cut_the_cake.cad_server --port 5000
```
Open `http://127.0.0.1:5000` to test layout changes, watch animated reticle trajectories, and inspect live Tactical Margins.
