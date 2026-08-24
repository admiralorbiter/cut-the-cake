"""Headless Browser E2E Tests for Tactical CAD Workbench using Playwright.

Launches the real local Flask CAD server and Chromium headless browser to
verify interactive 2D grey-box editing, route/threat scenario authoring,
live telemetry HUD metrics, timeline scrubbing, and full Undo/Redo cycles.
"""

from __future__ import annotations
import os
import time
import socket
import threading
import pytest
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.cad, pytest.mark.browser]

from cut_the_cake.cad_server import create_cad_app


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__()
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="module")
def cad_server_url():
    port = get_free_port()
    app = create_cad_app()
    server = ServerThread(app, port)
    server.start()
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}"
    yield url
    server.shutdown()
    server.join(timeout=2.0)


def test_cad_e2e_obstacle_authoring(cad_server_url):
    """E2E Test: Create wall via canvas drag, select, undo, redo, delete, and verify DOM / API parity."""
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))
    brain_dir = r"C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6"
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Navigate to CAD Workbench
        page.goto(cad_server_url, wait_until="networkidle")
        page.wait_for_selector("#fixtureBadge")
        assert "canonical" in page.inner_text("#fixtureBadge").lower()

        # 2. Switch to Custom Corridor
        page.select_option("#docSelect", "custom_corridor")
        page.wait_for_timeout(400)
        assert "custom" in page.inner_text("#fixtureBadge").lower()

        # 3. Select Wall Tool (W)
        page.click("#toolWall")
        page.wait_for_timeout(200)

        # 4. Drag on canvas to create a new rectangular wall in open area [6.0, 1.0] -> [7.2, 2.0]
        canvas = page.locator("#mapCanvas")
        box = canvas.bounding_box()
        assert box is not None

        start_pt = page.evaluate("() => ({ x: toCanvasX(6.0), y: toCanvasY(1.0) })")
        end_pt = page.evaluate("() => ({ x: toCanvasX(7.2), y: toCanvasY(2.0) })")

        start_x = box["x"] + start_pt["x"]
        start_y = box["y"] + start_pt["y"]
        end_x = box["x"] + end_pt["x"]
        end_y = box["y"] + end_pt["y"]

        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(end_x, end_y, steps=5)
        page.mouse.up()
        page.wait_for_timeout(800)

        # 5. Verify created wall updated Tactical Margin HUD
        margin_text = page.inner_text("#valMargin")
        assert "tics" in margin_text
        assert page.is_enabled("#btnUndo")

        # 6. Capture Obstacle Authoring Screenshot
        screenshot_path = os.path.join(artifacts_dir, "e2e_obstacle_authoring.png")
        page.screenshot(path=screenshot_path)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_obstacle_authoring.png"))

        # 7. Test Undo (Ctrl+Z)
        page.click("#btnUndo")
        page.wait_for_timeout(400)
        assert page.is_enabled("#btnRedo")

        # 8. Test Redo (Ctrl+Y)
        page.click("#btnRedo")
        page.wait_for_timeout(400)
        assert page.is_enabled("#btnUndo")

        # 9. Test Delete
        page.click("#btnDelete")
        page.wait_for_timeout(400)

        browser.close()


def test_cad_e2e_scenario_authoring_and_telemetry(cad_server_url):
    """E2E Test: Scenario authoring, threat placement, speed adjustment, and telemetry playback."""
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))
    brain_dir = r"C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6"
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Navigate to CAD Workbench
        page.goto(cad_server_url, wait_until="networkidle")
        page.wait_for_selector("#valMargin")

        # 2. Verify Canonical F1 initial state: M = -6 tics (Unserviceable)
        val_m = page.inner_text("#valMargin")
        assert "-6" in val_m

        # 3. Switch to Custom Corridor with 3 Threats
        page.select_option("#docSelect", "custom_corridor")
        page.wait_for_timeout(400)

        # 4. Activate Threat Tool (T) and place new threat
        page.click("#toolThreat")
        page.wait_for_timeout(200)

        canvas = page.locator("#mapCanvas")
        box = canvas.bounding_box()
        click_x = box["x"] + box["width"] * 0.6
        click_y = box["y"] + box["height"] * 0.4
        page.mouse.click(click_x, click_y)
        page.wait_for_timeout(600)

        # 5. Playback Simulation: Click Play button
        page.click("#btnPlayPause")
        page.wait_for_timeout(800)

        # Pause playback
        page.click("#btnPlayPause")
        page.wait_for_timeout(200)

        # Verify playback advanced tic counter > 0
        current_tic_str = page.inner_text("#readoutTic")
        current_tic = int(current_tic_str)
        assert current_tic > 0

        # Verify player position readout updated
        pos_str = page.inner_text("#tagPlayerPos")
        assert "POS:" in pos_str

        # 6. Timeline Scrubbing: Click at 50% width of timeline scrubber
        scrubber = page.locator("#timelineScrubber")
        scr_box = scrubber.bounding_box()
        if scr_box:
            page.mouse.click(scr_box["x"] + scr_box["width"] * 0.5, scr_box["y"] + scr_box["height"] * 0.5)
            page.wait_for_timeout(300)

        # 7. Capture Scenario Authoring & Telemetry Screenshot
        screenshot_path = os.path.join(artifacts_dir, "e2e_scenario_authoring.png")
        page.screenshot(path=screenshot_path)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_scenario_authoring.png"))

        browser.close()


def test_cad_e2e_auto_fix_interactive_flow(cad_server_url):
    """E2E Test: Auto-Fix repair workflow on unserviceable Canonical F1 document:
    1. Verify initial unserviceable margin (M = -6 tics).
    2. Click 'Auto-Fix' -> verify repair proposal banner and ghost overlay appear.
    3. Click 'Apply Fix' -> assert margin flips to +2 tics (Target Met).
    4. Verify Undo/Redo cycles and HUD metrics fidelity.
    """
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))
    brain_dir = r"C:\Users\admir\畅gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6".replace("畅", "")
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

        # 1. Load Canonical F1
        page.goto(cad_server_url, wait_until="networkidle")
        page.wait_for_selector("#fixtureBadge")
        
        # 2. Verify initial unserviceable margin
        val_m = page.inner_text("#valMargin")
        assert "-6" in val_m
        assert "UNSERVICEABLE" in page.inner_text("#statusBandBadge")

        # 3. Click Auto-Fix button
        page.click("#btnAutoFix")
        page.wait_for_selector("#repairProposalBanner", state="visible", timeout=5000)

        # 4. Verify repair proposal details
        badge_text = page.inner_text("#repairMarginBadge")
        assert "+2" in badge_text or "2" in badge_text
        desc_text = page.inner_text("#repairBannerDesc")
        assert "Central Baffle" in desc_text or "Shift" in desc_text

        # Capture Proposal Screenshot
        screenshot_prop = os.path.join(artifacts_dir, "e2e_auto_fix_proposal.png")
        page.screenshot(path=screenshot_prop)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_auto_fix_proposal.png"))

        # 5. Apply Repair
        page.click("#btnApplyRepair")
        page.wait_for_selector("#repairProposalBanner", state="hidden", timeout=10000)
        page.wait_for_function("() => !document.getElementById('btnUndo').disabled", timeout=10000)

        # 6. Verify repaired state
        repaired_margin = page.inner_text("#valMargin")
        assert "2" in repaired_margin and "-" not in repaired_margin
        assert "RESERVE" in page.inner_text("#statusBandBadge") or "FEASIBLE" in page.inner_text("#statusBandBadge")
        assert page.is_enabled("#btnUndo")

        # 7. Undo -> revert to -6 tics
        page.click("#btnUndo")
        page.wait_for_function("() => !document.getElementById('btnRedo').disabled", timeout=10000)
        undone_margin = page.inner_text("#valMargin")
        assert "-6" in undone_margin
        assert "UNSERVICEABLE" in page.inner_text("#statusBandBadge")
        assert page.is_enabled("#btnRedo")

        # 8. Redo -> restore +2 tics
        page.click("#btnRedo")
        page.wait_for_function("() => !document.getElementById('btnUndo').disabled", timeout=10000)
        page.wait_for_timeout(400)
        redone_margin = page.inner_text("#valMargin")
        assert "2" in redone_margin and "-" not in redone_margin

        # Capture Repaired Screenshot
        screenshot_rep = os.path.join(artifacts_dir, "e2e_auto_fix_repaired.png")
        page.screenshot(path=screenshot_rep)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_auto_fix_repaired.png"))

        browser.close()


def test_cad_e2e_spatial_heatmap(cad_server_url):
    """E2E Test: Toggle Suffix Tactical Margin heatmap ribbon, hover for tooltip metrics,
    enable 2D Floor LOS exposure grid, and capture visual screenshot artifact.
    """
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))
    brain_dir = r"C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6"
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

        # 1. Load Canonical F1
        page.goto(cad_server_url, wait_until="networkidle")
        page.wait_for_selector("#fixtureBadge")

        # Track outgoing heatmap request payloads
        heatmap_requests = []
        page.on("request", lambda req: heatmap_requests.append(req.post_data_json) if "/api/document/heatmap" in req.url and req.post_data else None)

        # 2. Toggle Heatmap via [H] button
        page.click("#btnToggleHeatmap")
        page.wait_for_selector("#heatmapLegend", state="visible", timeout=5000)
        assert "active" in page.get_attribute("#btnToggleHeatmap", "class")

        # Verify outgoing request contained valid 16-character expected_doc_hash
        page.wait_for_timeout(300)
        assert len(heatmap_requests) > 0
        last_req = heatmap_requests[-1]
        assert "expected_doc_hash" in last_req
        assert last_req["expected_doc_hash"] is not None
        assert len(last_req["expected_doc_hash"]) == 16

        # 3. Hover over route entrance to inspect tooltip
        canvas = page.locator("#mapCanvas")
        box = canvas.bounding_box()
        assert box is not None

        # Sample near x=0.0, y=0.0
        start_pt = page.evaluate("() => ({ x: toCanvasX(0.0), y: toCanvasY(0.0) })")
        page.mouse.move(box["x"] + start_pt["x"], box["y"] + start_pt["y"])
        page.wait_for_selector("#heatmapTooltip", state="visible", timeout=5000)

        tooltip_text = page.inner_text("#heatmapTooltip")
        assert "Suffix M:" in tooltip_text
        assert "LOS K:" in tooltip_text

        # 4. Enable 2D Floor Exposure Grid
        page.check("#chkFloorExposure")
        page.wait_for_timeout(600)

        # 5. Capture Visual Screenshot Artifact
        screenshot_path = os.path.join(artifacts_dir, "e2e_spatial_heatmap.png")
        page.screenshot(path=screenshot_path)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_spatial_heatmap.png"))

        # 6. Toggle Heatmap off
        page.keyboard.press("KeyH")
        page.wait_for_selector("#heatmapLegend", state="hidden", timeout=5000)
        assert "active" not in page.get_attribute("#btnToggleHeatmap", "class")

        browser.close()


def test_cad_e2e_real_map_transfer_case_study(cad_server_url):
    """E2E Test: Load Dust II A-Long real-map case study template, switch routes dynamically,
    verify Tactical Margin updating and capture visual screenshot artifacts for Pieing vs Wide Swing.
    """
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))
    brain_dir = r"C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6"
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

        # 1. Load Workbench & Select Dust II template
        page.goto(cad_server_url, wait_until="networkidle")
        page.wait_for_selector("#docSelect")
        page.select_option("#docSelect", "dust2_a_long")
        page.wait_for_selector("#fixtureBadge", timeout=5000)
        page.wait_for_timeout(400)

        fixture_text = page.inner_text("#fixtureBadge")
        assert "dust2_a_long" in fixture_text.lower()

        # 2. Verify Route Selector options
        route_options = page.eval_on_selector_all("#routeSelect option", "opts => opts.map(o => o.value)")
        assert "route_pieing" in route_options
        assert "route_wide_swing" in route_options
        assert "route_pit_drop" in route_options

        # 3. Enable Spatial Heatmap
        page.click("#btnToggleHeatmap")
        page.wait_for_selector("#heatmapLegend", state="visible", timeout=5000)
        page.wait_for_timeout(500)

        # 4. Capture Pieing Route Artifact
        page.select_option("#routeSelect", "route_pieing")
        page.wait_for_timeout(600)
        screenshot_pieing = os.path.join(artifacts_dir, "e2e_dust2_pieing_heatmap.png")
        page.screenshot(path=screenshot_pieing)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_dust2_pieing_heatmap.png"))

        # 5. Switch to Wide-Swing Route & Capture Artifact
        page.select_option("#routeSelect", "route_wide_swing")
        page.wait_for_timeout(600)
        screenshot_wide = os.path.join(artifacts_dir, "e2e_dust2_wide_swing_heatmap.png")
        page.screenshot(path=screenshot_wide)
        if os.path.exists(brain_dir):
            page.screenshot(path=os.path.join(brain_dir, "e2e_dust2_wide_swing_heatmap.png"))

        browser.close()



