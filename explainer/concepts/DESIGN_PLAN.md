# Tactical Clearability Visual Concepts — Prototype Plan

This directory is intentionally **not** another full guided explainer. It is a set of isolated visual prototypes that can be reviewed, corrected, or discarded one at a time before any of them are promoted into the main explainer.

## Design panel used for every prototype

Each concept is reviewed against four perspectives before implementation:

1. **FPS player / coach** — Can a player recognize the physical action immediately without knowing the research vocabulary?
2. **Visual / HCI design** — Is there one obvious focal point and only one changing variable?
3. **Math education** — Does the picture establish the phenomenon before notation appears?
4. **Scientific review** — Is it clear what is a teaching simplification versus a frozen/canonical research fixture?

## Hard gates

A prototype fails if any of these are false:

- **Five-second test:** with explanatory text hidden, the viewer can still say what physically changed.
- **One-sentence test:** the page has one main takeaway that fits in one sentence.
- **One-variable test:** the primary interaction changes one thing at a time.
- **Math-off test:** the concept still makes sense before `Show the math` is opened.
- **No mystery labels:** early visuals do not depend on P1/P2, coordinate origins, or research notation for basic comprehension.
- **Provenance visible:** teaching-only examples say so; canonical examples name their source fixture.

## Prototype set

| # | Human question | Player intuition | Research bridge | Provenance |
|---|---|---|---|---|
| 01 | Why does backing away from a corner help? | Slice the pie | angular reveal `theta = atan(x/d)` | teaching geometry |
| 02 | Why does crosshair placement matter? | Centering / pre-positioning | setup cost `q = Delta theta / omega` | teaching geometry |
| 03 | Why can two enemies be worse than three? | isolate angles / avoid crossfire | staggered release times `r_j` | teaching contrast |
| 04 | Why does clear order matter? | dangerous angle first | permutation-dependent lateness `L^pi`, optimum `L*` | teaching scheduling fixture |
| 05 | What does Tactical Margin mean? | did the clear fit in time? | `M = -L*` | teaching timeline |
| 06 | What does map knowledge buy you? | pre-aim a known angle | actionability `a_j(ell)` and critical lead `ell*` | teaching + canonical handoff |
| 07 | Can the same room change answer? | route choice | traversal-conditioned job set/order | canonical F05 fixture |
| 08 | How does this become PCG math? | safe room-to-room handoff | state-conditioned transfer map / min-plus composition | research-only bridge |

## Promotion rule

Do **not** merge these concepts into the main guided explainer merely because the code works. Each page is a visual prototype. Promote only after manual review establishes that the visual itself is clear.
