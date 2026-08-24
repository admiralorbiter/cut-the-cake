/**
 * Tactical CAD (Cut the Cake) - Milestone 2C Gray-Box Obstacle Authoring Engine
 * 
 * Strict boundary:
 * - Authoritative Python CADDocument operations: Create, Translate, Resize, Rotate, Delete.
 * - Server-side undo/redo document history snapshots.
 * - Select tool (V, Esc): Move body, 4 corner resize handles with pinned anchor, 1 top rotation handle.
 * - Rectangle Wall tool (R): Live rubber-band preview box (0.05m snap, min 0.10m), commits to Python.
 * - Delete (Del, Backspace): Removes selected obstacle, recomputes authoritative margin.
 * - Fast analysis during drag; full telemetry on pointer release.
 */

// Application State
let activeDoc = null;
let baselineDoc = null;
let currentAnalysis = null;
let currentTic = 0;
let isPlaying = false;
let playbackSpeed = 1.0;
let animTimer = null;

// Tool & Interaction State
let currentTool = 'select'; // 'select' | 'rectangle'
let selectedObstacleId = null;
let canUndo = false;
let canRedo = false;

// Dragging & Transform Modes
let interactionMode = null; // 'create_rect' | 'translate_body' | 'resize_corner' | 'rotate_handle'
let activeResizeHandle = null; // 'nw' | 'ne' | 'se' | 'sw'
let dragStartClientX = 0;
let dragStartClientY = 0;
let dragStartArenaX = 0;
let dragStartArenaY = 0;

// Transform live preview deltas
let previewDx = 0.00;
let previewDy = 0.00;
let previewAngleDeg = 0.00;
let previewRect = null; // { x1, y1, x2, y2 } in meters
let activeRepairPreview = null; // Auto-Fix proposed repair result (M2E)

// Spatial Heatmap State (Milestone 2F)
let showHeatmap = false;
let showFloorExposure = false;
let cachedHeatmapData = null;
let hoveredHeatmapSample = null;

let clientRevision = 0;
let latestRequestedRevision = 0;
let latestAppliedRevision = 0;
let activeAbortController = null;
let debounceTimer = null;
let invalidCandidateReason = null;

// DOM Elements
const canvas = document.getElementById('mapCanvas');
const ctx = canvas.getContext('2d');
const viewportContainer = document.getElementById('viewportContainer');

const docSelect = document.getElementById('docSelect');
const fixtureBadge = document.getElementById('fixtureBadge');
const evidenceBadge = document.getElementById('evidenceBadge');
const latencyBadge = document.getElementById('latencyBadge');
const btnResetDoc = document.getElementById('btnResetDoc');
const btnExportDoc = document.getElementById('btnExportDoc');

// CAD Authoring Toolbar Elements
const toolSelect = document.getElementById('toolSelect');
const toolWall = document.getElementById('toolWall');
const toolRoute = document.getElementById('toolRoute');
const toolThreat = document.getElementById('toolThreat');
const btnUndo = document.getElementById('btnUndo');
const btnRedo = document.getElementById('btnRedo');
const btnDelete = document.getElementById('btnDelete');
const btnAutoFix = document.getElementById('btnAutoFix');
const btnCardAutoFix = document.getElementById('btnCardAutoFix');
const btnToggleHeatmap = document.getElementById('btnToggleHeatmap');
const heatmapLegend = document.getElementById('heatmapLegend');
const chkFloorExposure = document.getElementById('chkFloorExposure');
const heatmapTooltip = document.getElementById('heatmapTooltip');
const repairProposalBanner = document.getElementById('repairProposalBanner');
const repairMarginBadge = document.getElementById('repairMarginBadge');
const repairBannerDesc = document.getElementById('repairBannerDesc');
const btnApplyRepair = document.getElementById('btnApplyRepair');
const btnDismissRepair = document.getElementById('btnDismissRepair');
const dragHintText = document.getElementById('dragHintText');

// Hero Card
const statusBandBadge = document.getElementById('statusBandBadge');
const valMargin = document.getElementById('valMargin');
const valMarginMs = document.getElementById('valMarginMs');
const valSelectedName = document.getElementById('valSelectedName');
const valDisp = document.getElementById('valDisp');
const valLStar = document.getElementById('valLStar');
const valFeasibility = document.getElementById('valFeasibility');
const valStaggerGap = document.getElementById('valStaggerGap');
const valEngineStatus = document.getElementById('valEngineStatus');

// Inspector Cards
const obstacleCard = document.getElementById('obstacleCard');
const valObsIdName = document.getElementById('valObsIdName');
const valObsCenter = document.getElementById('valObsCenter');
const valObsDimensions = document.getElementById('valObsDimensions');
const valObsRotation = document.getElementById('valObsRotation');

const routeCard = document.getElementById('routeCard');
const valRouteIdName = document.getElementById('valRouteIdName');
const inputRouteSpeed = document.getElementById('inputRouteSpeed');
const valRouteWptCount = document.getElementById('valRouteWptCount');

const threatCard = document.getElementById('threatCard');
const valThreatIdName = document.getElementById('valThreatIdName');
const valThreatAnchor = document.getElementById('valThreatAnchor');
const inputThreatDueWindow = document.getElementById('inputThreatDueWindow');
const inputThreatServiceDuration = document.getElementById('inputThreatServiceDuration');

const threatCountBadge = document.getElementById('threatCountBadge');
const threatListContainer = document.getElementById('threatListContainer');
const whyText = document.getElementById('whyText');

const controllerStateBadge = document.getElementById('controllerStateBadge');
const valActiveTarget = document.getElementById('valActiveTarget');
const valRouteDist = document.getElementById('valRouteDist');
const valMoveSpeed = document.getElementById('valMoveSpeed');
const valSlewSpeed = document.getElementById('valSlewSpeed');

const tagPlayerPos = document.getElementById('tagPlayerPos');
const tagReticle = document.getElementById('tagReticle');
const tagSelectedObs = document.getElementById('tagSelectedObs');
const pendingCommitBanner = document.getElementById('pendingCommitBanner');
const footerEl = document.querySelector('footer');

const timelineScrubber = document.getElementById('timelineScrubber');
const timelineProgress = document.getElementById('timelineProgress');
const timelineHead = document.getElementById('timelineHead');
const eventMarkerLayer = document.getElementById('eventMarkerLayer');

const btnPlayPause = document.getElementById('btnPlayPause');
const btnStepBack = document.getElementById('btnStepBack');
const btnStepFwd = document.getElementById('btnStepFwd');
const btnReset = document.getElementById('btnReset');
const btnSpeed05 = document.getElementById('btnSpeed05');
const btnSpeed10 = document.getElementById('btnSpeed10');
const btnSpeed20 = document.getElementById('btnSpeed20');

const readoutTic = document.getElementById('readoutTic');
const readoutTotalTics = document.getElementById('readoutTotalTics');
const readoutTime = document.getElementById('readoutTime');
const readoutTotalTime = document.getElementById('readoutTotalTime');

// Dynamic Coordinate Transformation (Meters -> Canvas Pixels)
let viewTransform = {
  scale: 60,
  offsetX: 80,
  offsetY: 250,
  minX: 0,
  maxX: 12,
  minY: -3.5,
  maxY: 3.5
};

// Initialize Application
async function init() {
  setupUI();
  setupCanvas();
  setupInteraction();
  setupKeyboardShortcuts();
  await loadDocumentByName('canonical_f1');
}

function setTool(tool) {
  currentTool = tool;
  if (toolSelect) toolSelect.classList.toggle('active', tool === 'select');
  if (toolWall) toolWall.classList.toggle('active', tool === 'rectangle');
  if (toolRoute) toolRoute.classList.toggle('active', tool === 'route');
  if (toolThreat) toolThreat.classList.toggle('active', tool === 'threat');

  if (tool === 'rectangle') {
    canvas.style.cursor = 'crosshair';
    dragHintText.innerHTML = '📐 <strong>Wall Tool [W]:</strong> Click and drag on arena canvas to create a new rectangular wall';
  } else if (tool === 'route') {
    canvas.style.cursor = 'crosshair';
    dragHintText.innerHTML = '⮑ <strong>Route Tool [R]:</strong> Click points to draw polyline route';
  } else if (tool === 'threat') {
    canvas.style.cursor = 'crosshair';
    dragHintText.innerHTML = '🎯 <strong>Threat Tool [T]:</strong> Click anywhere inside boundary to place a new hostile threat';
  } else {
    canvas.style.cursor = 'default';
    dragHintText.innerHTML = '🖱️ <strong>Interactive 2D CAD:</strong> [V] Select | [W] Wall | [R] Route | [T] Threat | [Del] Delete | [Ctrl+Z] Undo';
  }
  drawMap();
}

function updateUndoRedoButtons(undoAvailable, redoAvailable) {
  canUndo = !!undoAvailable;
  canRedo = !!redoAvailable;
  if (btnUndo) btnUndo.disabled = !canUndo;
  if (btnRedo) btnRedo.disabled = !canRedo;
  if (btnDelete) btnDelete.disabled = !selectedObstacleId;
}

function setupUI() {
  // Document Switcher
  docSelect.addEventListener('change', async () => {
    await loadDocumentByName(docSelect.value);
  });

  // Tool Selection
  if (toolSelect) toolSelect.addEventListener('click', () => setTool('select'));
  if (toolWall) toolWall.addEventListener('click', () => setTool('rectangle'));
  if (toolRoute) toolRoute.addEventListener('click', () => setTool('route'));
  if (toolThreat) toolThreat.addEventListener('click', () => setTool('threat'));

  // Route & Threat Parameter Inputs
  if (inputRouteSpeed) {
    inputRouteSpeed.addEventListener('change', async () => {
      const spd = parseFloat(inputRouteSpeed.value);
      if (spd > 0 && activeDoc && activeDoc.geometry && activeDoc.geometry.routes && activeDoc.geometry.routes.length > 0) {
        const rId = activeDoc.geometry.routes[0].id;
        try {
          const resp = await fetch('/api/document/update_route_speed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ route_id: rId, v_move_mps: spd, commit: true })
          });
          if (resp.ok) {
            const data = await resp.json();
            activeDoc = data.candidate_document;
            applyAnalysisResponse(data, true);
            updateUndoRedoButtons(data.can_undo, data.can_redo);
            drawMap();
          }
        } catch (err) {
          console.warn('Update route speed error:', err);
        }
      }
    });
  }

  if (inputThreatDueWindow) {
    inputThreatDueWindow.addEventListener('change', async () => {
      const dw = parseFloat(inputThreatDueWindow.value);
      if (dw > 0 && activeDoc && activeDoc.geometry && activeDoc.geometry.threats && activeDoc.geometry.threats.length > 0) {
        const tId = activeDoc.geometry.threats[0].id;
        try {
          const resp = await fetch('/api/document/update_threat_due_window', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ threat_id: tId, due_window_s: dw, commit: true })
          });
          if (resp.ok) {
            const data = await resp.json();
            activeDoc = data.candidate_document;
            applyAnalysisResponse(data, true);
            updateUndoRedoButtons(data.can_undo, data.can_redo);
            drawMap();
          }
        } catch (err) {
          console.warn('Update due window error:', err);
        }
      }
    });
  }

  if (inputThreatServiceDuration) {
    inputThreatServiceDuration.addEventListener('change', async () => {
      const sd = parseFloat(inputThreatServiceDuration.value);
      if (sd > 0 && activeDoc && activeDoc.geometry && activeDoc.geometry.threats && activeDoc.geometry.threats.length > 0) {
        const tId = activeDoc.geometry.threats[0].id;
        try {
          const resp = await fetch('/api/document/update_threat_service_duration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ threat_id: tId, service_duration_s: sd, commit: true })
          });
          if (resp.ok) {
            const data = await resp.json();
            activeDoc = data.candidate_document;
            applyAnalysisResponse(data, true);
            updateUndoRedoButtons(data.can_undo, data.can_redo);
            drawMap();
          }
        } catch (err) {
          console.warn('Update service duration error:', err);
        }
      }
    });
  }

  // Undo / Redo
  if (btnUndo) btnUndo.addEventListener('click', handleUndo);
  if (btnRedo) btnRedo.addEventListener('click', handleRedo);
  if (btnDelete) btnDelete.addEventListener('click', handleDeleteSelected);

  // Auto-Fix Mixed-Initiative Repair (M2E)
  if (btnAutoFix) btnAutoFix.addEventListener('click', handleSuggestAutoFix);
  if (btnCardAutoFix) btnCardAutoFix.addEventListener('click', handleSuggestAutoFix);
  if (btnApplyRepair) btnApplyRepair.addEventListener('click', handleApplyRepair);
  if (btnDismissRepair) btnDismissRepair.addEventListener('click', handleDismissRepair);

  // Suffix Tactical Margin & Spatial Heatmap (M2F)
  if (btnToggleHeatmap) btnToggleHeatmap.addEventListener('click', toggleHeatmap);
  if (chkFloorExposure) {
    chkFloorExposure.addEventListener('change', async () => {
      showFloorExposure = chkFloorExposure.checked;
      if (showHeatmap) {
        await fetchHeatmapData();
      }
      drawMap();
    });
  }

  // Document Reset
  btnResetDoc.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/document/reset', { method: 'POST' });
      if (resp.ok) {
        const data = await resp.json();
        activeDoc = data.document;
        activeRepairPreview = null;
        if (repairProposalBanner) repairProposalBanner.style.display = 'none';
        selectedObstacleId = getObstacles().length > 0 ? getObstacles()[0].id : null;
        updateUndoRedoButtons(data.can_undo, data.can_redo);
        resetTransformState();
        await requestInitialAnalysis();
      }
    } catch (err) {
      console.warn('Reset error:', err);
    }
  });

  // Export JSON
  btnExportDoc.addEventListener('click', () => {
    if (!activeDoc) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(activeDoc, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `${activeDoc.document_id || 'document'}_v1.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  });

  // Playback Controls
  btnPlayPause.addEventListener('click', togglePlay);
  btnStepBack.addEventListener('click', () => stepTic(-1));
  btnStepFwd.addEventListener('click', () => stepTic(1));
  btnReset.addEventListener('click', () => setTic(0));

  // Speed Controls
  btnSpeed05.addEventListener('click', () => setSpeed(0.5, btnSpeed05));
  btnSpeed10.addEventListener('click', () => setSpeed(1.0, btnSpeed10));
  btnSpeed20.addEventListener('click', () => setSpeed(2.0, btnSpeed20));

  // Timeline Scrubbing
  timelineScrubber.addEventListener('click', (e) => {
    if (footerEl.classList.contains('disabled')) return;
    const totalTics = getTotalTics();
    const rect = timelineScrubber.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const targetTic = Math.round(ratio * totalTics);
    setTic(targetTic);
  });

  window.addEventListener('resize', resizeCanvas);
}

async function handleSuggestAutoFix() {
  if (!activeDoc) return;
  try {
    const resp = await fetch('/api/document/auto_fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_margin_tics: 2, commit: false })
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.success && data.repaired_document) {
        activeRepairPreview = data;
        if (repairProposalBanner) {
          repairProposalBanner.style.display = 'flex';
          if (repairMarginBadge) {
            repairMarginBadge.textContent = `M = +${data.repaired_margin_tics} tics`;
          }
          if (repairBannerDesc) {
            repairBannerDesc.textContent = data.repair_description;
          }
        }
        drawMap();
      } else if (data.no_repair_needed) {
        alert(data.repair_description || 'Encounter already meets tactical margin target.');
      } else {
        alert(data.repair_description || data.error_reason || 'Could not find viable repair within budget.');
      }
    }
  } catch (err) {
    console.warn('Auto-Fix error:', err);
  }
}

async function handleApplyRepair() {
  if (!activeRepairPreview) return;
  try {
    const resp = await fetch('/api/document/auto_fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_margin_tics: 2,
        commit: true,
        expected_doc_hash: activeRepairPreview.source_doc_hash
      })
    });
    const data = await resp.json();
    if (resp.status === 409 || data.status === 'STALE_REPAIR_PROPOSAL') {
      alert('⚠️ Stale Repair Proposal: Document was modified after proposal was generated. Please re-run Auto-Fix.');
      handleDismissRepair();
      return;
    }
    if (resp.ok && data.success && data.repaired_document) {
      activeDoc = data.repaired_document;
      activeRepairPreview = null;
      if (repairProposalBanner) repairProposalBanner.style.display = 'none';
      if (data.repaired_analysis) {
        applyAnalysisResponse(data.repaired_analysis, true);
      }
      updateUndoRedoButtons(data.can_undo, data.can_redo);
      drawMap();
    }
  } catch (err) {
    console.warn('Apply repair error:', err);
  }
}

function handleDismissRepair() {
  activeRepairPreview = null;
  if (repairProposalBanner) repairProposalBanner.style.display = 'none';
  drawMap();
}

async function toggleHeatmap() {
  showHeatmap = !showHeatmap;
  if (btnToggleHeatmap) btnToggleHeatmap.classList.toggle('active', showHeatmap);
  if (heatmapLegend) heatmapLegend.style.display = showHeatmap ? 'flex' : 'none';
  if (!showHeatmap) {
    if (heatmapTooltip) heatmapTooltip.style.display = 'none';
    hoveredHeatmapSample = null;
  } else {
    await fetchHeatmapData();
  }
  drawMap();
}

async function fetchHeatmapData() {
  if (!activeDoc) return;
  try {
    const activeRouteId = getRoutes().length > 0 ? getRoutes()[0].id : null;
    const resp = await fetch('/api/document/heatmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        route_id: activeRouteId,
        include_floor_grid: showFloorExposure,
        grid_step_m: 0.25
      })
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.is_valid) {
        cachedHeatmapData = data;
        drawMap();
      }
    }
  } catch (err) {
    console.warn('Heatmap fetch error:', err);
  }
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Avoid triggering when focused in a text or numeric input field
    const targetTag = e.target.tagName.toLowerCase();
    const isTextInput = (targetTag === 'textarea' || (targetTag === 'input' && (e.target.type === 'text' || e.target.type === 'number')) || targetTag === 'select');
    if (isTextInput) return;

    if (e.key === 'v' || e.key === 'V' || e.key === 'Escape') {
      setTool('select');
    } else if (e.key === 'w' || e.key === 'W') {
      setTool('rectangle');
    } else if (e.key === 'r' || e.key === 'R') {
      setTool('route');
    } else if (e.key === 't' || e.key === 'T') {
      setTool('threat');
    } else if (e.key === 'a' || e.key === 'A') {
      handleSuggestAutoFix();
    } else if (e.key === 'h' || e.key === 'H') {
      toggleHeatmap();
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selectedObstacleId) {
        e.preventDefault();
        handleDeleteSelected();
      }
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) {
      e.preventDefault();
      handleUndo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || e.key === 'Y' || ((e.key === 'z' || e.key === 'Z') && e.shiftKey))) {
      e.preventDefault();
      handleRedo();
    }
  });
}

function resetTransformState() {
  previewDx = 0.00;
  previewDy = 0.00;
  previewAngleDeg = 0.00;
  previewRect = null;
  interactionMode = null;
  activeResizeHandle = null;
  invalidCandidateReason = null;
}

async function loadDocumentByName(docName) {
  try {
    const resp = await fetch('/api/document/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: docName })
    });
    if (resp.ok) {
      const data = await resp.json();
      activeDoc = data.document;
      baselineDoc = JSON.parse(JSON.stringify(data.document));
      updateUndoRedoButtons(data.can_undo, data.can_redo);
    }
  } catch (err) {
    console.warn('Server offline, loading fallback');
  }

  if (!activeDoc) return;

  const obstacles = getObstacles();
  selectedObstacleId = obstacles.length > 0 ? obstacles[0].id : null;
  resetTransformState();
  setupDynamicBounds();
  await requestInitialAnalysis();
}

async function handleUndo() {
  if (!canUndo) return;
  try {
    const resp = await fetch('/api/document/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
      const data = await resp.json();
      applyAnalysisResponse(data, true);
      updateUndoRedoButtons(data.can_undo, data.can_redo);
    }
  } catch (err) {
    console.warn('Undo error:', err);
  }
}

async function handleRedo() {
  if (!canRedo) return;
  try {
    const resp = await fetch('/api/document/redo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
      const data = await resp.json();
      applyAnalysisResponse(data, true);
      updateUndoRedoButtons(data.can_undo, data.can_redo);
    }
  } catch (err) {
    console.warn('Redo error:', err);
  }
}

async function handleDeleteSelected() {
  if (!selectedObstacleId) return;
  try {
    const resp = await fetch('/api/document/delete_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ obstacle_id: selectedObstacleId })
    });
    if (resp.ok) {
      const data = await resp.json();
      selectedObstacleId = null;
      applyAnalysisResponse(data, true);
      updateUndoRedoButtons(data.can_undo, data.can_redo);
    }
  } catch (err) {
    console.warn('Delete error:', err);
  }
}

function getObstacles() {
  if (!activeDoc) return [];
  if (activeDoc.geometry && activeDoc.geometry.obstacles) return activeDoc.geometry.obstacles;
  if (activeDoc.obstacles) return activeDoc.obstacles;
  return [];
}

function getBoundary() {
  if (!activeDoc) return [];
  if (activeDoc.geometry && activeDoc.geometry.boundary) return activeDoc.geometry.boundary;
  if (activeDoc.boundary) return activeDoc.boundary;
  return [];
}

function getRoutes() {
  if (!activeDoc) return [];
  if (activeDoc.geometry && activeDoc.geometry.routes) return activeDoc.geometry.routes;
  if (activeDoc.routes) return activeDoc.routes;
  return [];
}

function getThreats() {
  if (!activeDoc) return [];
  if (activeDoc.geometry && activeDoc.geometry.threats) return activeDoc.geometry.threats;
  if (activeDoc.threats) return activeDoc.threats;
  return [];
}

function getTotalTics() {
  if (currentAnalysis && currentAnalysis.telemetry_frames) {
    return Math.max(1, currentAnalysis.telemetry_frames.length - 1);
  }
  return 78;
}

function setupDynamicBounds() {
  const boundary = getBoundary();
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  
  boundary.forEach(([x, y]) => {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  });

  getThreats().forEach(t => {
    const poly = t.polygon || [];
    poly.forEach(([x, y]) => {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    });
  });

  viewTransform.minX = minX;
  viewTransform.maxX = maxX;
  viewTransform.minY = minY;
  viewTransform.maxY = maxY;
  resizeCanvas();
}

function toCanvasX(x) {
  return viewTransform.offsetX + x * viewTransform.scale;
}

function toCanvasY(y) {
  return viewTransform.offsetY - y * viewTransform.scale;
}

function toArenaX(cx) {
  return (cx - viewTransform.offsetX) / viewTransform.scale;
}

function toArenaY(cy) {
  return -(cy - viewTransform.offsetY) / viewTransform.scale;
}

function snap(val, step = 0.05) {
  return Math.round(val / step) * step;
}

// Transform Handles & Hit Testing
function getSelectedObstacleBounds() {
  const obs = getObstacles().find(o => o.id === selectedObstacleId);
  if (!obs || !obs.vertices || obs.vertices.length < 3) return null;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  obs.vertices.forEach(([x, y]) => {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  });
  return { minX, maxX, minY, maxY, cx: (minX + maxX) / 2, cy: (minY + maxY) / 2, width: maxX - minX, height: maxY - minY };
}

function getHandlesForObstacle(obs) {
  if (!obs || !obs.vertices || obs.vertices.length < 3) return null;
  const rawVerts = obs.vertices;
  const isClosed = rawVerts.length > 3 &&
    Math.hypot(rawVerts[0][0] - rawVerts[rawVerts.length - 1][0], rawVerts[0][1] - rawVerts[rawVerts.length - 1][1]) < 1e-4;
  const corners = isClosed ? rawVerts.slice(0, -1) : rawVerts;

  const cx = corners.reduce((sum, v) => sum + v[0], 0) / corners.length;
  const cy = corners.reduce((sum, v) => sum + v[1], 0) / corners.length;

  const cornerHandles = corners.map(([x, y], idx) => ({
    x: toCanvasX(x),
    y: toCanvasY(y),
    handle: String(idx),
    arenaX: x,
    arenaY: y,
    idx: idx
  }));

  // Top edge midpoint for rotation stem
  const sortedByY = [...corners].sort((a, b) => b[1] - a[1]);
  const p1 = sortedByY[0] || [cx, cy];
  const p2 = sortedByY[1] || sortedByY[0] || [cx, cy];
  const topMidX = (p1[0] + p2[0]) / 2;
  const topMidY = (p1[1] + p2[1]) / 2;

  let dirX = topMidX - cx;
  let dirY = topMidY - cy;
  const len = Math.hypot(dirX, dirY);
  if (len > 1e-4) {
    dirX /= len;
    dirY /= len;
  } else {
    dirX = 0;
    dirY = 1;
  }

  const stemArenaX = topMidX + dirX * 0.40;
  const stemArenaY = topMidY + dirY * 0.40;

  return {
    corners: cornerHandles,
    topMid: { x: toCanvasX(topMidX), y: toCanvasY(topMidY) },
    rot: {
      x: toCanvasX(stemArenaX),
      y: toCanvasY(stemArenaY),
      handle: 'rot',
      arenaCx: cx,
      arenaCy: cy
    }
  };
}

function hitTestHandles(cx, cy) {
  const obs = getObstacles().find(o => o.id === selectedObstacleId);
  if (!obs) return null;
  const handles = getHandlesForObstacle(obs);
  if (!handles) return null;

  // 1. Rotation handle check (radius 12px)
  const distRot = Math.hypot(cx - handles.rot.x, cy - handles.rot.y);
  if (distRot <= 12) return { type: 'rot', handle: handles.rot };

  // 2. Corner resize handles check (8px box)
  const hSize = 8;
  for (const h of handles.corners) {
    if (Math.abs(cx - h.x) <= hSize && Math.abs(cy - h.y) <= hSize) {
      return { type: 'resize', handle: h.handle, idx: h.idx };
    }
  }
  return null;
}

function hitTestObstacles(cx, cy) {
  const obstacles = getObstacles();
  for (let i = obstacles.length - 1; i >= 0; i--) {
    const obs = obstacles[i];
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    obs.vertices.forEach(([x, y]) => {
      const px = toCanvasX(x);
      const py = toCanvasY(y);
      minX = Math.min(minX, px);
      maxX = Math.max(maxX, px);
      minY = Math.min(minY, py);
      maxY = Math.max(maxY, py);
    });
    const pad = 6;
    if (cx >= minX - pad && cx <= maxX + pad && cy >= minY - pad && cy <= maxY + pad) {
      return obs;
    }
  }
  return null;
}

// Setup Interactive Canvas Handlers
function setupInteraction() {
  function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  canvas.addEventListener('mousemove', (e) => {
    const pt = getCanvasCoords(e);
    const mx = toArenaX(pt.x);
    const my = toArenaY(pt.y);

    if (interactionMode === 'create_rect') {
      const curX = snap(mx, 0.05);
      const curY = snap(my, 0.05);
      previewRect = {
        x1: Math.min(dragStartArenaX, curX),
        y1: Math.min(dragStartArenaY, curY),
        x2: Math.max(dragStartArenaX, curX),
        y2: Math.max(dragStartArenaY, curY)
      };
      drawMap();
    } else if (interactionMode === 'translate_body') {
      const rawDx = mx - dragStartArenaX;
      const rawDy = my - dragStartArenaY;
      previewDx = snap(rawDx, 0.05);
      previewDy = snap(rawDy, 0.05);

      pendingCommitBanner.style.display = 'block';
      footerEl.classList.add('disabled');

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        requestTranslateAnalysis(selectedObstacleId, previewDx, previewDy, false);
      }, 20);

      drawMap();
    } else if (interactionMode === 'resize_corner') {
      const rawDx = mx - dragStartArenaX;
      const rawDy = my - dragStartArenaY;
      previewDx = snap(rawDx, 0.05);
      previewDy = snap(rawDy, 0.05);

      pendingCommitBanner.style.display = 'block';
      footerEl.classList.add('disabled');

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        requestResizeAnalysis(selectedObstacleId, activeResizeHandle, previewDx, previewDy, false);
      }, 20);

      drawMap();
    } else if (interactionMode === 'rotate_handle') {
      const b = getSelectedObstacleBounds();
      if (b) {
        const angleRad = Math.atan2(my - b.cy, mx - b.cx);
        let angleDeg = -(angleRad * 180 / Math.PI - 90); // 0 at top, clockwise positive
        if (!e.shiftKey) {
          angleDeg = Math.round(angleDeg / 5) * 5; // 5 degree snap
        }
        previewAngleDeg = angleDeg;

        pendingCommitBanner.style.display = 'block';
        footerEl.classList.add('disabled');

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          requestRotateAnalysis(selectedObstacleId, previewAngleDeg, false);
        }, 20);

        drawMap();
      }
    } else {
      // Hover Cursor State
      if (currentTool === 'rectangle') {
        canvas.style.cursor = 'crosshair';
      } else {
        const handleHit = hitTestHandles(pt.x, pt.y);
        if (handleHit) {
          if (handleHit.type === 'rot') canvas.style.cursor = 'grab';
          else if (handleHit.handle === 'nw' || handleHit.handle === 'se') canvas.style.cursor = 'nwse-resize';
          else canvas.style.cursor = 'nesw-resize';
        } else {
          const obsHit = hitTestObstacles(pt.x, pt.y);
          canvas.style.cursor = obsHit ? 'move' : 'default';
        }
      }

      // Heatmap Sample Tooltip & Highlight on Hover
      if (showHeatmap && cachedHeatmapData?.samples) {
        let closestSample = null;
        let closestDistPx = 18;
        for (const s of cachedHeatmapData.samples) {
          const sx = toCanvasX(s.position[0]);
          const sy = toCanvasY(s.position[1]);
          const dPx = Math.hypot(pt.x - sx, pt.y - sy);
          if (dPx < closestDistPx) {
            closestDistPx = dPx;
            closestSample = s;
          }
        }

        if (closestSample) {
          hoveredHeatmapSample = closestSample;
          if (heatmapTooltip) {
            const mText = closestSample.suffix_margin_tics !== null
              ? (closestSample.suffix_margin_tics >= 0 ? `+${closestSample.suffix_margin_tics}` : `${closestSample.suffix_margin_tics}`) + ` tics (${closestSample.status_band})`
              : `None (${closestSample.status_band})`;
            const hText = closestSample.min_deadline_headroom_tics !== null
              ? (closestSample.min_deadline_headroom_tics >= 0 ? `+${closestSample.min_deadline_headroom_tics}` : `${closestSample.min_deadline_headroom_tics}`) + ` tics`
              : `N/A`;

            heatmapTooltip.innerHTML = `<strong>Suffix M:</strong> ${mText} | <strong>Headroom:</strong> ${hText} | <strong>LOS K:</strong> ${closestSample.los_concurrency}`;
            const canvasRect = canvas.getBoundingClientRect();
            heatmapTooltip.style.left = `${canvasRect.left + toCanvasX(closestSample.position[0])}px`;
            heatmapTooltip.style.top = `${canvasRect.top + toCanvasY(closestSample.position[1])}px`;
            heatmapTooltip.style.display = 'block';
          }
          drawMap();
        } else if (hoveredHeatmapSample) {
          hoveredHeatmapSample = null;
          if (heatmapTooltip) heatmapTooltip.style.display = 'none';
          drawMap();
        }
      }
    }
  });

  canvas.addEventListener('mouseleave', () => {
    if (hoveredHeatmapSample) {
      hoveredHeatmapSample = null;
      if (heatmapTooltip) heatmapTooltip.style.display = 'none';
      drawMap();
    }
  });

  canvas.addEventListener('mousedown', (e) => {
    const pt = getCanvasCoords(e);
    const mx = toArenaX(pt.x);
    const my = toArenaY(pt.y);

    if (currentTool === 'rectangle') {
      // Start Rectangle Creation
      interactionMode = 'create_rect';
      dragStartArenaX = snap(mx, 0.05);
      dragStartArenaY = snap(my, 0.05);
      previewRect = {
        x1: dragStartArenaX,
        y1: dragStartArenaY,
        x2: dragStartArenaX,
        y2: dragStartArenaY
      };
      drawMap();
    } else {
      // Select tool: Check handles first, then obstacles
      const handleHit = hitTestHandles(pt.x, pt.y);
      if (handleHit) {
        if (handleHit.type === 'rot') {
          interactionMode = 'rotate_handle';
          dragStartArenaX = mx;
          dragStartArenaY = my;
          previewAngleDeg = 0.0;
          canvas.style.cursor = 'grabbing';
        } else {
          interactionMode = 'resize_corner';
          activeResizeHandle = handleHit.handle;
          dragStartArenaX = mx;
          dragStartArenaY = my;
          previewDx = 0.00;
          previewDy = 0.00;
        }
        drawMap();
        return;
      }

      const hitObs = hitTestObstacles(pt.x, pt.y);
      if (hitObs) {
        selectedObstacleId = hitObs.id;
        interactionMode = 'translate_body';
        dragStartArenaX = mx;
        dragStartArenaY = my;
        previewDx = 0.00;
        previewDy = 0.00;
        canvas.style.cursor = 'grabbing';
        updateUndoRedoButtons(canUndo, canRedo);
        drawMap();
      } else {
        selectedObstacleId = null;
        updateUndoRedoButtons(canUndo, canRedo);
        drawMap();
      }
    }
  });

  window.addEventListener('mouseup', async () => {
    if (interactionMode === 'create_rect') {
      interactionMode = null;
      if (previewRect) {
        const w = previewRect.x2 - previewRect.x1;
        const h = previewRect.y2 - previewRect.y1;
        if (w >= 0.10 && h >= 0.10) {
          await requestCreateObstacle(previewRect.x1, previewRect.y1, previewRect.x2, previewRect.y2);
        }
      }
      previewRect = null;
      setTool('select');
    } else if (interactionMode === 'translate_body') {
      interactionMode = null;
      canvas.style.cursor = 'default';
      pendingCommitBanner.style.display = 'none';
      footerEl.classList.remove('disabled');
      await requestTranslateAnalysis(selectedObstacleId, previewDx, previewDy, true);
    } else if (interactionMode === 'resize_corner') {
      interactionMode = null;
      canvas.style.cursor = 'default';
      pendingCommitBanner.style.display = 'none';
      footerEl.classList.remove('disabled');
      await requestResizeAnalysis(selectedObstacleId, activeResizeHandle, previewDx, previewDy, true);
    } else if (interactionMode === 'rotate_handle') {
      interactionMode = null;
      canvas.style.cursor = 'default';
      pendingCommitBanner.style.display = 'none';
      footerEl.classList.remove('disabled');
      await requestRotateAnalysis(selectedObstacleId, previewAngleDeg, true);
    }
  });
}

// Server Analysis & Mutation Requests
async function requestInitialAnalysis() {
  try {
    const resp = await fetch('/api/document/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_telemetry: true })
    });
    if (resp.ok) {
      const data = await resp.json();
      applyAnalysisResponse(data, true);
    }
  } catch (err) {
    console.warn('Initial analysis error:', err);
  }
}

async function requestCreateObstacle(x1, y1, x2, y2) {
  try {
    const resp = await fetch('/api/document/create_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        x1, y1, x2, y2, commit: true, include_telemetry: true
      })
    });
    const data = await resp.json();
    if (resp.ok && data.is_valid) {
      selectedObstacleId = data.created_obstacle_id;
      applyAnalysisResponse(data, true);
      updateUndoRedoButtons(data.can_undo, data.can_redo);
    } else {
      console.warn('Create rejected:', data.error_reason);
    }
  } catch (err) {
    console.warn('Create request error:', err);
  }
}

async function requestTranslateAnalysis(obsId, dx, dy, commit) {
  if (!obsId) return;
  clientRevision++;
  const thisRev = clientRevision;
  latestRequestedRevision = thisRev;

  try {
    const resp = await fetch('/api/document/translate_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        obstacle_id: obsId,
        dx: dx,
        dy: dy,
        commit: commit,
        client_revision: thisRev,
        include_telemetry: commit
      })
    });
    const data = await resp.json();
    if (data.client_revision !== latestRequestedRevision) return;
    applyAnalysisResponse(data, commit);
    if (commit) updateUndoRedoButtons(data.can_undo, data.can_redo);
  } catch (err) {
    console.warn('Translate error:', err);
  }
}

async function requestResizeAnalysis(obsId, handle, dx, dy, commit) {
  if (!obsId) return;
  clientRevision++;
  const thisRev = clientRevision;
  latestRequestedRevision = thisRev;

  try {
    const resp = await fetch('/api/document/resize_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        obstacle_id: obsId,
        handle: handle,
        dx: dx,
        dy: dy,
        commit: commit,
        client_revision: thisRev,
        include_telemetry: commit
      })
    });
    const data = await resp.json();
    if (data.client_revision !== latestRequestedRevision) return;
    applyAnalysisResponse(data, commit);
    if (commit) updateUndoRedoButtons(data.can_undo, data.can_redo);
  } catch (err) {
    console.warn('Resize error:', err);
  }
}

async function requestRotateAnalysis(obsId, angleDeg, commit) {
  if (!obsId) return;
  clientRevision++;
  const thisRev = clientRevision;
  latestRequestedRevision = thisRev;

  try {
    const resp = await fetch('/api/document/rotate_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        obstacle_id: obsId,
        angle_deg: angleDeg,
        commit: commit,
        client_revision: thisRev,
        include_telemetry: commit
      })
    });
    const data = await resp.json();
    if (data.client_revision !== latestRequestedRevision) return;
    applyAnalysisResponse(data, commit);
    if (commit) updateUndoRedoButtons(data.can_undo, data.can_redo);
  } catch (err) {
    console.warn('Rotate error:', err);
  }
}

function applyAnalysisResponse(data, committed) {
  if (!data.is_valid) {
    invalidCandidateReason = data.error_reason || 'Invalid placement';
    statusBandBadge.textContent = 'INVALID PLACEMENT';
    statusBandBadge.style.background = 'rgba(248, 81, 73, 0.3)';
    statusBandBadge.style.color = 'var(--red)';
    valFeasibility.textContent = 'INVALID GEOMETRY';
    valFeasibility.style.color = 'var(--red)';
    latencyBadge.textContent = `⚡ Analysis: ${data.runtime_ms || 0} ms (Rejected)`;
    latencyBadge.style.color = 'var(--red)';
    drawMap();
    return;
  }

  invalidCandidateReason = null;
  currentAnalysis = data;
  if (data.candidate_document) {
    activeDoc = data.candidate_document;
  }
  if (committed) {
    previewDx = 0.00;
    previewDy = 0.00;
    previewAngleDeg = 0.00;
    cachedHeatmapData = null;
    if (showHeatmap) {
      fetchHeatmapData();
    }
  }
  if (data.can_undo !== undefined || data.can_redo !== undefined) {
    updateUndoRedoButtons(data.can_undo, data.can_redo);
  }

  latencyBadge.textContent = `⚡ Analysis: ${data.runtime_ms} ms`;
  latencyBadge.style.color = '#58a6ff';

  renderTimelineEvents();
  updateView(currentTic);
}

// Playback Helpers
function setSpeed(speed, activeBtn) {
  playbackSpeed = speed;
  [btnSpeed05, btnSpeed10, btnSpeed20].forEach(b => b.style.background = '#172130');
  activeBtn.style.background = '#233145';
  if (isPlaying) {
    pause();
    play();
  }
}

function togglePlay() {
  if (isPlaying) pause();
  else play();
}

function play() {
  if (footerEl.classList.contains('disabled') || !currentAnalysis || !currentAnalysis.telemetry_frames) return;
  const frames = currentAnalysis.telemetry_frames;
  if (currentTic >= frames.length - 1) {
    currentTic = 0;
  }
  isPlaying = true;
  btnPlayPause.textContent = '⏸ Pause';
  btnPlayPause.classList.remove('primary');
  btnPlayPause.style.background = 'var(--amber)';

  const intervalMs = (1000.0 / 35) / playbackSpeed;
  animTimer = setInterval(() => {
    if (currentTic < frames.length - 1) {
      setTic(currentTic + 1);
    } else {
      pause();
    }
  }, intervalMs);
}

function pause() {
  isPlaying = false;
  clearInterval(animTimer);
  btnPlayPause.textContent = '▶ Play';
  btnPlayPause.classList.add('primary');
  btnPlayPause.style.background = '';
}

function stepTic(delta) {
  pause();
  const maxTic = getTotalTics();
  const nextTic = Math.max(0, Math.min(maxTic, currentTic + delta));
  setTic(nextTic);
}

function setTic(tic) {
  currentTic = tic;
  updateView(tic);
}

function setupCanvas() {
  resizeCanvas();
}

function resizeCanvas() {
  const rect = viewportContainer.getBoundingClientRect();
  canvas.width = rect.width - 20;
  canvas.height = rect.height - 20;
  
  const spanX = (viewTransform.maxX - viewTransform.minX) + 1.0;
  const spanY = (viewTransform.maxY - viewTransform.minY) + 1.0;
  
  const padding = 65;
  const scaleX = (canvas.width - padding * 2) / spanX;
  const scaleY = (canvas.height - padding * 2) / spanY;
  viewTransform.scale = Math.min(scaleX, scaleY);
  
  viewTransform.offsetX = padding + 25 - (viewTransform.minX * viewTransform.scale);
  viewTransform.offsetY = canvas.height / 2;
  
  drawMap();
}

function renderTimelineEvents() {
  eventMarkerLayer.innerHTML = '';
  if (!currentAnalysis || !currentAnalysis.events) return;
  const totalTics = getTotalTics();

  currentAnalysis.events.forEach(evt => {
    const marker = document.createElement('div');
    marker.className = 'event-marker ' + evt.type.toLowerCase().replace('_', '-');
    const pct = (evt.tic / totalTics) * 100;
    marker.style.left = `${pct}%`;
    marker.title = `[Tic ${evt.tic} / ${evt.time_s}s] ${evt.type}: ${evt.description}`;
    marker.addEventListener('click', (e) => {
      e.stopPropagation();
      setTic(evt.tic);
    });
    eventMarkerLayer.appendChild(marker);
  });
}

function updateView(tic) {
  if (!activeDoc || !currentAnalysis) return;

  fixtureBadge.textContent = activeDoc.document_id || 'active_doc';
  readoutTotalTics.textContent = getTotalTics();
  readoutTotalTime.textContent = (getTotalTics() / 35.0).toFixed(2) + 's';

  const marginTics = currentAnalysis.tactical_margin_tics;
  const marginMs = currentAnalysis.tactical_margin_ms;
  const lStar = currentAnalysis.l_star_tics;
  const isFeasible = currentAnalysis.source_schedule_feasible;

  // Status Band Badge & Hero Card
  if (marginTics < 0) {
    statusBandBadge.textContent = 'UNSERVICEABLE';
    statusBandBadge.style.background = 'rgba(248, 81, 73, 0.2)';
    statusBandBadge.style.color = 'var(--red)';
    statusBandBadge.style.borderColor = 'rgba(248, 81, 73, 0.4)';

    valMargin.textContent = `${marginTics} tics`;
    valMargin.className = 'margin-val status-unserviceable';
    valMarginMs.textContent = `${marginMs} ms`;
    valMarginMs.className = 'margin-status status-unserviceable';
    valLStar.textContent = `+${lStar} tics (Late)`;
    valFeasibility.textContent = 'INFEASIBLE';
    valFeasibility.style.color = 'var(--red)';
  } else if (marginTics < 2) {
    statusBandBadge.textContent = 'FEASIBLE — BELOW TARGET RESERVE';
    statusBandBadge.style.background = 'rgba(210, 153, 34, 0.2)';
    statusBandBadge.style.color = 'var(--amber)';
    statusBandBadge.style.borderColor = 'rgba(210, 153, 34, 0.4)';

    valMargin.textContent = `+${marginTics} tics`;
    valMargin.className = 'margin-val status-below-target';
    valMarginMs.textContent = `+${marginMs} ms`;
    valMarginMs.className = 'margin-status status-below-target';
    valLStar.textContent = `${lStar} tics (On Time)`;
    valFeasibility.textContent = 'FEASIBLE';
    valFeasibility.style.color = 'var(--amber)';
  } else {
    statusBandBadge.textContent = 'TARGET RESERVE MET';
    statusBandBadge.style.background = 'rgba(63, 185, 80, 0.2)';
    statusBandBadge.style.color = 'var(--green)';
    statusBandBadge.style.borderColor = 'rgba(63, 185, 80, 0.4)';

    valMargin.textContent = `+${marginTics} tics`;
    valMargin.className = 'margin-val status-serviceable';
    valMarginMs.textContent = `+${marginMs} ms`;
    valMarginMs.className = 'margin-status status-serviceable';
    valLStar.textContent = `${lStar} tics (Optimal)`;
    valFeasibility.textContent = 'RESERVE CERTIFIED';
    valFeasibility.style.color = 'var(--green)';
  }

  // Selected Obstacle & Inspector Card
  const curObs = getObstacles().find(o => o.id === selectedObstacleId);
  const obsName = curObs ? `${curObs.name} (${curObs.id})` : (selectedObstacleId || 'None');
  valSelectedName.textContent = obsName;
  tagSelectedObs.textContent = `SELECTED: ${obsName}`;

  if (curObs) {
    valObsIdName.textContent = `${curObs.name} (${curObs.id})`;
    const b = getSelectedObstacleBounds();
    if (b) {
      valObsCenter.textContent = `${b.cx.toFixed(2)} m, ${b.cy.toFixed(2)} m`;
      valObsDimensions.textContent = `${b.width.toFixed(2)} m × ${b.height.toFixed(2)} m`;
      valObsRotation.textContent = `${previewAngleDeg.toFixed(1)}°`;
    }
  } else {
    valObsIdName.textContent = 'None';
    valObsCenter.textContent = '—';
    valObsDimensions.textContent = '—';
    valObsRotation.textContent = '—';
  }

  valDisp.textContent = `${previewDx >= 0 ? '+' : ''}${previewDx.toFixed(2)}m, ${previewDy >= 0 ? '+' : ''}${previewDy.toFixed(2)}m`;
  valStaggerGap.textContent = `${currentAnalysis.stagger_gap_ms} ms (${currentAnalysis.stagger_gap_tics} tics)`;

  // Threats List
  threatCountBadge.textContent = `${currentAnalysis.threat_jobs.length} THREATS`;
  renderThreatList();

  // Diagnostic
  if (currentAnalysis.diagnostic) {
    whyText.textContent = currentAnalysis.diagnostic.explanation;
  }

  // Telemetry Frame Updates
  const frames = currentAnalysis.telemetry_frames;
  if (frames && frames.length > 0) {
    const frame = frames[Math.min(tic, frames.length - 1)];
    readoutTic.textContent = frame.tic;
    readoutTime.textContent = frame.time_s.toFixed(2) + 's';

    const totalTics = getTotalTics();
    const progressPct = (frame.tic / totalTics) * 100;
    timelineProgress.style.width = `${progressPct}%`;
    timelineHead.style.left = `${progressPct}%`;

    controllerStateBadge.textContent = frame.controller_state;
    if (frame.controller_state === 'DEAD') {
      controllerStateBadge.style.background = 'rgba(248, 81, 73, 0.2)';
      controllerStateBadge.style.color = 'var(--red)';
    } else if (frame.controller_state === 'CLEARED') {
      controllerStateBadge.style.background = 'rgba(63, 185, 80, 0.2)';
      controllerStateBadge.style.color = 'var(--green)';
    } else if (frame.controller_state === 'SERVICING') {
      controllerStateBadge.style.background = 'rgba(210, 153, 34, 0.2)';
      controllerStateBadge.style.color = 'var(--amber)';
    } else {
      controllerStateBadge.style.background = '#172030';
      controllerStateBadge.style.color = 'var(--blue)';
    }

    valActiveTarget.textContent = frame.active_target_id || 'None';
    const curDist = frame.route_dist_m ?? frame.route_distance_traversed_m ?? 0.0;
    const lastFrame = frames && frames.length > 0 ? frames[frames.length - 1] : null;
    const totalDist = lastFrame ? (lastFrame.route_dist_m ?? lastFrame.route_distance_traversed_m ?? 0.0) : 0.0;
    valRouteDist.textContent = `${curDist.toFixed(2)} m / ${totalDist.toFixed(2)} m`;
    const moveSpd = frame.movement_speed_mps ?? (activeDoc?.routes?.[0]?.v_move_mps ?? 4.5);
    valMoveSpeed.textContent = `${moveSpd.toFixed(1)} m/s`;
    const slewSpd = frame.reticle_slew_velocity_deg_s ?? (activeDoc?.player_model?.v_slew_deg_s ?? 360.0);
    valSlewSpeed.textContent = `${slewSpd.toFixed(1)}°/s`;

    tagPlayerPos.textContent = `POS: (${frame.player_pos[0].toFixed(2)}m, ${frame.player_pos[1].toFixed(2)}m)`;
    tagReticle.textContent = `RETICLE: ${frame.reticle_heading_deg.toFixed(1)}°`;
  }

  drawMap();
}

function renderThreatList() {
  threatListContainer.innerHTML = '';
  if (!currentAnalysis || !currentAnalysis.threat_jobs) return;

  currentAnalysis.threat_jobs.forEach(job => {
    const item = document.createElement('div');
    item.className = 'threat-item';

    const header = document.createElement('div');
    header.className = 'threat-header';
    header.innerHTML = `
      <span class="threat-name">${job.label || job.id}</span>
      <span class="threat-badge ${job.lateness_tics <= 0 ? 'good' : 'bad'}">
        ${job.lateness_tics <= 0 ? `Lateness: ${job.lateness_tics} tics` : `Late: +${job.lateness_tics} tics`}
      </span>
    `;

    const details = document.createElement('div');
    details.className = 'threat-details';
    details.innerHTML = `
      <div>Reveal: <strong>Tic ${job.reveal_tic}</strong> (${job.reveal_s}s)</div>
      <div>Deadline: <strong>Tic ${job.deadline_tic}</strong> (${job.deadline_s}s)</div>
      <div>Due Window: <strong>${job.due_window_tics} tics</strong> (${job.due_window_s}s)</div>
      <div>Angle: <strong>${job.angle_deg}&deg;</strong></div>
    `;

    item.appendChild(header);
    item.appendChild(details);
    threatListContainer.appendChild(item);
  });
}

// 2D Map Rendering
function drawMap() {
  if (!activeDoc) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const boundary = getBoundary();
  const frames = currentAnalysis?.telemetry_frames;
  const currentFrame = (frames && frames.length > 0) ? frames[Math.min(currentTic, frames.length - 1)] : null;

  // 1. Grid lines (0.5m grid)
  ctx.strokeStyle = '#121926';
  ctx.lineWidth = 1;
  for (let x = -5; x <= 20; x += 0.5) {
    ctx.beginPath();
    ctx.moveTo(toCanvasX(x), 0);
    ctx.lineTo(toCanvasX(x), canvas.height);
    ctx.stroke();
  }
  for (let y = -10; y <= 10; y += 0.5) {
    ctx.beginPath();
    ctx.moveTo(0, toCanvasY(y));
    ctx.lineTo(canvas.width, toCanvasY(y));
    ctx.stroke();
  }

  // 2. Arena Boundary Polygon
  ctx.fillStyle = '#0c121c';
  ctx.strokeStyle = '#233145';
  ctx.lineWidth = 3;
  ctx.beginPath();
  boundary.forEach(([x, y], idx) => {
    if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
    else ctx.lineTo(toCanvasX(x), toCanvasY(y));
  });
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 2.5 Floor LOS Exposure Density Grid (M2F-B)
  if (showHeatmap && showFloorExposure && cachedHeatmapData?.floor_grid) {
    const grid = cachedHeatmapData.floor_grid;
    const step = grid.grid_step_m;
    const maxExp = Math.max(1, grid.max_exposure);
    const halfStep = step / 2.0;

    grid.cells.forEach(cell => {
      if (!cell.masked && cell.exposure_count > 0) {
        const x1 = toCanvasX(cell.x - halfStep);
        const y1 = toCanvasY(cell.y + halfStep);
        const w = toCanvasX(cell.x + halfStep) - x1;
        const h = toCanvasY(cell.y - halfStep) - y1;

        const intensity = Math.min(0.42, 0.08 + (cell.exposure_count / maxExp) * 0.34);
        ctx.fillStyle = `rgba(99, 102, 241, ${intensity})`;
        ctx.fillRect(x1, y1, w, h);
        ctx.strokeStyle = `rgba(129, 140, 248, ${intensity * 0.4})`;
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x1, y1, w, h);
      }
    });
  }

  // 3. Traversal Routes & Suffix Tactical Margin Heatmap Ribbon (M2F-A)
  if (showHeatmap && cachedHeatmapData?.samples && cachedHeatmapData.samples.length > 1) {
    const samples = cachedHeatmapData.samples;
    // Outer glow aura
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    for (let i = 0; i < samples.length - 1; i++) {
      const s1 = samples[i];
      const s2 = samples[i + 1];
      ctx.strokeStyle = s1.color || '#64748b';
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.moveTo(toCanvasX(s1.position[0]), toCanvasY(s1.position[1]));
      ctx.lineTo(toCanvasX(s2.position[0]), toCanvasY(s2.position[1]));
      ctx.stroke();
    }
    ctx.globalAlpha = 1.0;

    // Solid core ribbon
    ctx.lineWidth = 5;
    for (let i = 0; i < samples.length - 1; i++) {
      const s1 = samples[i];
      const s2 = samples[i + 1];
      ctx.strokeStyle = s1.color || '#64748b';
      ctx.beginPath();
      ctx.moveTo(toCanvasX(s1.position[0]), toCanvasY(s1.position[1]));
      ctx.lineTo(toCanvasX(s2.position[0]), toCanvasY(s2.position[1]));
      ctx.stroke();
    }

    // Sample dots along the path
    samples.forEach((s, idx) => {
      if (idx % 2 === 0) {
        ctx.fillStyle = s.color || '#64748b';
        ctx.beginPath();
        ctx.arc(toCanvasX(s.position[0]), toCanvasY(s.position[1]), 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Highlight hovered sample
    if (hoveredHeatmapSample) {
      const hx = toCanvasX(hoveredHeatmapSample.position[0]);
      const hy = toCanvasY(hoveredHeatmapSample.position[1]);
      ctx.strokeStyle = '#ffffff';
      ctx.fillStyle = hoveredHeatmapSample.color || '#64748b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(hx, hy, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
  } else {
    getRoutes().forEach(r => {
      ctx.strokeStyle = '#23384d';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 6]);
      ctx.beginPath();
      r.waypoints.forEach(([x, y], idx) => {
        if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
        else ctx.lineTo(toCanvasX(x), toCanvasY(y));
      });
      ctx.stroke();
      ctx.setLineDash([]);
    });
  }

  // 4. Active Obstacles
  getObstacles().forEach(obs => {
    const isSelected = (obs.id === selectedObstacleId);
    ctx.fillStyle = isSelected ? '#1e2820' : '#1c2536';
    ctx.strokeStyle = isSelected ? '#39c5bb' : '#4f688a';
    ctx.lineWidth = isSelected ? 3 : 2;

    ctx.beginPath();
    obs.vertices.forEach(([x, y], vIdx) => {
      if (vIdx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
      else ctx.lineTo(toCanvasX(x), toCanvasY(y));
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Selection Label
    const cx = obs.vertices.reduce((sum, v) => sum + v[0], 0) / obs.vertices.length;
    const cy = obs.vertices.reduce((sum, v) => sum + v[1], 0) / obs.vertices.length;
    ctx.fillStyle = isSelected ? '#39c5bb' : '#8b9bb0';
    ctx.font = 'bold 10px monospace';
    ctx.fillText(obs.name || obs.id, toCanvasX(cx) - 20, toCanvasY(cy) + 4);

    // Transform Handles for Selected Obstacle
    if (isSelected && currentTool === 'select') {
      const handles = getHandlesForObstacle(obs);
      if (handles) {
        // Rotation stem line & circle handle
        ctx.strokeStyle = '#39c5bb';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(handles.topMid.x, handles.topMid.y);
        ctx.lineTo(handles.rot.x, handles.rot.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Rotation Handle Knob
        ctx.fillStyle = '#39c5bb';
        ctx.beginPath();
        ctx.arc(handles.rot.x, handles.rot.y, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Corner Resize Handles
        const hSize = 4;
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#39c5bb';
        ctx.lineWidth = 2;
        handles.corners.forEach(h => {
          ctx.fillRect(h.x - hSize, h.y - hSize, hSize * 2, hSize * 2);
          ctx.strokeRect(h.x - hSize, h.y - hSize, hSize * 2, hSize * 2);
        });
      }
    }
  });

  // 4.5 Auto-Fix Ghost Repair Preview (M2E)
  if (activeRepairPreview && activeRepairPreview.repaired_document) {
    const repObs = activeRepairPreview.repaired_document.geometry?.obstacles?.find(o => o.id === activeRepairPreview.controlling_obstacle_id);
    if (repObs && repObs.vertices) {
      ctx.fillStyle = 'rgba(188, 140, 255, 0.25)';
      ctx.strokeStyle = '#bc8cff';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      repObs.vertices.forEach(([x, y], idx) => {
        if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
        else ctx.lineTo(toCanvasX(x), toCanvasY(y));
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.setLineDash([]);

      // Ghost label
      const cx = repObs.vertices.reduce((sum, v) => sum + v[0], 0) / repObs.vertices.length;
      const cy = repObs.vertices.reduce((sum, v) => sum + v[1], 0) / repObs.vertices.length;
      ctx.fillStyle = '#d2a8ff';
      ctx.font = 'bold 10px monospace';
      ctx.fillText('✨ ' + (repObs.name || repObs.id) + ' (Proposed)', toCanvasX(cx) - 30, toCanvasY(cy) - 8);
    }
  }

  // 5. Rectangle Creation Preview Box
  if (interactionMode === 'create_rect' && previewRect) {
    const px1 = toCanvasX(previewRect.x1);
    const py1 = toCanvasY(previewRect.y2); // Canvas top-left
    const pw = (previewRect.x2 - previewRect.x1) * viewTransform.scale;
    const ph = (previewRect.y2 - previewRect.y1) * viewTransform.scale;

    ctx.fillStyle = 'rgba(88, 166, 255, 0.2)';
    ctx.strokeStyle = '#58a6ff';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.fillRect(px1, py1, pw, ph);
    ctx.strokeRect(px1, py1, pw, ph);
    ctx.setLineDash([]);

    // Live dimension label
    const dimW = (previewRect.x2 - previewRect.x1).toFixed(2);
    const dimH = (previewRect.y2 - previewRect.y1).toFixed(2);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`${dimW}m × ${dimH}m`, px1 + pw / 2 - 25, py1 + ph / 2 + 4);
  }

  // 6. Threats
  getThreats().forEach(threat => {
    const isVisible = currentFrame && currentFrame.visible_threat_ids.includes(threat.id);
    const isTarget = currentFrame && currentFrame.active_target_id === threat.id;
    const job = currentAnalysis?.threat_jobs?.find(j => j.id === threat.id);
    const isNeutralized = currentFrame && job && job.realized_service_complete_tic !== null && currentFrame.tic >= job.realized_service_complete_tic;

    if (isNeutralized) {
      ctx.fillStyle = 'rgba(63, 185, 80, 0.1)';
      ctx.strokeStyle = '#238636';
      ctx.lineWidth = 1.5;
    } else if (isVisible) {
      ctx.fillStyle = isTarget ? 'rgba(248, 81, 73, 0.35)' : 'rgba(248, 81, 73, 0.2)';
      ctx.strokeStyle = '#f85149';
      ctx.lineWidth = isTarget ? 3 : 1.5;
    } else {
      ctx.fillStyle = 'rgba(88, 166, 255, 0.05)';
      ctx.strokeStyle = '#2a3a4f';
      ctx.lineWidth = 1;
    }

    ctx.beginPath();
    threat.polygon.forEach(([x, y], idx) => {
      if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
      else ctx.lineTo(toCanvasX(x), toCanvasY(y));
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Anchor
    const ax = toCanvasX(threat.anchor[0]);
    const ay = toCanvasY(threat.anchor[1]);
    ctx.fillStyle = isNeutralized ? '#3fb950' : (isVisible ? '#f85149' : '#3b4b5e');
    ctx.beginPath();
    ctx.arc(ax, ay, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = isNeutralized ? '#3fb950' : '#f0f6fc';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(threat.name || threat.id, ax - 24, ay - 12);
  });

  // 7. Player Telemetry (Only when committed and not actively interacting)
  if (currentFrame && !interactionMode) {
    const px = toCanvasX(currentFrame.player_pos[0]);
    const py = toCanvasY(currentFrame.player_pos[1]);

    // LOS Rays
    currentFrame.los_rays.forEach(ray => {
      const tx = toCanvasX(ray.target_pos[0]);
      const ty = toCanvasY(ray.target_pos[1]);
      const job = currentAnalysis?.threat_jobs?.find(j => j.id === ray.threat_id);
      const isNeutralized = job && job.realized_service_complete_tic !== null && currentFrame.tic >= job.realized_service_complete_tic;

      if (ray.is_visible && !isNeutralized) {
        ctx.strokeStyle = currentFrame.active_target_id === ray.threat_id ? '#3fb950' : 'rgba(88, 166, 255, 0.6)';
        ctx.lineWidth = currentFrame.active_target_id === ray.threat_id ? 2.5 : 1;
        ctx.setLineDash([]);
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
      }

      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(tx, ty);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Player Body and Reticle Pointer
    const isDead = currentFrame.controller_state === 'DEAD';
    const fwdAngleRad = (currentFrame.forward_heading_deg * Math.PI) / 180.0;
    const reticleAngleRad = (currentFrame.reticle_heading_deg * Math.PI) / 180.0;
    const fovRad = (90 * Math.PI) / 180.0;

    if (!isDead) {
      // FOV Cone
      ctx.fillStyle = 'rgba(88, 166, 255, 0.08)';
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.arc(px, py, 140, -reticleAngleRad - fovRad / 2, -reticleAngleRad + fovRad / 2);
      ctx.closePath();
      ctx.fill();

      // Laser Pointer
      const laserLen = 220;
      const lx = px + Math.cos(reticleAngleRad) * laserLen;
      const ly = py - Math.sin(reticleAngleRad) * laserLen;

      ctx.strokeStyle = currentFrame.controller_state === 'SERVICING' ? '#ffd33d' : '#58a6ff';
      ctx.lineWidth = currentFrame.controller_state === 'SERVICING' ? 3 : 2;
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(lx, ly);
      ctx.stroke();
    }

    // Player Circle
    ctx.fillStyle = isDead ? '#f85149' : '#58a6ff';
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(px, py, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    if (isDead) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px - 5, py - 5);
      ctx.lineTo(px + 5, py + 5);
      ctx.moveTo(px + 5, py - 5);
      ctx.lineTo(px - 5, py + 5);
      ctx.stroke();
    } else {
      const hx = px + Math.cos(fwdAngleRad) * 16;
      const hy = py - Math.sin(fwdAngleRad) * 16;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(hx, hy);
      ctx.stroke();
    }
  }
}

// Start application
window.addEventListener('DOMContentLoaded', init);
