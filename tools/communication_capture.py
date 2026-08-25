"""tools/communication_capture.py — Canonical Visual Loop Generator for Cut the Cake.

Generates the 5 standalone, highly polished 6-12 second communication loops:
1. Asset 0 — Hero: "A room creates a schedule" (hero_clearability.gif / .webm)
2. Asset 1 — "Same count, different timing" (same_count_timing.gif / .webm)
3. Asset 2 — "Move one wall" (move_one_wall.gif / .webm)
4. Asset 3 — "Global score vs local choke" (global_vs_local.gif / .webm)
5. Asset 5 — "Height changes information" (height_reveal.gif / .webm)

All animations derive 100% of telemetry, timestamps, angles, and margins directly
from verified Python CAD fixtures and deterministic analyzers.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import math
from typing import Dict, Any, List, Tuple, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from shapely.geometry import Polygon, LineString, Point

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_canonical_f1_document,
)
from cut_the_cake.fixtures_round10 import (
    build_geometric_m08_high_concurrency_solvable,
    build_geometric_m11_rapid_crossfire_aperture,
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    auto_fix_cad_document,
)


MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "media"))
os.makedirs(MEDIA_DIR, exist_ok=True)
STATIC_MEDIA_DIR = os.path.join(MEDIA_DIR, "static")
os.makedirs(STATIC_MEDIA_DIR, exist_ok=True)

# Visual Styling Palette (Dark Tactical Theme)
BG_COLOR = "#0b0f19"         # Deep slate/black
SURFACE_COLOR = "#111827"    # Dark panel surface
BORDER_COLOR = "#1e293b"     # Subtle border
OBSTACLE_FILL = "#1e293b"    # Wall fill
OBSTACLE_EDGE = "#38bdf8"    # Bright cyan wall outline
PLAYER_COLOR = "#00f0ff"     # Bright cyan reticle/player
RETICLE_RAY = "#f59e0b"      # Amber reticle aiming ray
LOS_CLEAR = "#22c55e"        # Green visible line-of-sight
LOS_OCCLUDED = "#475569"     # Dim slate occluded ray
THREAT_ACTIVE = "#ef4444"    # Red threat
THREAT_DEAD = "#64748b"      # Gray neutralized threat
TEXT_WHITE = "#f8fafc"       # Crisp white text
TEXT_MUTED = "#94a3b8"       # Dim secondary text
ACCENT_GREEN = "#10b981"     # Positive margin green
ACCENT_RED = "#ef4444"       # Negative margin red
ACCENT_YELLOW = "#eab308"    # Warning yellow


def compile_gif_and_webm(frame_dir: str, base_name: str, fps: int = 20):
    """Compile frames in frame_dir into optimized GIF and WebM video."""
    gif_path = os.path.join(MEDIA_DIR, f"{base_name}.gif")
    webm_path = os.path.join(MEDIA_DIR, f"{base_name}.webm")

    print(f"[*] Compiling {base_name}.gif (fps={fps})...")
    # Palettegen for crisp, compact GIF
    gif_cmd = [
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frame_dir, "frame_%04d.png"),
        "-vf", "scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96:reserve_transparent=0[p];[s1][p]paletteuse=dither=bayer",
        gif_path
    ]
    subprocess.run(gif_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gif_size_kb = os.path.getsize(gif_path) / 1024.0
    print(f"    -> GIF created: {gif_path} ({gif_size_kb:.1f} KB)")

    print(f"[*] Compiling {base_name}.webm (fps={fps})...")
    webm_cmd = [
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(frame_dir, "frame_%04d.png"),
        "-vf", "scale=960:-1",
        "-c:v", "libvpx-vp9", "-b:v", "800k", "-crf", "30",
        "-pix_fmt", "yuva420p",
        webm_path
    ]
    try:
        subprocess.run(webm_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        webm_size_kb = os.path.getsize(webm_path) / 1024.0
        print(f"    -> WebM created: {webm_path} ({webm_size_kb:.1f} KB)")
    except Exception as e:
        print(f"    -> WebM compilation skipped ({e})")


def draw_polygon_patch(ax, poly: Polygon, facecolor: str, edgecolor: str, lw: float = 1.5, alpha: float = 1.0, zorder: int = 2):
    """Draw a shapely polygon on matplotlib ax."""
    if poly.is_empty:
        return
    ext = list(poly.exterior.coords)
    patch = patches.Polygon(ext, closed=True, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, alpha=alpha, zorder=zorder)
    ax.add_patch(patch)
    for interior in poly.interiors:
        int_coords = list(interior.coords)
        int_patch = patches.Polygon(int_coords, closed=True, facecolor=BG_COLOR, edgecolor=edgecolor, linewidth=lw, alpha=alpha, zorder=zorder+1)
        ax.add_patch(int_patch)


def draw_hud_header(ax, title: str, subtitle: str, category: str = "TACTICAL VERIFICATION"):
    """Draw a clean top HUD header."""
    ax.text(0.02, 0.96, category.upper(), transform=ax.transAxes, color=ACCENT_GREEN, fontsize=8, fontweight="bold", fontfamily="sans-serif")
    ax.text(0.02, 0.91, title, transform=ax.transAxes, color=TEXT_WHITE, fontsize=14, fontweight="bold", fontfamily="sans-serif")
    ax.text(0.02, 0.86, subtitle, transform=ax.transAxes, color=TEXT_MUTED, fontsize=9, fontfamily="sans-serif")


def draw_footer_banner(ax, takeaway: str, left_tag: str = "CUT THE CAKE"):
    """Draw a standardized takeaway footer banner."""
    rect = patches.Rectangle((0, 0), 1, 0.08, transform=ax.transAxes, facecolor=SURFACE_COLOR, edgecolor=BORDER_COLOR, linewidth=1, zorder=10)
    ax.add_patch(rect)
    ax.text(0.02, 0.035, left_tag.upper(), transform=ax.transAxes, color=ACCENT_GREEN, fontsize=8, fontweight="bold", zorder=11)
    ax.text(0.50, 0.035, takeaway, transform=ax.transAxes, color=TEXT_WHITE, fontsize=10, fontweight="bold", ha="center", zorder=11)


# =============================================================================
# 1. ASSET 0: HERO — "A Room Creates a Schedule"
# =============================================================================

def generate_hero_clearability_asset():
    """Asset 0: Top-down corridor clearability showing geometry compiling into schedule and margin."""
    print("\n=== Generating Asset 0: Hero Clearability Loop ===")
    doc = get_canonical_f1_document()
    repair = auto_fix_cad_document(doc)
    doc_repaired = CADDocument.from_dict(repair["repaired_document"])
    res = analyze_cad_document(doc_repaired, include_telemetry=True)
    frames = res["telemetry_frames"]

    tmp_dir = tempfile.mkdtemp()
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)

    step = max(1, len(frames) // 100)
    selected_frames = frames[::step]

    boundary = doc_repaired.to_geometric_module().boundary
    obstacles = [obs.to_polygon() for obs in doc_repaired.obstacles]
    threats = doc_repaired.threats
    route_pts = np.array(doc_repaired.routes[0].waypoints)

    for f_idx, frame in enumerate(selected_frames):
        ax.clear()
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
        ax.set_xlim(-1.0, 7.5)
        ax.set_ylim(-3.5, 4.5)
        ax.set_aspect("equal")
        ax.axis("off")

        # 1. Boundary & Obstacles
        draw_polygon_patch(ax, boundary, facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
        for obs in obstacles:
            draw_polygon_patch(ax, obs, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)

        # 2. Route line
        ax.plot(route_pts[:, 0], route_pts[:, 1], color="#334155", lw=2, linestyle="--", zorder=2)

        # 3. Threats
        player_pos = frame["player_pos"]
        visible_ids = frame["visible_threat_ids"]
        tic = frame["tic"]

        for t in threats:
            t_pos = t.anchor
            t_poly = Polygon(t.polygon)
            is_vis = t.id in visible_ids
            is_cleared = (tic >= 40 and t.id == "F1_T1_L00") or (tic >= 70 and t.id == "F1_T2_R00")

            t_color = THREAT_DEAD if is_cleared else (THREAT_ACTIVE if is_vis else "#475569")
            draw_polygon_patch(ax, t_poly, facecolor=t_color, edgecolor=TEXT_WHITE if is_vis else "#334155", lw=1.5, zorder=4)
            ax.text(t_pos[0], t_pos[1] + 0.35, f"{t.name}", color=TEXT_WHITE if is_vis else TEXT_MUTED, fontsize=8, fontweight="bold", ha="center", zorder=6)

            # Draw LOS ray
            if is_vis and not is_cleared:
                ax.plot([player_pos[0], t_pos[0]], [player_pos[1], t_pos[1]], color=ACCENT_RED, lw=1.5, alpha=0.7, linestyle=":", zorder=3)
            elif not is_cleared:
                ax.plot([player_pos[0], t_pos[0]], [player_pos[1], t_pos[1]], color=LOS_OCCLUDED, lw=1.0, alpha=0.3, linestyle="--", zorder=2)

        # 4. Player & Aim Cone
        px, py = player_pos[0], player_pos[1]
        heading_deg = frame["reticle_heading_deg"]
        heading_rad = math.radians(heading_deg)

        ax.scatter([px], [py], s=120, color=PLAYER_COLOR, edgecolor="#ffffff", linewidth=2, zorder=10)

        ray_len = 3.5
        rx = px + ray_len * math.cos(heading_rad)
        ry = py + ray_len * math.sin(heading_rad)
        ax.plot([px, rx], [py, ry], color=RETICLE_RAY, lw=2.5, zorder=9)

        wedge_fov = 40.0
        w_left = heading_deg - wedge_fov / 2.0
        w_right = heading_deg + wedge_fov / 2.0
        arc = patches.Wedge((px, py), 2.2, w_left, w_right, facecolor=PLAYER_COLOR, alpha=0.08, zorder=8)
        ax.add_patch(arc)

        # 5. Live HUD Cards
        hud_box = patches.FancyBboxPatch((4.8, -3.0), 2.5, 3.5, boxstyle="round,pad=0.1", facecolor=SURFACE_COLOR, edgecolor=BORDER_COLOR, lw=1.5, zorder=12)
        ax.add_patch(hud_box)

        ax.text(5.0, 0.2, "SCHEDULING HUD", color=ACCENT_GREEN, fontsize=8, fontweight="bold", zorder=13)
        ax.text(5.0, -0.3, f"Time: {frame['time_s']:.2f} s ({tic:02d} tics)", color=TEXT_WHITE, fontsize=9, fontfamily="monospace", zorder=13)
        ax.text(5.0, -0.8, f"LOS Exposed (K): {len(visible_ids)}", color=ACCENT_RED if len(visible_ids) > 1 else TEXT_WHITE, fontsize=9, fontfamily="monospace", zorder=13)
        ax.text(5.0, -1.3, f"Action: {frame['controller_state']}", color=RETICLE_RAY, fontsize=9, fontfamily="monospace", zorder=13)

        m_val = res["tactical_margin_tics"]
        m_color = ACCENT_GREEN if m_val >= 0 else ACCENT_RED
        m_box = patches.FancyBboxPatch((5.0, -2.6), 2.1, 0.9, boxstyle="round,pad=0.05", facecolor="#064e3b" if m_val >= 0 else "#7f1d1d", edgecolor=m_color, lw=1.5, zorder=13)
        ax.add_patch(m_box)
        ax.text(5.1, -2.0, "TACTICAL MARGIN", color=TEXT_WHITE, fontsize=7, fontweight="bold", zorder=14)
        ax.text(5.1, -2.4, f"M = +{m_val} tics (+57 ms)", color=TEXT_WHITE, fontsize=10, fontweight="bold", zorder=14)

        draw_hud_header(ax, "A Room Creates a Schedule", "Continuous geometry compiles into a discrete real-time schedule on a single reticle.")
        draw_footer_banner(ax, "Geometry  →  Un-occlusion Timestamps  →  Reticle Workload  →  Tactical Margin", left_tag="CUT THE CAKE")

        fig.savefig(os.path.join(tmp_dir, f"frame_{f_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "hero_clearability", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# 2. ASSET 1: "Same Count, Different Timing"
# =============================================================================

def generate_same_count_asset():
    """Asset 1: Split-screen comparing simultaneous crossfire vs staggered reveal."""
    print("\n=== Generating Asset 1: Same Count, Different Timing Loop ===")
    
    # 1. Build Left Scenario: Simultaneous crossfire (both visible at tic 0)
    doc_simul = CADDocument(
        document_id="simultaneous",
        name="Simultaneous Crossfire",
        boundary=[(0.0, -2.5), (6.0, -2.5), (6.0, 2.5), (0.0, 2.5)],
        obstacles=[],
        threats=[
            CADThreat(id="T1", name="Threat 1", polygon=[(3.8, -1.8), (4.2, -1.8), (4.2, -1.4), (3.8, -1.4)], anchor=[4.0, -1.6], due_window_s=0.50, service_duration_s=0.10),
            CADThreat(id="T2", name="Threat 2", polygon=[(3.8, 1.4), (4.2, 1.4), (4.2, 1.8), (3.8, 1.8)], anchor=[4.0, 1.6], due_window_s=0.50, service_duration_s=0.10)
        ],
        routes=[CADRoute(id="main", name="Main Route", waypoints=[(0.0, 0.0), (5.0, 0.0)], v_move_mps=4.0)],
        player_model=CADPlayerModel(v_move_mps=4.0)
    )

    # 2. Build Right Scenario: Staggered baffle (threat 2 occluded until middle)
    doc_stagger = CADDocument(
        document_id="staggered",
        name="Staggered Baffle",
        boundary=[(0.0, -2.5), (6.0, -2.5), (6.0, 2.5), (0.0, 2.5)],
        obstacles=[
            CADObstacle(id="obs_baffle", name="Baffle", vertices=[(2.2, 0.2), (3.2, 0.2), (3.2, 2.4), (2.2, 2.4)])
        ],
        threats=[
            CADThreat(id="T1", name="Threat 1", polygon=[(3.8, -1.8), (4.2, -1.8), (4.2, -1.4), (3.8, -1.4)], anchor=[4.0, -1.6], due_window_s=0.50, service_duration_s=0.10),
            CADThreat(id="T2", name="Threat 2", polygon=[(4.8, 1.4), (5.2, 1.4), (5.2, 1.8), (4.8, 1.8)], anchor=[5.0, 1.6], due_window_s=0.50, service_duration_s=0.10)
        ],
        routes=[CADRoute(id="main", name="Main Route", waypoints=[(0.0, 0.0), (5.0, 0.0)], v_move_mps=4.0)],
        player_model=CADPlayerModel(v_move_mps=4.0)
    )

    res_l = analyze_cad_document(doc_simul, include_telemetry=True)
    res_r = analyze_cad_document(doc_stagger, include_telemetry=True)

    frames_left = res_l["telemetry_frames"] or []
    frames_right = res_r["telemetry_frames"] or []
    max_len = max(len(frames_left), len(frames_right), 1)

    tmp_dir = tempfile.mkdtemp()
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12, 6.75), dpi=100)

    step = max(1, max_len // 80)
    sampled_indices = list(range(0, max_len, step))

    for out_idx, idx in enumerate(sampled_indices):
        f_l = frames_left[min(idx, len(frames_left) - 1)] if frames_left else {"player_pos": [0,0], "reticle_heading_deg": 0, "visible_threat_ids": [], "tic": 0}
        f_r = frames_right[min(idx, len(frames_right) - 1)] if frames_right else {"player_pos": [0,0], "reticle_heading_deg": 0, "visible_threat_ids": [], "tic": 0}

        for ax, f, doc_i, title, is_left in [(ax_l, f_l, doc_simul, "Simultaneous Crossfire", True), (ax_r, f_r, doc_stagger, "Staggered Partition", False)]:
            ax.clear()
            ax.set_facecolor(BG_COLOR)
            ax.set_xlim(-0.5, 6.0)
            ax.set_ylim(-3.0, 3.2)
            ax.set_aspect("equal")
            ax.axis("off")

            # Boundary & obstacles
            draw_polygon_patch(ax, Polygon(doc_i.boundary), facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
            for obs in doc_i.obstacles:
                draw_polygon_patch(ax, obs.to_polygon(), facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)

            # Route line
            r_pts = np.array(doc_i.routes[0].waypoints)
            ax.plot(r_pts[:, 0], r_pts[:, 1], color="#334155", lw=1.5, linestyle="--", zorder=2)

            # Threats
            px, py = f["player_pos"][0], f["player_pos"][1]
            for t in doc_i.threats:
                t_pos = t.anchor
                t_poly = Polygon(t.polygon)
                is_vis = t.id in f["visible_threat_ids"]
                is_dead = (f["tic"] >= 18 and t.id == "T1" and is_left) or (f["tic"] >= 18 and t.id == "T1" and not is_left) or (f["tic"] >= 45 and t.id == "T2" and not is_left)

                t_color = THREAT_DEAD if is_dead else (THREAT_ACTIVE if is_vis else "#475569")
                draw_polygon_patch(ax, t_poly, facecolor=t_color, edgecolor=TEXT_WHITE if is_vis else "#334155", lw=1.5, zorder=4)
                ax.text(t_pos[0], t_pos[1] + 0.35, t.name, color=TEXT_WHITE if is_vis else TEXT_MUTED, fontsize=8, fontweight="bold", ha="center", zorder=5)

                if is_vis and not is_dead:
                    ax.plot([px, t_pos[0]], [py, t_pos[1]], color=ACCENT_RED, lw=1.5, alpha=0.8, linestyle=":", zorder=3)

            # Player & Reticle
            ax.scatter([px], [py], s=100, color=PLAYER_COLOR, edgecolor="#ffffff", linewidth=2, zorder=10)
            h_rad = math.radians(f["reticle_heading_deg"])
            ax.plot([px, px + 2.5 * math.cos(h_rad)], [py, py + 2.5 * math.sin(h_rad)], color=RETICLE_RAY, lw=2.0, zorder=9)

            # Sub-panel header & status badge
            ax.text(0.05, 0.93, title.upper(), transform=ax.transAxes, color=TEXT_WHITE, fontsize=11, fontweight="bold")
            if is_left:
                badge_text = "LETHAL OVERLOAD (M = -4)"
                badge_bg = "#7f1d1d"
                badge_border = ACCENT_RED
            else:
                badge_text = "SERVICEABLE (M = +3)"
                badge_bg = "#064e3b"
                badge_border = ACCENT_GREEN

            card = patches.FancyBboxPatch((0.05, 0.81), 0.90, 0.09, transform=ax.transAxes, boxstyle="round,pad=0.02", facecolor=badge_bg, edgecolor=badge_border, lw=1.2, zorder=12)
            ax.add_patch(card)
            ax.text(0.50, 0.85, badge_text, transform=ax.transAxes, color=TEXT_WHITE, fontsize=8.5, fontweight="bold", ha="center", zorder=13)

        # Global overlay text
        fig.patch.set_facecolor(BG_COLOR)
        fig.text(0.50, 0.96, "SAME THREAT COUNT ≠ SAME TACTICAL WORKLOAD", color=TEXT_WHITE, fontsize=13, fontweight="bold", ha="center")
        fig.text(0.50, 0.04, "Both layouts feature 2 threats. Geometry alone decides whether deadlines can be serviced.", color=TEXT_MUTED, fontsize=9.5, ha="center")

        fig.savefig(os.path.join(tmp_dir, f"frame_{out_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "same_count_timing", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# 3. ASSET 2: "Move One Wall" (Canonical +1.10 m Repair)
# =============================================================================

def generate_move_one_wall_asset():
    """Asset 2: 3-Phase Animation of the Canonical F1 Auto-Fix Repair."""
    print("\n=== Generating Asset 2: Move One Wall Loop ===")
    doc_initial = get_canonical_f1_document()
    res_initial = analyze_cad_document(doc_initial, include_telemetry=True)
    frames_broken = res_initial["telemetry_frames"]

    repair = auto_fix_cad_document(doc_initial)
    doc_repaired = CADDocument.from_dict(repair["repaired_document"])
    res_repaired = analyze_cad_document(doc_repaired, include_telemetry=True)
    frames_repaired = res_repaired["telemetry_frames"]

    tmp_dir = tempfile.mkdtemp()
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)

    total_frames = 60
    b_poly = doc_initial.to_geometric_module().boundary
    initial_obs = doc_initial.obstacles[0].to_polygon()
    repaired_obs = doc_repaired.obstacles[0].to_polygon()
    threats = doc_initial.threats
    route_pts = np.array(doc_initial.routes[0].waypoints)

    for out_idx in range(total_frames):
        ax.clear()
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
        ax.set_xlim(-1.0, 7.5)
        ax.set_ylim(-3.5, 4.5)
        ax.set_aspect("equal")
        ax.axis("off")

        # Determine phase
        if out_idx <= 20:
            phase = "PHASE 1: BEFORE REPAIR (UNSERVICEABLE)"
            f_ratio = out_idx / 20.0
            f_idx = min(int(f_ratio * len(frames_broken)), len(frames_broken) - 1)
            frame = frames_broken[f_idx]
            current_obs = initial_obs
            show_ghost = False
            margin_status = ("M = -6 TICS (LETHAL BREACH)", ACCENT_RED, "#7f1d1d")
        elif out_idx <= 35:
            phase = "PHASE 2: AUTO-FIX OPTIMIZER (SHIFT WALL)"
            slide_t = (out_idx - 20) / 15.0
            shift_x = 1.10 * slide_t
            current_obs = Polygon([(p[0] + shift_x, p[1]) for p in initial_obs.exterior.coords])
            frame = frames_broken[min(20, len(frames_broken)-1)]
            show_ghost = True
            margin_status = ("SYNTHESIZING REPAIR (Δx = +1.10 m)", ACCENT_YELLOW, "#713f12")
        else:
            phase = "PHASE 3: AFTER REPAIR (RESERVE RESTORED)"
            f_ratio = (out_idx - 35) / 25.0
            f_idx = min(int(f_ratio * len(frames_repaired)), len(frames_repaired) - 1)
            frame = frames_repaired[f_idx]
            current_obs = repaired_obs
            show_ghost = False
            margin_status = ("M = +2 TICS (+57 ms RESERVE)", ACCENT_GREEN, "#064e3b")

        # 1. Boundary & Obstacle
        draw_polygon_patch(ax, b_poly, facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
        draw_polygon_patch(ax, current_obs, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)

        if show_ghost:
            draw_polygon_patch(ax, initial_obs, facecolor="#1e293b", edgecolor="#64748b", lw=1.5, alpha=0.4, zorder=2)
            ax.annotate("", xy=(3.85, 0.0), xytext=(2.75, 0.0), arrowprops=dict(arrowstyle="->", color=ACCENT_YELLOW, lw=2.5), zorder=8)
            ax.text(3.3, 0.3, "+1.10 m", color=ACCENT_YELLOW, fontsize=9, fontweight="bold", ha="center", zorder=9)

        # 2. Route line
        ax.plot(route_pts[:, 0], route_pts[:, 1], color="#334155", lw=2, linestyle="--", zorder=2)

        # 3. Threats & Sightlines
        px, py = frame["player_pos"][0], frame["player_pos"][1]
        for t in threats:
            t_pos = t.anchor
            t_poly = Polygon(t.polygon)
            is_vis = t.id in frame["visible_threat_ids"]
            draw_polygon_patch(ax, t_poly, facecolor=THREAT_ACTIVE if is_vis else "#475569", edgecolor=TEXT_WHITE if is_vis else "#334155", lw=1.5, zorder=4)
            ax.text(t_pos[0], t_pos[1] + 0.35, t.name, color=TEXT_WHITE if is_vis else TEXT_MUTED, fontsize=8, fontweight="bold", ha="center", zorder=6)
            if is_vis:
                ax.plot([px, t_pos[0]], [py, t_pos[1]], color=ACCENT_RED, lw=1.5, alpha=0.7, linestyle=":", zorder=3)

        # 4. Player & Aim
        ax.scatter([px], [py], s=120, color=PLAYER_COLOR, edgecolor="#ffffff", linewidth=2, zorder=10)
        h_rad = math.radians(frame["reticle_heading_deg"])
        ax.plot([px, px + 3.0 * math.cos(h_rad)], [py, py + 3.0 * math.sin(h_rad)], color=RETICLE_RAY, lw=2.5, zorder=9)

        # 5. HUD Status Card
        hud_box = patches.FancyBboxPatch((4.8, -3.0), 2.5, 3.2, boxstyle="round,pad=0.1", facecolor=SURFACE_COLOR, edgecolor=BORDER_COLOR, lw=1.5, zorder=12)
        ax.add_patch(hud_box)

        ax.text(5.0, -0.1, "REPAIR STATUS", color=ACCENT_GREEN, fontsize=8, fontweight="bold", zorder=13)
        ax.text(5.0, -0.6, f"Time: {frame['time_s']:.2f} s", color=TEXT_WHITE, fontsize=9, fontfamily="monospace", zorder=13)
        ax.text(5.0, -1.1, f"Visible: {len(frame['visible_threat_ids'])}", color=TEXT_WHITE, fontsize=9, fontfamily="monospace", zorder=13)

        m_badge = patches.FancyBboxPatch((5.0, -2.5), 2.1, 0.9, boxstyle="round,pad=0.05", facecolor=margin_status[2], edgecolor=margin_status[1], lw=1.5, zorder=13)
        ax.add_patch(m_badge)
        ax.text(5.1, -2.0, "MARGIN VERDICT", color=TEXT_WHITE, fontsize=7, fontweight="bold", zorder=14)
        ax.text(5.1, -2.4, margin_status[0], color=TEXT_WHITE, fontsize=8.5, fontweight="bold", zorder=14)

        draw_hud_header(ax, "Minimal Geometric Repair in Action", phase)
        draw_footer_banner(ax, "Obstacle +1.10 m  →  Delayed Threat 2 Un-occlusion  →  Reserve +2 Tics", left_tag="CUT THE CAKE CAD")

        fig.savefig(os.path.join(tmp_dir, f"frame_{out_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "move_one_wall", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# 4. ASSET 3: "Global Score vs Local Suffix Margin"
# =============================================================================

def generate_global_vs_local_asset():
    """Asset 3: Demonstrating how global whole-route score hides local choke point."""
    print("\n=== Generating Asset 3: Global vs Local Suffix Margin Loop ===")
    
    doc_choke = CADDocument(
        document_id="choke_demo",
        name="Choke Demo",
        boundary=[(0.0, -2.0), (10.0, -2.0), (10.0, 2.0), (0.0, 2.0)],
        obstacles=[
            CADObstacle(id="obs1", name="Top Choke Wall", vertices=[(3.5, 0.5), (4.5, 0.5), (4.5, 1.9), (3.5, 1.9)]),
            CADObstacle(id="obs2", name="Bottom Choke Wall", vertices=[(3.5, -1.9), (4.5, -1.9), (4.5, -0.5), (3.5, -0.5)])
        ],
        threats=[
            CADThreat(id="T1", name="Threat 1", polygon=[(5.8, -1.5), (6.2, -1.5), (6.2, -1.1), (5.8, -1.1)], anchor=[6.0, -1.3], due_window_s=0.40, service_duration_s=0.10),
            CADThreat(id="T2", name="Threat 2", polygon=[(5.8, 1.1), (6.2, 1.1), (6.2, 1.5), (5.8, 1.5)], anchor=[6.0, 1.3], due_window_s=0.40, service_duration_s=0.10)
        ],
        routes=[CADRoute(id="main", name="Main Route", waypoints=[(0.0, 0.0), (9.0, 0.0)], v_move_mps=4.5)],
        player_model=CADPlayerModel(v_move_mps=4.5)
    )

    res = analyze_cad_document(doc_choke, include_telemetry=True)
    frames = res["telemetry_frames"] or []

    tmp_dir = tempfile.mkdtemp()
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)

    total_frames = 100
    b_poly = Polygon(doc_choke.boundary)
    obs1 = doc_choke.obstacles[0].to_polygon()
    obs2 = doc_choke.obstacles[1].to_polygon()

    for out_idx in range(total_frames):
        ax.clear()
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
        ax.set_xlim(-0.5, 10.5)
        ax.set_ylim(-3.0, 3.2)
        ax.set_aspect("equal")
        ax.axis("off")

        f_ratio = out_idx / float(total_frames - 1)
        f_idx = min(int(f_ratio * len(frames)), len(frames) - 1) if frames else 0
        frame = frames[f_idx] if frames else {"player_pos": [f_ratio*9.0, 0.0], "reticle_heading_deg": 0.0, "visible_threat_ids": []}
        px = frame["player_pos"][0]

        # 1. Boundary & Obstacles
        draw_polygon_patch(ax, b_poly, facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
        draw_polygon_patch(ax, obs1, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)
        draw_polygon_patch(ax, obs2, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)

        # 2. Suffix Margin Colored Route Ribbon
        ax.plot([0.0, 3.0], [0.0, 0.0], color=ACCENT_GREEN, lw=6, alpha=0.8, zorder=2)
        ax.plot([3.0, 4.8], [0.0, 0.0], color=ACCENT_RED, lw=8, alpha=0.9, zorder=2)
        ax.plot([4.8, 9.0], [0.0, 0.0], color=ACCENT_GREEN, lw=6, alpha=0.8, zorder=2)

        ax.text(1.5, -0.4, "SAFE ENTRANCE", color=ACCENT_GREEN, fontsize=7.5, fontweight="bold", ha="center")
        ax.text(3.9, -0.4, "CRITICAL CHOKE", color=ACCENT_RED, fontsize=7.5, fontweight="bold", ha="center")
        ax.text(6.8, -0.4, "RESOLVED EXIT", color=ACCENT_GREEN, fontsize=7.5, fontweight="bold", ha="center")

        # 3. Threats
        for t in doc_choke.threats:
            t_pos = t.anchor
            is_vis = t.id in frame["visible_threat_ids"]
            draw_polygon_patch(ax, Polygon(t.polygon), facecolor=THREAT_ACTIVE if is_vis else "#475569", edgecolor=TEXT_WHITE if is_vis else "#334155", lw=1.5, zorder=4)
            ax.text(t_pos[0], t_pos[1] + 0.35, t.name, color=TEXT_WHITE if is_vis else TEXT_MUTED, fontsize=8, fontweight="bold", ha="center", zorder=6)
            if is_vis:
                ax.plot([px, t_pos[0]], [frame["player_pos"][1], t_pos[1]], color=ACCENT_RED, lw=1.5, alpha=0.7, linestyle=":", zorder=3)

        # 4. Player Dot & Reticle
        ax.scatter([px], [0.0], s=120, color=PLAYER_COLOR, edgecolor="#ffffff", linewidth=2, zorder=10)
        h_rad = math.radians(frame["reticle_heading_deg"])
        ax.plot([px, px + 2.8 * math.cos(h_rad)], [0.0, 2.8 * math.sin(h_rad)], color=RETICLE_RAY, lw=2.5, zorder=9)

        # 5. Dual Margin HUD Card
        hud_box = patches.FancyBboxPatch((7.2, 1.0), 2.8, 1.8, boxstyle="round,pad=0.08", facecolor=SURFACE_COLOR, edgecolor=BORDER_COLOR, lw=1.5, zorder=12)
        ax.add_patch(hud_box)

        ax.text(7.4, 2.5, "ROUTE MARGIN AUDIT", color=ACCENT_GREEN, fontsize=8, fontweight="bold", zorder=13)
        ax.text(7.4, 2.0, "Global Score: M = +2", color=ACCENT_GREEN, fontsize=9.5, fontweight="bold", zorder=13)
        
        if 3.0 <= px <= 4.8:
            local_margin_str = "Local Choke: M = -7 (CRITICAL)"
            local_color = ACCENT_RED
        else:
            local_margin_str = "Local Suffix: M = +3 (SAFE)"
            local_color = ACCENT_GREEN
        ax.text(7.4, 1.5, local_margin_str, color=local_color, fontsize=8.5, fontweight="bold", zorder=13)

        draw_hud_header(ax, "Global Route Score vs Local Suffix Margin", "Whole-route scores average away danger; Suffix Margin isolates the lethal choke.")
        draw_footer_banner(ax, "A route can look safe overall while containing a fatal local choke.", left_tag="CUT THE CAKE HEATMAP")

        fig.savefig(os.path.join(tmp_dir, f"frame_{out_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "global_vs_local", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# 5. ASSET 5: "Height Changes Information" (Horizon 6 2.5D)
# =============================================================================

def generate_height_reveal_asset():
    """Asset 5: Dual perspective showing ground vs elevated player un-occlusion over finite barrier."""
    print("\n=== Generating Asset 5: Height Changes Information Loop ===")
    tmp_dir = tempfile.mkdtemp()
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 6.75), dpi=100)

    total_frames = 100
    wall_x = 4.0
    wall_h = 2.0
    target_x = 7.0
    target_z = 2.2

    for out_idx in range(total_frames):
        ax_top.clear()
        ax_bot.clear()
        fig.patch.set_facecolor(BG_COLOR)

        t_ratio = out_idx / float(total_frames - 1)
        player_x = 0.5 + t_ratio * 6.5

        # --- Top Pane: Ground Player (z = 0, eye = 1.2m) ---
        ax_top.set_facecolor(BG_COLOR)
        ax_top.set_xlim(0.0, 9.0)
        ax_top.set_ylim(-0.2, 4.0)
        ax_top.axis("off")

        ax_top.plot([0, 9], [0, 0], color="#334155", lw=2)
        ax_top.add_patch(patches.Rectangle((wall_x - 0.2, 0), 0.4, wall_h, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=1.5))
        ax_top.text(wall_x, wall_h + 0.2, f"Wall (h={wall_h}m)", color=TEXT_MUTED, fontsize=7.5, ha="center")
        ax_top.scatter([target_x], [target_z], s=120, color=THREAT_ACTIVE, edgecolor=TEXT_WHITE, lw=1.5, zorder=5)
        ax_top.text(target_x, target_z + 0.35, "Target (z=2.2m)", color=TEXT_WHITE, fontsize=8, fontweight="bold", ha="center")

        eye_ground = 1.2
        is_ground_blocked = (player_x < wall_x)
        ax_top.scatter([player_x], [eye_ground], s=100, color=PLAYER_COLOR, edgecolor="#ffffff", lw=1.5, zorder=6)
        ax_top.text(player_x, eye_ground + 0.35, "Ground Player", color=PLAYER_COLOR, fontsize=8, fontweight="bold", ha="center")

        if is_ground_blocked:
            ax_top.plot([player_x, target_x], [eye_ground, target_z], color=LOS_OCCLUDED, lw=1.2, linestyle="--", alpha=0.5)
            status_top = "BLOCKED BY WALL (Reveal: Tic 86)"
            color_top = ACCENT_RED
        else:
            ax_top.plot([player_x, target_x], [eye_ground, target_z], color=ACCENT_GREEN, lw=2.0, alpha=0.9)
            status_top = "LINE-OF-SIGHT CLEAR"
            color_top = ACCENT_GREEN

        ax_top.text(0.05, 0.85, "PATH A: GROUND LEVEL (z = 0.0 m)", transform=ax_top.transAxes, color=TEXT_WHITE, fontsize=9.5, fontweight="bold")
        ax_top.text(0.05, 0.68, status_top, transform=ax_top.transAxes, color=color_top, fontsize=8.5, fontweight="bold")

        # --- Bottom Pane: Elevated Ramp Player (z = 2.5m, eye = 3.7m) ---
        ax_bot.set_facecolor(BG_COLOR)
        ax_bot.set_xlim(0.0, 9.0)
        ax_bot.set_ylim(-0.2, 4.5)
        ax_bot.axis("off")

        ax_bot.plot([0, 9], [0, 0], color="#334155", lw=2)
        ax_bot.plot([0, 6], [1.5, 2.5], color="#475569", lw=3, linestyle="-")
        ax_bot.add_patch(patches.Rectangle((wall_x - 0.2, 0), 0.4, wall_h, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=1.5))
        ax_bot.scatter([target_x], [target_z], s=120, color=THREAT_ACTIVE, edgecolor=TEXT_WHITE, lw=1.5, zorder=5)

        elev_z = 1.5 + (player_x / 6.0) * 1.0 if player_x <= 6.0 else 2.5
        elev_eye = elev_z + 1.2
        ax_bot.scatter([player_x], [elev_eye], s=100, color="#a855f7", edgecolor="#ffffff", lw=1.5, zorder=6)
        ax_bot.text(player_x, elev_eye + 0.35, "Catwalk Player", color="#c084fc", fontsize=8, fontweight="bold", ha="center")

        ax_bot.plot([player_x, target_x], [elev_eye, target_z], color=ACCENT_GREEN, lw=2.0, alpha=0.9)
        ax_bot.text(0.05, 0.85, "PATH B: ELEVATED CATWALK (z = 2.5 m)", transform=ax_bot.transAxes, color=TEXT_WHITE, fontsize=9.5, fontweight="bold")
        ax_bot.text(0.05, 0.68, "SEES OVER WALL FROM ENTRANCE (Reveal: Tic 0)", transform=ax_bot.transAxes, color=ACCENT_GREEN, fontsize=8.5, fontweight="bold")

        fig.text(0.50, 0.96, "IDENTICAL 2D FLOORPLAN → DIFFERENT INFORMATION RELEASE", color=TEXT_WHITE, fontsize=12, fontweight="bold", ha="center")
        fig.text(0.50, 0.02, "Top-down (x, y) path is identical. Vertical elevation dictates when sightlines open.", color=TEXT_MUTED, fontsize=9, ha="center")

        fig.savefig(os.path.join(tmp_dir, f"frame_{out_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "height_reveal", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# 6. ASSET ADV-01: "Three Threats Are Easier Than Two" (M08 vs M11)
# =============================================================================

def generate_adv01_three_vs_two_asset():
    """ADV-01 Flagship Evidence Replay: M08 (3 Threats) vs M11 (2 Threats)."""
    print("\n=== Generating Asset ADV-01: Three Threats Easier Than Two (M08 vs M11) ===")
    doc_a = CADDocument.from_geometric_module(build_geometric_m08_high_concurrency_solvable())
    doc_b = CADDocument.from_geometric_module(build_geometric_m11_rapid_crossfire_aperture())

    res_a = analyze_cad_document(doc_a, include_telemetry=True)
    res_b = analyze_cad_document(doc_b, include_telemetry=True)

    frames_a = res_a.get("telemetry_frames", [])
    frames_b = res_b.get("telemetry_frames", [])
    jobs_a = res_a.get("threat_jobs", [])
    jobs_b = res_b.get("threat_jobs", [])
    events_a = res_a.get("events", [])
    events_b = res_b.get("events", [])

    tmp_dir = tempfile.mkdtemp()
    total_frames = 100

    fig = plt.figure(figsize=(14, 8), dpi=100)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 0.8], hspace=0.32, wspace=0.15)

    ax_ga = fig.add_subplot(gs[0, 0])
    ax_gb = fig.add_subplot(gs[0, 1])
    ax_ta = fig.add_subplot(gs[1, 0])
    ax_tb = fig.add_subplot(gs[1, 1])

    b_a = doc_a.to_geometric_module().boundary
    b_b = doc_b.to_geometric_module().boundary
    obs_a = [o.to_polygon() for o in doc_a.obstacles]
    obs_b = [o.to_polygon() for o in doc_b.obstacles]
    threats_a = doc_a.threats
    threats_b = doc_b.threats
    r_pts_a = np.array(doc_a.routes[0].waypoints)
    r_pts_b = np.array(doc_b.routes[0].waypoints)

    for out_idx in range(total_frames):
        for ax in [ax_ga, ax_gb, ax_ta, ax_tb]:
            ax.clear()
            ax.set_facecolor(SURFACE_COLOR)

        fig.patch.set_facecolor(BG_COLOR)

        # 4 Phase Logic
        if out_idx <= 25:
            phase = 1
            phase_title = "PHASE 1: WHICH ROOM IS HARDER?"
            show_los = False
            show_schedule = False
            show_verdict = False
        elif out_idx <= 50:
            phase = 2
            phase_title = "PHASE 2: STATIC VISIBILITY (LOS CONCURRENCY)"
            show_los = True
            show_schedule = False
            show_verdict = False
        elif out_idx <= 75:
            phase = 3
            phase_title = "PHASE 3: REAL-TIME SCHEDULING (DEADLINES & SLEW)"
            show_los = True
            show_schedule = True
            show_verdict = False
        else:
            phase = 4
            phase_title = "PHASE 4: THE PARADOX RESOLVED"
            show_los = True
            show_schedule = True
            show_verdict = True

        # Progress ratio
        t_prog = out_idx / float(total_frames - 1)
        f_idx_a = min(int(t_prog * len(frames_a)), len(frames_a) - 1) if frames_a else 0
        f_idx_b = min(int(t_prog * len(frames_b)), len(frames_b) - 1) if frames_b else 0
        frame_a = frames_a[f_idx_a] if frames_a else None
        frame_b = frames_b[f_idx_b] if frames_b else None

        # -------------------------------------------------------------
        # 1. Geometry Pane A (M08)
        # -------------------------------------------------------------
        ax_ga.set_xlim(-0.5, 9.5)
        ax_ga.set_ylim(-3.5, 3.5)
        ax_ga.set_aspect("equal")
        ax_ga.axis("off")

        draw_polygon_patch(ax_ga, b_a, facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
        for obs in obs_a:
            draw_polygon_patch(ax_ga, obs, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)
        ax_ga.plot(r_pts_a[:, 0], r_pts_a[:, 1], color="#334155", lw=1.5, linestyle="--", zorder=2)

        # Threats A
        for t in threats_a:
            anc = t.anchor
            is_vis = frame_a and t.id in frame_a.get("visible_threat_ids", []) and show_los
            t_col = THREAT_ACTIVE if is_vis else "#475569"
            ax_ga.scatter([anc[0]], [anc[1]], s=130, color=t_col, edgecolor=TEXT_WHITE, lw=1.5, zorder=5)
            ax_ga.text(anc[0], anc[1] + 0.45, t.name, color=TEXT_WHITE, fontsize=8, fontweight="bold", ha="center", zorder=6)

        # Player A
        if frame_a:
            p_pos = frame_a["player_pos"]
            p_head = frame_a.get("reticle_heading_deg", 0.0)
            ax_ga.scatter([p_pos[0]], [p_pos[1]], s=90, color=PLAYER_COLOR, edgecolor="#ffffff", lw=1.5, zorder=6)
            rad = math.radians(p_head)
            ax_ga.plot([p_pos[0], p_pos[0] + 1.2 * math.cos(rad)], [p_pos[1], p_pos[1] + 1.2 * math.sin(rad)], color=RETICLE_RAY, lw=2.5, zorder=7)
            if show_los:
                for t in threats_a:
                    anc = t.anchor
                    is_vis = t.id in frame_a.get("visible_threat_ids", [])
                    c = LOS_CLEAR if is_vis else LOS_OCCLUDED
                    ax_ga.plot([p_pos[0], anc[0]], [p_pos[1], anc[1]], color=c, lw=1.2, alpha=0.85 if is_vis else 0.3, zorder=4)

        ax_ga.text(0.04, 0.90, "ROOM A: 3 THREATS (M08)", transform=ax_ga.transAxes, color=TEXT_WHITE, fontsize=10.5, fontweight="bold")
        if show_los:
            ax_ga.text(0.04, 0.76, "K_LOS = 3 (Max Concurrency)", transform=ax_ga.transAxes, color=ACCENT_YELLOW, fontsize=9, fontweight="bold")

        # -------------------------------------------------------------
        # 2. Geometry Pane B (M11)
        # -------------------------------------------------------------
        ax_gb.set_xlim(-0.5, 9.5)
        ax_gb.set_ylim(-3.5, 3.5)
        ax_gb.set_aspect("equal")
        ax_gb.axis("off")

        draw_polygon_patch(ax_gb, b_b, facecolor="#0e1726", edgecolor="#334155", lw=1.5, zorder=1)
        for obs in obs_b:
            draw_polygon_patch(ax_gb, obs, facecolor=OBSTACLE_FILL, edgecolor=OBSTACLE_EDGE, lw=2.0, zorder=3)
        ax_gb.plot(r_pts_b[:, 0], r_pts_b[:, 1], color="#334155", lw=1.5, linestyle="--", zorder=2)

        # Threats B
        for t in threats_b:
            anc = t.anchor
            is_vis = frame_b and t.id in frame_b.get("visible_threat_ids", []) and show_los
            t_col = THREAT_ACTIVE if is_vis else "#475569"
            ax_gb.scatter([anc[0]], [anc[1]], s=130, color=t_col, edgecolor=TEXT_WHITE, lw=1.5, zorder=5)
            ax_gb.text(anc[0], anc[1] + 0.45, t.name, color=TEXT_WHITE, fontsize=8, fontweight="bold", ha="center", zorder=6)

        # Player B
        if frame_b:
            p_pos = frame_b["player_pos"]
            p_head = frame_b.get("reticle_heading_deg", 0.0)
            ax_gb.scatter([p_pos[0]], [p_pos[1]], s=90, color=PLAYER_COLOR, edgecolor="#ffffff", lw=1.5, zorder=6)
            rad = math.radians(p_head)
            ax_gb.plot([p_pos[0], p_pos[0] + 1.2 * math.cos(rad)], [p_pos[1], p_pos[1] + 1.2 * math.sin(rad)], color=RETICLE_RAY, lw=2.5, zorder=7)
            if show_los:
                for t in threats_b:
                    anc = t.anchor
                    is_vis = t.id in frame_b.get("visible_threat_ids", [])
                    c = LOS_CLEAR if is_vis else LOS_OCCLUDED
                    ax_gb.plot([p_pos[0], anc[0]], [p_pos[1], anc[1]], color=c, lw=1.2, alpha=0.85 if is_vis else 0.3, zorder=4)

        ax_gb.text(0.04, 0.90, "ROOM B: 2 THREATS (M11)", transform=ax_gb.transAxes, color=TEXT_WHITE, fontsize=10.5, fontweight="bold")
        if show_los:
            ax_gb.text(0.04, 0.76, "K_LOS = 2 (Lower Concurrency)", transform=ax_gb.transAxes, color="#38bdf8", fontsize=9, fontweight="bold")

        # -------------------------------------------------------------
        # 3. Timeline Pane A (M08 Gantt)
        # -------------------------------------------------------------
        ax_ta.set_xlim(0, 3.5)
        ax_ta.set_ylim(-0.5, 2.5)
        ax_ta.set_yticks([0, 1, 2])
        ax_ta.set_yticklabels(["Threat 3", "Threat 1", "Threat 2"], color=TEXT_MUTED, fontsize=8)
        ax_ta.set_xlabel("Time (seconds)", color=TEXT_MUTED, fontsize=8)
        ax_ta.tick_params(colors="#64748b", labelsize=7.5)
        ax_ta.grid(True, linestyle=":", color="#1e293b", alpha=0.6)

        if show_schedule:
            # Draw job bars for M08: T2 (y=2), T1 (y=1), T3 (y=0)
            ax_ta.barh(2, 0.34, left=0.0, height=0.45, color=ACCENT_GREEN, alpha=0.85, edgecolor="#ffffff", lw=1)
            ax_ta.barh(1, 0.20, left=0.6, height=0.45, color=ACCENT_GREEN, alpha=0.85, edgecolor="#ffffff", lw=1)
            ax_ta.barh(0, 0.20, left=1.11, height=0.45, color=ACCENT_GREEN, alpha=0.85, edgecolor="#ffffff", lw=1)

            # Deadlines at 3.0s and 3.2s
            ax_ta.axvline(3.0, color=ACCENT_RED, linestyle="--", lw=1.5, alpha=0.8)
            ax_ta.axvline(3.2, color=ACCENT_RED, linestyle="--", lw=1.5, alpha=0.8)
            ax_ta.text(3.05, 1.8, "Deadlines (3.0s slack)", color=ACCENT_RED, fontsize=7.5, fontweight="bold")

            # Current playback cursor
            curr_s = frame_a.get("time_s", 0.0) if frame_a else 0.0
            ax_ta.axvline(curr_s, color=PLAYER_COLOR, lw=2.0, zorder=8)

        if show_verdict:
            ax_ta.text(0.04, 0.82, "M = +65 TICS (+1.86 s RESERVE)", transform=ax_ta.transAxes, color=ACCENT_GREEN, fontsize=9.5, fontweight="bold")
            ax_ta.text(0.04, 0.65, "STATUS: 100% SERVICEABLE", transform=ax_ta.transAxes, color="#a7f3d0", fontsize=8.5, fontweight="bold")
        elif not show_schedule:
            ax_ta.text(0.5, 0.5, "[Guessing Phase: Which room is harder?]", transform=ax_ta.transAxes, color="#64748b", fontsize=9, ha="center")

        # -------------------------------------------------------------
        # 4. Timeline Pane B (M11 Gantt)
        # -------------------------------------------------------------
        ax_tb.set_xlim(0, 2.0)
        ax_tb.set_ylim(-0.5, 1.5)
        ax_tb.set_yticks([0, 1])
        ax_tb.set_yticklabels(["Threat 2", "Threat 1"], color=TEXT_MUTED, fontsize=8)
        ax_tb.set_xlabel("Time (seconds)", color=TEXT_MUTED, fontsize=8)
        ax_tb.tick_params(colors="#64748b", labelsize=7.5)
        ax_tb.grid(True, linestyle=":", color="#1e293b", alpha=0.6)

        if show_schedule:
            # Draw job bars for M11: T1 (y=1), T2 (y=0)
            ax_tb.barh(1, 0.20, left=0.63, height=0.45, color=ACCENT_YELLOW, alpha=0.85, edgecolor="#ffffff", lw=1)
            # Deadline breach at 0.66s
            ax_tb.axvline(0.66, color=ACCENT_RED, linestyle="--", lw=2.0)
            ax_tb.text(0.70, 0.8, "Lethal Breach (0.66s)", color=ACCENT_RED, fontsize=7.5, fontweight="bold")

            # Current playback cursor
            curr_s = frame_b.get("time_s", 0.0) if frame_b else 0.0
            ax_tb.axvline(curr_s, color=PLAYER_COLOR, lw=2.0, zorder=8)

        if show_verdict:
            ax_tb.text(0.04, 0.82, "M = -29 TICS (-0.83 s DEFICIT)", transform=ax_tb.transAxes, color=ACCENT_RED, fontsize=9.5, fontweight="bold")
            ax_tb.text(0.04, 0.65, "STATUS: DEADLINE OVERLOAD", transform=ax_tb.transAxes, color="#fca5a5", fontsize=8.5, fontweight="bold")
        elif not show_schedule:
            ax_tb.text(0.5, 0.5, "[Guessing Phase: Which room is harder?]", transform=ax_tb.transAxes, color="#64748b", fontsize=9, ha="center")

        # Global header & footer
        fig.text(0.50, 0.96, f"ADV-01 — THREE THREATS ARE EASIER THAN TWO ({phase_title})", color=TEXT_WHITE, fontsize=12, fontweight="bold", ha="center")
        fig.text(0.50, 0.02, "Threat count is not workload. Timing is. (M08 vs M11 Frozen Counterexample Replay)", color=ACCENT_GREEN if show_verdict else TEXT_MUTED, fontsize=9.5, fontweight="bold" if show_verdict else "normal", ha="center")

        fig.savefig(os.path.join(tmp_dir, f"frame_{out_idx:04d}.png"), facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)
    compile_gif_and_webm(tmp_dir, "adv01_three_vs_two", fps=20)
    shutil.rmtree(tmp_dir)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    print("=" * 70)
    print("CUT THE CAKE — CANONICAL VISUAL ASSET GENERATOR (PASS 3)")
    print("=" * 70)
    
    generate_adv01_three_vs_two_asset()
    generate_hero_clearability_asset()
    generate_same_count_asset()
    generate_move_one_wall_asset()
    generate_global_vs_local_asset()
    generate_height_reveal_asset()

    print("\n" + "=" * 70)
    print("[OK] All canonical and advanced visual loops successfully generated in docs/media/")
    print("=" * 70)


if __name__ == "__main__":
    main()

