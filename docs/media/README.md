# Cut the Cake — Visual Media Assets Directory

This directory houses the visual assets, animation loops, diagrams, and video captures for *Cut the Cake*.

---

## 1. Directory Structure

```text
docs/media/
├── README.md               # Asset manifest and capture standards (this file)
├── capture_manifest.json   # Configuration manifest for automated frame capture
├── hero_clearability.gif   # Asset 0: The 10-second hero clearability loop
├── same_count_timing.gif   # Asset 1: Same count, different timing comparison
├── move_one_wall.gif       # Asset 2: Canonical +1.10 m auto-repair loop
├── global_vs_local.gif     # Asset 3: Whole-route vs local Suffix Margin
├── model_says_no.gif       # Asset 4: Dust II B-Tunnels expected negative
├── height_reveal.gif       # Asset 5: Height-induced reveal differentiation
├── quantization_null.gif   # Asset 6: Ascent pitch angle quantization null
├── execution_parity.gif    # Asset 7: 3D controller execution parity
└── static/
    ├── evidence_ladder.svg # Static vector graphic of the 7-tier evidence ladder
    └── pipeline.svg        # Static vector diagram of geometry-to-contract compilation
```

---

## 2. Capture Standards

- **GIF Resolution:** `1200 x 675` (16:9 widescreen) or `1000 x 750` (4:3 aspect).
- **Framerate:** 20 fps.
- **Color Optimization:** Lanczos scaling with 256-color global palette generation via `ffmpeg`.
- **WebM Video:** High-efficiency VP9 / H.264 video format for browser and website embedding.
- **Determinism:** All visual assets are captured directly from frozen Python test fixtures via `tools/communication_capture.py`.
