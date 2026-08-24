"""ASCII terminal visualizer and diagnostic reporter [G + C + P]."""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Optional
import numpy as np

from .model import World, ThreatView
from .paths import PathClearabilityResult, TrajectorySample


def render_ascii_map(
    world: World,
    player_pos: Tuple[float, float],
    path_coords: List[Tuple[float, float]],
    visible_threats: List[ThreatView],
    grid_w: int = 50,
    grid_h: int = 20
) -> str:
    """Render a 2D ASCII map showing obstacles, threats, player, and active lines of sight."""
    min_x, min_y, max_x, max_y = world.bounds
    # Add small padding
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    grid = [[" " for _ in range(grid_w)] for _ in range(grid_h)]

    def to_grid(x: float, y: float) -> Tuple[int, int]:
        gx = int(((x - min_x) / span_x) * (grid_w - 1))
        gy = int(((y - min_y) / span_y) * (grid_h - 1))
        gx = max(0, min(grid_w - 1, gx))
        gy = max(0, min(grid_h - 1, grid_h - 1 - gy))  # invert Y for terminal row
        return gx, gy

    # Draw obstacles
    for obs in world.obstacles:
        min_ox, min_oy, max_ox, max_oy = obs.bounds
        g_x0, g_y0 = to_grid(min_ox, max_oy)
        g_x1, g_y1 = to_grid(max_ox, min_oy)
        for r in range(min(g_y0, g_y1), max(g_y0, g_y1) + 1):
            for c in range(min(g_x0, g_x1), max(g_x0, g_x1) + 1):
                grid[r][c] = "#"

    # Draw path
    for i in range(len(path_coords) - 1):
        p1, p2 = path_coords[i], path_coords[i + 1]
        for t in np.linspace(0, 1, 15):
            px = p1[0] + t * (p2[0] - p1[0])
            py = p1[1] + t * (p2[1] - p1[1])
            gx, gy = to_grid(px, py)
            if grid[gy][gx] == " ":
                grid[gy][gx] = "·"

    # Draw lines of sight to visible threats
    vis_threat_ids = {tv.threat_id for tv in visible_threats}
    for threat in world.threats:
        if threat.id in vis_threat_ids:
            tx, ty = threat.centroid
            for t in np.linspace(0.1, 0.9, 10):
                lx = player_pos[0] + t * (tx - player_pos[0])
                ly = player_pos[1] + t * (ty - player_pos[1])
                gx, gy = to_grid(lx, ly)
                if grid[gy][gx] == " ":
                    grid[gy][gx] = "\\" if (tx > player_pos[0] and ty < player_pos[1]) or (tx < player_pos[0] and ty > player_pos[1]) else "/"

    # Draw threats
    for threat in world.threats:
        tx, ty = threat.centroid
        gx, gy = to_grid(tx, ty)
        if threat.id in vis_threat_ids:
            grid[gy][gx] = "◉"
        else:
            grid[gy][gx] = "○"

    # Draw player
    px, py = to_grid(player_pos[0], player_pos[1])
    grid[py][px] = "●"

    # Build ASCII box
    border = "┌" + "─" * (grid_w + 2) + "┐\n"
    content = ""
    for r in range(grid_h):
        content += "│ " + "".join(grid[r]) + " │\n"
    bottom = "└" + "─" * (grid_w + 2) + "┘\n"

    return border + content + bottom


def render_path_frontier_chart(result: PathClearabilityResult, width: int = 35) -> str:
    """Render an ASCII bar chart of the visibility frontier width over trajectory s."""
    if not result.samples:
        return ""

    s_list = [sample.s for sample in result.samples]
    k_list = [sample.k_ici for sample in result.samples]
    max_k = max(max(k_list), 1)

    chart = "Path Concurrency Profile (K_ICI over trajectory s):\n"
    for level in range(max_k, 0, -1):
        line = f"  {level} │ "
        for k in k_list[::max(1, len(k_list) // width)]:
            line += "█" if k >= level else " "
        chart += line + "\n"
    chart += "  0 └──" + "─" * min(len(k_list), width) + "──> s (distance m)\n"
    return chart


def format_clearability_report(
    scenario_name: str,
    world: World,
    path_coords: List[Tuple[float, float]],
    result: PathClearabilityResult
) -> str:
    """Format full scientific diagnostic report for a scenario."""
    last_sample = result.samples[-1] if result.samples else None
    mid_sample = result.samples[len(result.samples) // 2] if result.samples else None
    eval_sample = mid_sample or last_sample

    vis_threats = eval_sample.visible_threats if eval_sample else []
    player_pos = eval_sample.pos if eval_sample else path_coords[0]

    ascii_map = render_ascii_map(world, player_pos, path_coords, vis_threats)
    frontier_chart = render_path_frontier_chart(result)

    report = f"=======================================================================\n"
    report += f"  SCENARIO: {scenario_name}\n"
    report += f"=======================================================================\n\n"
    report += ascii_map + "\n"
    report += f"Trajectory Evaluation:\n"
    report += f"  • Path Length:            {result.path_length_m:.2f} m ({result.duration_s:.2f} s)\n"
    report += f"  • Peak K_ICI (Clique):    {result.peak_k_ici}\n"
    report += f"  • Optimal Lateness L*:    {result.schedule_result.optimal_max_lateness_s:+.3f} s\n"
    report += f"  • Lat-Optimal Frontier:   W_L* = {result.schedule_result.max_frontier_width}\n"
    report += f"  • Min Unconstrained W*:   W* = {result.schedule_result.unconstrained_min_frontier_width}\n"
    feas_w = str(result.schedule_result.feasible_min_frontier_width) if result.schedule_result.feasible_min_frontier_width is not None else "Infeasible"
    report += f"  • Min Feasible W_feas*:   {feas_w}\n"
    report += f"  • Service Solvable:       {'✔ PASS (Solvable)' if result.is_solvable else '✖ FAIL (Unsolvable Deadlines Missed)'}\n"
    if not result.is_solvable:
        report += f"  • Missed Threats:         {', '.join(result.schedule_result.unresolved_deadlines_missed)}\n"
    report += f"  • Optimal Clearing Order: {' -> '.join(result.schedule_result.optimal_clearing_order) or 'None'}\n"
    report += f"  • First Reveals:          " + ", ".join(f"{tid} at {s:.2f}m" for tid, s in result.reveals.items()) + "\n"
    b = result.schedule_result.baselines
    report += f"  • Classical OR Baselines: Static Overlap={b.static_overlap_width}, Min Slack={b.min_slack_s:+.2f}s, Workload={b.total_service_workload_s:.2f}s, Max Setup={b.max_setup_s:.2f}s\n\n"
    report += frontier_chart + "\n"
    return report
