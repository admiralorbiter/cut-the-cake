/**
 * Tactical CAD (Cut the Cake) - Milestone 2B General Working Document Engine
 * 
 * Strict boundary:
 * - Operates on arbitrary CADDocument instances (cad_document_v1).
 * - Generic multi-obstacle selection and 2D translation (X and Y).
 * - Fast analysis updates scalar metrics; dims playback with 'PLAYBACK PENDING COMMIT'.
 * - Full telemetry is fetched on pointer release to eliminate mixed-state visualization.
 * - AbortController prevents stale out-of-order responses.
 */

// Application State
let activeDoc = null;
let baselineDoc = null;
let currentAnalysis = null;
let currentTic = 0;
let isPlaying = false;
let playbackSpeed = 1.0;
let animTimer = null;

// Generic Interaction State
let selectedObstacleId = null;
let currentDx = 0.00;
let currentDy = 0.00;
let previewDx = 0.00;
let previewDy = 0.00;
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let dragStartDx = 0.00;
let dragStartDy = 0.00;
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

const statusBandBadge = document.getElementById('statusBandBadge');
const valMargin = document.getElementById('valMargin');
const valMarginMs = document.getElementById('valMarginMs');
const valSelectedName = document.getElementById('valSelectedName');
const valDisp = document.getElementById('valDisp');
const valLStar = document.getElementById('valLStar');
const valFeasibility = document.getElementById('valFeasibility');
const valStaggerGap = document.getElementById('valStaggerGap');
const valEngineStatus = document.getElementById('valEngineStatus');

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
  setupDragging();
  await loadDocumentByName('canonical_f1');
}

function setupUI() {
  docSelect.addEventListener('change', async () => {
    await loadDocumentByName(docSelect.value);
  });

  btnResetDoc.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/document/reset', { method: 'POST' });
      if (resp.ok) {
        currentDx = 0.00;
        currentDy = 0.00;
        previewDx = 0.00;
        previewDy = 0.00;
        invalidCandidateReason = null;
        await requestAnalysis(0.00, 0.00, true);
      }
    } catch (err) {
      console.warn('Server offline, resetting local document');
    }
  });

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
    }
  } catch (err) {
    console.warn('Server offline, loading fallback manifest');
    if (window.SCENE_MANIFEST) {
      activeDoc = {
        schema_version: 'cad_document_v1',
        document_id: window.SCENE_MANIFEST.provenance.fixture_id,
        name: 'Canonical Family 1',
        geometry: window.SCENE_MANIFEST.broken_geometry,
        player_model: window.SCENE_MANIFEST.source_parameters
      };
      baselineDoc = JSON.parse(JSON.stringify(activeDoc));
    }
  }

  if (!activeDoc) return;

  // Default selection
  const obstacles = getObstacles();
  if (obstacles.length > 0) {
    selectedObstacleId = obstacles[0].id;
  }

  currentDx = 0.00;
  currentDy = 0.00;
  previewDx = 0.00;
  previewDy = 0.00;
  invalidCandidateReason = null;

  setupDynamicBounds();
  await requestAnalysis(0.00, 0.00, true);
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

// Interactive Obstacle Selection & 2D Dragging
function setupDragging() {
  function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
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
      const pad = 8;
      if (cx >= minX - pad && cx <= maxX + pad && cy >= minY - pad && cy <= maxY + pad) {
        return obs;
      }
    }
    return null;
  }

  canvas.addEventListener('mousemove', (e) => {
    const pt = getCanvasCoords(e);

    if (isDragging) {
      const dpX = pt.x - dragStartX;
      const dpY = pt.y - dragStartY;
      const dmX = dpX / viewTransform.scale;
      const dmY = -dpY / viewTransform.scale; // Invert Canvas Y to arena coordinates

      const rawDx = dragStartDx + dmX;
      const rawDy = dragStartDy + dmY;
      
      // 0.05m grid snapping
      const snappedDx = Math.round(rawDx / 0.05) * 0.05;
      const snappedDy = Math.round(rawDy / 0.05) * 0.05;

      previewDx = snappedDx;
      previewDy = snappedDy;

      // Show Pending Commit state
      pendingCommitBanner.style.display = 'block';
      footerEl.classList.add('disabled');

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        requestAnalysis(snappedDx, snappedDy, false);
      }, 20);

      drawMap();
    } else {
      const hoveredObs = hitTestObstacles(pt.x, pt.y);
      canvas.style.cursor = hoveredObs ? 'move' : 'default';
    }
  });

  canvas.addEventListener('mousedown', (e) => {
    const pt = getCanvasCoords(e);
    const hitObs = hitTestObstacles(pt.x, pt.y);

    if (hitObs) {
      selectedObstacleId = hitObs.id;
      isDragging = true;
      dragStartX = pt.x;
      dragStartY = pt.y;
      dragStartDx = currentDx;
      dragStartDy = currentDy;
      previewDx = currentDx;
      previewDy = currentDy;
      canvas.style.cursor = 'grabbing';
      drawMap();
    }
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      canvas.style.cursor = 'default';
      pendingCommitBanner.style.display = 'none';
      footerEl.classList.remove('disabled');

      // Commit final position with full telemetry
      requestAnalysis(previewDx, previewDy, true);
    }
  });
}

// Authoritative Python CAD Document Re-analysis
async function requestAnalysis(dx, dy, includeTelemetry = false) {
  clientRevision++;
  latestRequestedRevision = clientRevision;
  const thisRevision = clientRevision;

  if (activeAbortController) {
    activeAbortController.abort();
  }
  activeAbortController = new AbortController();

  latencyBadge.textContent = '⚡ Analyzing...';
  latencyBadge.style.color = 'var(--amber)';

  try {
    const resp = await fetch('/api/document/translate_obstacle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        obstacle_id: selectedObstacleId,
        dx: dx,
        dy: dy,
        client_revision: thisRevision,
        include_telemetry: includeTelemetry
      }),
      signal: activeAbortController.signal
    });

    const data = await resp.json();

    // Strict revision ordering check for both 200 and 422
    if (data.client_revision !== latestRequestedRevision) {
      return; // Discard stale out-of-order response
    }

    latestAppliedRevision = data.client_revision;

    if (!resp.ok || !data.is_valid) {
      invalidCandidateReason = data.error_reason || 'Invalid placement (boundary or clearance collision)';
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
    currentDx = data.dx !== undefined ? data.dx : dx;
    currentDy = data.dy !== undefined ? data.dy : dy;
    currentAnalysis = data;
    if (data.candidate_document) {
      activeDoc = data.candidate_document;
    }

    latencyBadge.textContent = `⚡ Analysis: ${data.runtime_ms} ms`;
    latencyBadge.style.color = '#58a6ff';

    renderTimelineEvents();
    updateView(currentTic);
  } catch (err) {
    if (err.name === 'AbortError') return;
    console.warn('Analysis error:', err);
  }
}

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
  
  const padding = 55;
  const scaleX = (canvas.width - padding * 2) / spanX;
  const scaleY = (canvas.height - padding * 2) / spanY;
  viewTransform.scale = Math.min(scaleX, scaleY);
  
  viewTransform.offsetX = padding + 15 - (viewTransform.minX * viewTransform.scale);
  viewTransform.offsetY = canvas.height / 2;
  
  drawMap();
}

function toCanvasX(x) {
  return viewTransform.offsetX + x * viewTransform.scale;
}

function toCanvasY(y) {
  return viewTransform.offsetY - y * viewTransform.scale;
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

  // Selected Obstacle & Displacement
  const curObs = getObstacles().find(o => o.id === selectedObstacleId);
  const obsName = curObs ? `${curObs.name} (${curObs.id})` : (selectedObstacleId || 'None');
  valSelectedName.textContent = obsName;
  tagSelectedObs.textContent = `SELECTED: ${obsName}`;

  valDisp.textContent = `${currentDx >= 0 ? '+' : ''}${currentDx.toFixed(2)}m, ${currentDy >= 0 ? '+' : ''}${currentDy.toFixed(2)}m`;
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
    valRouteDist.textContent = `${frame.route_dist_m.toFixed(2)} m`;
    tagPlayerPos.textContent = `POS: (${frame.player_pos[0].toFixed(2)}m, ${frame.player_pos[1].toFixed(2)}m)`;
    tagReticle.textContent = `RETICLE: ${frame.reticle_heading_deg.toFixed(1)}° (FWD: ${frame.forward_heading_deg.toFixed(1)}°)`;
  }

  drawMap();
}

function renderThreatList() {
  if (!currentAnalysis) return;
  threatListContainer.innerHTML = '';

  const frames = currentAnalysis.telemetry_frames;
  const currentFrame = frames ? frames[Math.min(currentTic, frames.length - 1)] : null;

  currentAnalysis.threat_jobs.forEach(job => {
    const isVisible = currentFrame && currentFrame.visible_threat_ids.includes(job.id);
    const isTarget = currentFrame && currentFrame.active_target_id === job.id;
    const isCleared = currentFrame && job.realized_service_complete_tic !== null && currentFrame.tic >= job.realized_service_complete_tic;
    const isBreached = currentFrame && currentFrame.tic >= job.deadline_tic && !isCleared;

    let statusTag = 'Occluded';
    let statusColor = 'var(--text-muted)';
    let itemClass = 'threat-item';

    if (isCleared) {
      statusTag = `Neutralized (Tic ${job.realized_service_complete_tic})`;
      statusColor = 'var(--green)';
      itemClass += ' neutralized';
    } else if (isBreached) {
      statusTag = `BREACHED (+${job.lateness_tics} tics)`;
      statusColor = 'var(--red)';
    } else if (isTarget && currentFrame.controller_state === 'SERVICING') {
      statusTag = 'ENGAGING / FIRING';
      statusColor = 'var(--amber)';
    } else if (isTarget) {
      statusTag = 'ACQUIRING / AIMING';
      statusColor = 'var(--blue)';
    } else if (isVisible) {
      statusTag = `Revealed (Due Tic ${job.deadline_tic})`;
      statusColor = 'var(--blue)';
    }

    const item = document.createElement('div');
    item.className = itemClass;
    item.innerHTML = `
      <div>
        <div class="threat-name">
          <div class="threat-pill" style="background: ${statusColor};"></div>
          <span>${job.label}</span>
          <span class="threat-sublabel">${job.id}</span>
        </div>
        <div class="threat-timing">
          r=${job.reveal_tic} | D=${job.deadline_tic} | C=${job.completion_tic}
        </div>
      </div>
      <div class="threat-status-tag" style="color: ${statusColor};">${statusTag}</div>
    `;
    threatListContainer.appendChild(item);
  });
}

// 2D Canvas Map Drawing
function drawMap() {
  if (!activeDoc) return;
  const frames = currentAnalysis ? currentAnalysis.telemetry_frames : null;
  const currentFrame = frames ? frames[Math.min(currentTic, frames.length - 1)] : null;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 1. Grid
  ctx.strokeStyle = '#121926';
  ctx.lineWidth = 1;
  const minX = Math.floor(viewTransform.minX);
  const maxX = Math.ceil(viewTransform.maxX);
  const minY = Math.floor(viewTransform.minY);
  const maxY = Math.ceil(viewTransform.maxY);

  for (let x = minX; x <= maxX; x += 1) {
    ctx.beginPath();
    ctx.moveTo(toCanvasX(x), toCanvasY(minY));
    ctx.lineTo(toCanvasX(x), toCanvasY(maxY));
    ctx.stroke();
  }
  for (let y = minY; y <= maxY; y += 1) {
    ctx.beginPath();
    ctx.moveTo(toCanvasX(minX), toCanvasY(y));
    ctx.lineTo(toCanvasX(maxX), toCanvasY(y));
    ctx.stroke();
  }

  // 2. Arena Boundary
  const boundary = getBoundary();
  ctx.strokeStyle = '#3b506e';
  ctx.lineWidth = 3;
  ctx.fillStyle = '#0a0e17';
  ctx.beginPath();
  boundary.forEach(([x, y], idx) => {
    if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
    else ctx.lineTo(toCanvasX(x), toCanvasY(y));
  });
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 3. Traversal Routes
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

  // 4. Baseline Reference Ghost for Selected Obstacle
  if (baselineDoc && selectedObstacleId) {
    const baseObs = (baselineDoc.geometry?.obstacles || baselineDoc.obstacles || []).find(o => o.id === selectedObstacleId);
    if (baseObs && (Math.abs(currentDx) > 1e-4 || Math.abs(currentDy) > 1e-4)) {
      ctx.strokeStyle = 'rgba(248, 81, 73, 0.3)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      baseObs.vertices.forEach(([x, y], idx) => {
        if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
        else ctx.lineTo(toCanvasX(x), toCanvasY(y));
      });
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // 5. Active Obstacles
  getObstacles().forEach(obs => {
    const isSelected = (obs.id === selectedObstacleId);
    ctx.fillStyle = isSelected ? '#22271d' : '#1c2536';
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

    // Selection Label & Coordinates
    const cx = (obs.vertices[0][0] + obs.vertices[1][0]) / 2;
    const cy = (obs.vertices[0][1] + obs.vertices[2][1]) / 2;
    ctx.fillStyle = isSelected ? '#39c5bb' : '#8b9bb0';
    ctx.font = 'bold 10px monospace';
    ctx.fillText(obs.name || obs.id, toCanvasX(cx) - 20, toCanvasY(cy) + 4);
  });

  // Client-Side Drag Preview Ghost
  if (isDragging) {
    const isInvalid = (invalidCandidateReason !== null);
    const baseObs = (baselineDoc.geometry?.obstacles || baselineDoc.obstacles || []).find(o => o.id === selectedObstacleId);
    if (baseObs) {
      ctx.strokeStyle = isInvalid ? 'rgba(248, 81, 73, 0.9)' : 'rgba(255, 215, 0, 0.9)';
      ctx.lineWidth = 2.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      baseObs.vertices.forEach(([x, y], idx) => {
        const px = toCanvasX(x + previewDx);
        const py = toCanvasY(y + previewDy);
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);

      const cx = (baseObs.vertices[0][0] + baseObs.vertices[1][0]) / 2 + previewDx;
      const cy = (baseObs.vertices[0][1] + baseObs.vertices[2][1]) / 2 + previewDy;
      ctx.fillStyle = isInvalid ? 'rgba(248, 81, 73, 0.95)' : 'rgba(255, 215, 0, 0.95)';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(isInvalid ? 'INVALID' : 'PREVIEW', toCanvasX(cx) - 20, toCanvasY(cy) - 10);
    }
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

  // 7. Player Telemetry (Only when active and committed)
  if (currentFrame && !isDragging) {
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
