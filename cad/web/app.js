/**
 * Tactical CAD (Cut the Cake) - Milestone 2A Interactive Workbench Engine
 * 
 * Strict boundary:
 * - Browser is a dumb renderer and interactive pointer capture client.
 * - Does NOT calculate tactical margins, does NOT raycast, does NOT repair geometry.
 * - Drags send candidate displacements to the local Python CAD service (/api/analyze)
 *   and render authoritative 35 Hz per-tic states.
 */

// State
let manifest = null;
let currentMode = 'working'; // 'working' | 'broken' | 'repaired'
let currentTic = 0;
let isPlaying = false;
let playbackSpeed = 1.0;
let animTimer = null;

// Working Copy State
let workingTranslation = 0.00; // meters from broken baseline
let previewTranslation = 0.00;
let workingAnalysis = null;
let clientRevision = 0;
let latestAppliedRevision = 0;
let isAnalyzing = false;
let isDragging = false;
let dragStartX = 0;
let dragStartTranslation = 0.00;
let debounceTimer = null;

// DOM Elements
const canvas = document.getElementById('mapCanvas');
const ctx = canvas.getContext('2d');
const viewportContainer = document.getElementById('viewportContainer');

const btnModeWorking = document.getElementById('btnModeWorking');
const btnModeBroken = document.getElementById('btnModeBroken');
const btnModeRepaired = document.getElementById('btnModeRepaired');
const btnPlayPause = document.getElementById('btnPlayPause');
const btnStepBack = document.getElementById('btnStepBack');
const btnStepFwd = document.getElementById('btnStepFwd');
const btnReset = document.getElementById('btnReset');
const btnSpeed05 = document.getElementById('btnSpeed05');
const btnSpeed10 = document.getElementById('btnSpeed10');
const btnSpeed20 = document.getElementById('btnSpeed20');
const btnJumpBottleneck = document.getElementById('btnJumpBottleneck');

const timelineScrubber = document.getElementById('timelineScrubber');
const timelineProgress = document.getElementById('timelineProgress');
const timelineHead = document.getElementById('timelineHead');
const eventMarkerLayer = document.getElementById('eventMarkerLayer');

const readoutTic = document.getElementById('readoutTic');
const readoutTotalTics = document.getElementById('readoutTotalTics');
const readoutTime = document.getElementById('readoutTime');
const readoutTotalTime = document.getElementById('readoutTotalTime');

const fixtureBadge = document.getElementById('fixtureBadge');
const playbackTag = document.getElementById('playbackTag');
const evidenceBadge = document.getElementById('evidenceBadge');
const latencyBadge = document.getElementById('latencyBadge');
const statusBandBadge = document.getElementById('statusBandBadge');
const valMargin = document.getElementById('valMargin');
const valMarginMs = document.getElementById('valMarginMs');
const valDisp = document.getElementById('valDisp');
const valLStar = document.getElementById('valLStar');
const valT2Reveal = document.getElementById('valT2Reveal');
const valStaggerGap = document.getElementById('valStaggerGap');
const valEngineStatus = document.getElementById('valEngineStatus');

const tblWorkingShift = document.getElementById('tblWorkingShift');
const tblWorkingT1 = document.getElementById('tblWorkingT1');
const tblWorkingT2 = document.getElementById('tblWorkingT2');
const tblWorkingGap = document.getElementById('tblWorkingGap');
const tblWorkingMargin = document.getElementById('tblWorkingMargin');

const controllerStateBadge = document.getElementById('controllerStateBadge');
const valActiveTarget = document.getElementById('valActiveTarget');
const valRouteDist = document.getElementById('valRouteDist');
const valMoveSpeed = document.getElementById('valMoveSpeed');
const valSlewSpeed = document.getElementById('valSlewSpeed');

const threatListContainer = document.getElementById('threatListContainer');
const whyCard = document.getElementById('whyCard');
const whyText = document.getElementById('whyText');

const tagPlayerPos = document.getElementById('tagPlayerPos');
const tagReticle = document.getElementById('tagReticle');
const tagLOS = document.getElementById('tagLOS');

// Dynamic Coordinate Transformation (Meters -> Canvas Pixels)
let viewTransform = {
  scale: 60,
  offsetX: 80,
  offsetY: 250,
  minX: 0,
  maxX: 10,
  minY: -3,
  maxY: 3
};

// Initialize Application
async function init() {
  try {
    if (window.SCENE_MANIFEST) {
      manifest = window.SCENE_MANIFEST;
    } else {
      const resp = await fetch('../data/m1_scene.json');
      manifest = await resp.json();
    }
    setupDynamicBounds();
    setupUI();
    setupCanvas();
    setupDragging();

    // Initial working copy analysis request
    await requestAnalysis(0.00, true);
    switchMode('working');
  } catch (err) {
    console.error('Failed to load scene manifest:', err);
  }
}

function setupDynamicBounds() {
  const boundary = manifest.broken_geometry.boundary;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  
  boundary.forEach(([x, y]) => {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  });

  manifest.broken_geometry.threats.forEach(t => {
    t.polygon.forEach(([x, y]) => {
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
}

function setupUI() {
  fixtureBadge.textContent = manifest.provenance.fixture_id;
  readoutTotalTics.textContent = manifest.clock.total_tics;
  readoutTotalTime.textContent = manifest.clock.total_duration_s.toFixed(2) + 's';

  const vMove = manifest.source_parameters.v_move_mps;
  const movePerTic = (vMove / manifest.clock.ticrate_hz).toFixed(3);
  valMoveSpeed.textContent = `${vMove.toFixed(1)} m/s (${movePerTic} m/tic)`;

  const wSlew = manifest.source_parameters.omega_slew_deg_per_s;
  const slewPerTic = (wSlew / manifest.clock.ticrate_hz).toFixed(2);
  valSlewSpeed.textContent = `${wSlew.toFixed(0)}°/s (${slewPerTic}°/tic)`;

  // Mode Toggle Events
  btnModeWorking.addEventListener('click', () => switchMode('working'));
  btnModeBroken.addEventListener('click', () => switchMode('broken'));
  btnModeRepaired.addEventListener('click', () => switchMode('repaired'));

  // Playback Controls
  btnPlayPause.addEventListener('click', togglePlay);
  btnStepBack.addEventListener('click', () => stepTic(-1));
  btnStepFwd.addEventListener('click', () => stepTic(1));
  btnReset.addEventListener('click', () => setTic(0));

  // Jump to Bottleneck
  btnJumpBottleneck.addEventListener('click', () => {
    const jobs = getScenario().threat_jobs;
    if (jobs && jobs.length > 1) {
      setTic(jobs[1].reveal_tic);
    }
  });

  // Speed Controls
  btnSpeed05.addEventListener('click', () => setSpeed(0.5, btnSpeed05));
  btnSpeed10.addEventListener('click', () => setSpeed(1.0, btnSpeed10));
  btnSpeed20.addEventListener('click', () => setSpeed(2.0, btnSpeed20));

  // Timeline Scrubbing
  timelineScrubber.addEventListener('click', (e) => {
    const rect = timelineScrubber.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const targetTic = Math.round(ratio * manifest.clock.total_tics);
    setTic(targetTic);
  });

  window.addEventListener('resize', resizeCanvas);
}

function switchMode(mode) {
  currentMode = mode;
  btnModeWorking.className = 'toggle-btn' + (mode === 'working' ? ' active working' : '');
  btnModeBroken.className = 'toggle-btn' + (mode === 'broken' ? ' active broken' : '');
  btnModeRepaired.className = 'toggle-btn' + (mode === 'repaired' ? ' active repaired' : '');

  if (mode === 'broken') {
    evidenceBadge.textContent = 'EXTERNAL: NATIVE VIZDOOM VERIFIED (FATAL)';
    evidenceBadge.className = 'badge';
    evidenceBadge.style.color = 'var(--red)';
    evidenceBadge.style.borderColor = 'rgba(248, 81, 73, 0.4)';
    latencyBadge.style.display = 'none';
    btnJumpBottleneck.textContent = '⚡ Jump to Critical Bottleneck (Tic 3)';
  } else if (mode === 'repaired') {
    evidenceBadge.textContent = 'EXTERNAL: NATIVE VIZDOOM VERIFIED (RESCUED)';
    evidenceBadge.className = 'badge verified';
    evidenceBadge.style.color = '';
    evidenceBadge.style.borderColor = '';
    latencyBadge.style.display = 'none';
    btnJumpBottleneck.textContent = '⚡ Jump to Delayed Reveal (Tic 13)';
  } else {
    evidenceBadge.textContent = 'SOURCE MODEL ONLY — EXTERNAL ENGINE NOT RUN';
    evidenceBadge.className = 'badge';
    evidenceBadge.style.color = 'var(--text-muted)';
    evidenceBadge.style.borderColor = 'var(--border)';
    latencyBadge.style.display = 'inline-block';
    const jobs = getScenario().threat_jobs;
    btnJumpBottleneck.textContent = `⚡ Jump to Reveal (Tic ${jobs && jobs[1] ? jobs[1].reveal_tic : 3})`;
  }

  renderTimelineEvents();
  updateView(currentTic);
}

// Interactive Wall Dragging (Obstacle #0 along X Axis)
function setupDragging() {
  function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  function isPointInObstacle0(cx, cy) {
    const geo = getGeometry();
    if (!geo.obstacles || !geo.obstacles[0]) return false;
    const verts = geo.obstacles[0].vertices;
    
    // Bounding box hit test with generous padding
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    verts.forEach(([x, y]) => {
      const px = toCanvasX(x);
      const py = toCanvasY(y);
      minX = Math.min(minX, px);
      maxX = Math.max(maxX, px);
      minY = Math.min(minY, py);
      maxY = Math.max(maxY, py);
    });

    const pad = 12;
    return cx >= minX - pad && cx <= maxX + pad && cy >= minY - pad && cy <= maxY + pad;
  }

  canvas.addEventListener('mousemove', (e) => {
    const pt = getCanvasCoords(e);

    if (isDragging) {
      const dp = pt.x - dragStartX;
      const dm = dp / viewTransform.scale;
      const rawDx = dragStartTranslation + dm;
      
      // 0.05m grid snapping clamped to [0.00, 1.40]m
      const snappedDx = Math.max(0.00, Math.min(1.40, Math.round(rawDx / 0.05) * 0.05));
      previewTranslation = snappedDx;
      
      // Trigger debounced analysis
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        requestAnalysis(snappedDx, false);
      }, 20);

      drawMap();
    } else {
      if (isPointInObstacle0(pt.x, pt.y)) {
        canvas.style.cursor = 'ew-resize';
      } else {
        canvas.style.cursor = 'default';
      }
    }
  });

  canvas.addEventListener('mousedown', (e) => {
    const pt = getCanvasCoords(e);
    if (isPointInObstacle0(pt.x, pt.y)) {
      isDragging = true;
      if (currentMode !== 'working') {
        switchMode('working');
      }
      dragStartX = pt.x;
      dragStartTranslation = workingTranslation;
      previewTranslation = workingTranslation;
      canvas.style.cursor = 'ew-resize';
    }
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      canvas.style.cursor = 'default';
      // Commit final position with full telemetry frames
      requestAnalysis(previewTranslation, true);
    }
  });
}

// Authoritative Python CAD Analysis Request
async function requestAnalysis(translationM, includeTelemetry = false) {
  clientRevision++;
  const thisRevision = clientRevision;
  latencyBadge.textContent = '⚡ Analyzing...';
  latencyBadge.style.color = 'var(--amber)';

  try {
    const resp = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fixture_id: manifest.provenance.fixture_id,
        obstacle_id: 0,
        translation_m: translationM,
        axis: 'x',
        client_revision: thisRevision,
        include_telemetry: includeTelemetry
      })
    });

    if (!resp.ok) {
      console.warn('Analysis rejected by Python server');
      return;
    }

    const data = await resp.json();
    if (data.client_revision < latestAppliedRevision) {
      return; // Stale out-of-order response discarded
    }

    latestAppliedRevision = data.client_revision;
    workingTranslation = data.translation_m;
    workingAnalysis = data;
    
    latencyBadge.textContent = `⚡ Analysis: ${data.runtime_ms} ms`;
    latencyBadge.style.color = '#58a6ff';

    renderTimelineEvents();
    updateView(currentTic);
  } catch (err) {
    // Local static file:// fallback approximation
    console.warn('CAD server offline, using local representation:', err);
    latencyBadge.textContent = '⚡ Standalone Mode';
  }
}

function getGeometry() {
  if (currentMode === 'broken') return manifest.broken_geometry;
  if (currentMode === 'repaired') return manifest.repaired_geometry;
  if (workingAnalysis && workingAnalysis.candidate_geometry) {
    return workingAnalysis.candidate_geometry;
  }
  return manifest.broken_geometry;
}

function getScenario() {
  if (currentMode === 'broken') return manifest.broken_scenario;
  if (currentMode === 'repaired') return manifest.repaired_scenario;
  if (workingAnalysis) {
    return {
      tactical_margin_tics: workingAnalysis.tactical_margin_tics,
      tactical_margin_ms: workingAnalysis.tactical_margin_ms,
      l_star_tics: workingAnalysis.l_star_tics,
      verdict: workingAnalysis.verdict,
      threat_jobs: workingAnalysis.threat_jobs,
      diagnostic: workingAnalysis.diagnostic,
      telemetry_frames: workingAnalysis.telemetry_frames || manifest.broken_scenario.telemetry_frames,
      events: workingAnalysis.events || manifest.broken_scenario.events,
      model_episode_survived: workingAnalysis.model_episode_survived,
      model_death_tic: workingAnalysis.model_death_tic
    };
  }
  return manifest.broken_scenario;
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
  if (isPlaying) {
    pause();
  } else {
    play();
  }
}

function play() {
  const scenario = getScenario();
  if (currentTic >= scenario.telemetry_frames.length - 1) {
    currentTic = 0;
  }
  isPlaying = true;
  btnPlayPause.textContent = '⏸ Pause';
  btnPlayPause.classList.remove('primary');
  btnPlayPause.style.background = 'var(--amber)';

  const intervalMs = (1000.0 / manifest.clock.ticrate_hz) / playbackSpeed;
  animTimer = setInterval(() => {
    if (currentTic < scenario.telemetry_frames.length - 1) {
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
  const scenario = getScenario();
  const maxTic = scenario.telemetry_frames.length - 1;
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

// Convert arena coordinates (m) to canvas pixels
function toCanvasX(x) {
  return viewTransform.offsetX + x * viewTransform.scale;
}

function toCanvasY(y) {
  return viewTransform.offsetY - y * viewTransform.scale;
}

// Render Timeline Events
function renderTimelineEvents() {
  eventMarkerLayer.innerHTML = '';
  const scenario = getScenario();
  const totalTics = manifest.clock.total_tics;

  if (!scenario.events) return;
  scenario.events.forEach(evt => {
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

// Main View Update
function updateView(tic) {
  const scenario = getScenario();
  const frames = scenario.telemetry_frames;
  const frame = frames[Math.min(tic, frames.length - 1)];

  // Update Timeline Scrubber
  const totalTics = manifest.clock.total_tics;
  const progressPct = (frame.tic / totalTics) * 100;
  timelineProgress.style.width = `${progressPct}%`;
  timelineHead.style.left = `${progressPct}%`;

  // Update Header Readouts
  readoutTic.textContent = frame.tic;
  readoutTime.textContent = frame.time_s.toFixed(2) + 's';

  // Update Schedulability Banner & Status Band
  const marginTics = scenario.tactical_margin_tics;
  const marginMs = scenario.tactical_margin_ms;
  const lStar = scenario.l_star_tics;

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
  }

  // Displacement & Reveals
  const currentDisp = currentMode === 'working' ? workingTranslation : (currentMode === 'repaired' ? 1.10 : 0.00);
  valDisp.textContent = `+${currentDisp.toFixed(2)} m (0.05m snap)`;

  const jobs = scenario.threat_jobs || [];
  const t1 = jobs[0];
  const t2 = jobs[1];
  if (t2) {
    valT2Reveal.textContent = `Tic ${t2.reveal_tic} (${t2.reveal_s.toFixed(2)}s)`;
    const gapMs = Math.round((t2.reveal_tic - (t1 ? t1.reveal_tic : 0)) * manifest.clock.dt_s * 1000);
    valStaggerGap.textContent = `${gapMs} ms`;
  }

  // Comparison Table
  tblWorkingShift.textContent = `+${currentDisp.toFixed(2)} m`;
  if (t1) tblWorkingT1.textContent = `Tic ${t1.reveal_tic} (${t1.reveal_s.toFixed(2)}s)`;
  if (t2) {
    tblWorkingT2.textContent = `Tic ${t2.reveal_tic} (${t2.reveal_s.toFixed(2)}s)`;
    const gapMs = Math.round((t2.reveal_tic - (t1 ? t1.reveal_tic : 0)) * manifest.clock.dt_s * 1000);
    tblWorkingGap.textContent = `${gapMs} ms`;
  }
  tblWorkingMargin.textContent = `${marginTics >= 0 ? '+' : ''}${marginTics} tics`;
  tblWorkingMargin.style.color = marginTics >= 2 ? 'var(--green)' : (marginTics >= 0 ? 'var(--amber)' : 'var(--red)');

  // External Evidence Readout
  if (currentMode === 'working') {
    valEngineStatus.textContent = 'SOURCE MODEL ONLY — EXTERNAL ENGINE NOT RUN';
    valEngineStatus.style.color = 'var(--text-muted)';
  } else if (currentMode === 'broken') {
    valEngineStatus.textContent = 'Fatal Death (0 HP)';
    valEngineStatus.style.color = 'var(--red)';
  } else {
    valEngineStatus.textContent = 'Rescued / Survived (100 HP)';
    valEngineStatus.style.color = 'var(--green)';
  }

  // Controller State
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

  const actJob = jobs.find(j => j.id === frame.active_target_id);
  valActiveTarget.textContent = actJob ? `${actJob.label} (${actJob.id})` : 'None';
  valRouteDist.textContent = `${frame.route_dist_m.toFixed(2)} m / ${getGeometry().route.total_length_m.toFixed(2)} m`;

  // Overlay Tags
  tagPlayerPos.textContent = `POS: (${frame.player_pos[0].toFixed(2)}m, ${frame.player_pos[1].toFixed(2)}m)`;
  tagReticle.textContent = `RETICLE: ${frame.reticle_heading_deg.toFixed(1)}° (FWD: ${frame.forward_heading_deg.toFixed(1)}°)`;
  tagLOS.textContent = `VISIBLE: ${frame.visible_threat_ids.length} [${frame.visible_threat_ids.join(', ')}]`;

  // Threats List
  renderThreatList(frame);

  // Diagnostic Cards
  if (scenario.diagnostic) {
    whyText.textContent = scenario.diagnostic.explanation;
  }

  // Render Map Canvas
  drawMap(frame);
}

function renderThreatList(currentFrame) {
  const scenario = getScenario();
  threatListContainer.innerHTML = '';

  (scenario.threat_jobs || []).forEach(job => {
    const isVisible = currentFrame.visible_threat_ids.includes(job.id);
    const isTarget = currentFrame.active_target_id === job.id;
    const isCleared = currentFrame.tic >= (job.realized_service_complete_tic !== null ? job.realized_service_complete_tic : 9999);
    const isBreached = currentFrame.tic >= job.deadline_tic && !isCleared;

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
          r=${job.reveal_tic} | D=${job.deadline_tic} | Angle: ${job.angle_deg}°
        </div>
      </div>
      <div class="threat-status-tag" style="color: ${statusColor};">${statusTag}</div>
    `;
    threatListContainer.appendChild(item);
  });
}

// 2D Canvas Map Drawing
function drawMap(frame) {
  if (!manifest) return;
  const currentFrame = frame || getScenario().telemetry_frames[Math.min(currentTic, getScenario().telemetry_frames.length - 1)];
  const currentGeo = getGeometry();

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 1. Draw Grid in Meters
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

  // 2. Room Boundary
  ctx.strokeStyle = '#3b506e';
  ctx.lineWidth = 3;
  ctx.fillStyle = '#0a0e17';
  ctx.beginPath();
  currentGeo.boundary.forEach(([x, y], idx) => {
    if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
    else ctx.lineTo(toCanvasX(x), toCanvasY(y));
  });
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // 3. Polyline Route
  ctx.strokeStyle = '#23384d';
  ctx.lineWidth = 3;
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  currentGeo.route.waypoints.forEach(([x, y], idx) => {
    if (idx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
    else ctx.lineTo(toCanvasX(x), toCanvasY(y));
  });
  ctx.stroke();
  ctx.setLineDash([]);

  // 4. Reference Ghost Obstacle Outline in Working & Repaired Modes
  if (currentMode === 'working' || currentMode === 'repaired') {
    const baseObs = manifest.broken_geometry.obstacles[0];
    if (baseObs) {
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

    // Translation Vector Arrow
    const activeObs = currentGeo.obstacles[0];
    if (baseObs && activeObs) {
      const oldX = (baseObs.vertices[0][0] + baseObs.vertices[1][0]) / 2;
      const oldY = (baseObs.vertices[0][1] + baseObs.vertices[2][1]) / 2;
      const newX = (activeObs.vertices[0][0] + activeObs.vertices[1][0]) / 2;
      const newY = (activeObs.vertices[0][1] + activeObs.vertices[2][1]) / 2;

      const p1x = toCanvasX(oldX);
      const p1y = toCanvasY(oldY);
      const p2x = toCanvasX(newX);
      const p2y = toCanvasY(newY);

      if (Math.abs(p2x - p1x) > 3) {
        ctx.strokeStyle = '#d29922';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(p1x, p1y);
        ctx.lineTo(p2x, p2y);
        ctx.stroke();

        const angle = Math.atan2(p2y - p1y, p2x - p1x);
        const headLen = 8;
        ctx.fillStyle = '#d29922';
        ctx.beginPath();
        ctx.moveTo(p2x, p2y);
        ctx.lineTo(p2x - headLen * Math.cos(angle - Math.PI / 6), p2y - headLen * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(p2x - headLen * Math.cos(angle + Math.PI / 6), p2y - headLen * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#d29922';
        ctx.font = 'bold 10px monospace';
        const dispVal = currentMode === 'working' ? workingTranslation : 1.10;
        ctx.fillText(`+${dispVal.toFixed(2)}m (Shift)`, (p1x + p2x) / 2 - 30, p1y - 12);
      }
    }
  }

  // 5. Active Obstacles
  currentGeo.obstacles.forEach((obs, idx) => {
    const isDraggable = (idx === 0);
    ctx.fillStyle = isDraggable ? (currentMode === 'working' ? '#252119' : '#1c2536') : '#1c2536';
    ctx.strokeStyle = isDraggable ? (currentMode === 'working' ? '#d29922' : '#4f688a') : '#4f688a';
    ctx.lineWidth = isDraggable ? 2.5 : 2;

    ctx.beginPath();
    obs.vertices.forEach(([x, y], vIdx) => {
      if (vIdx === 0) ctx.moveTo(toCanvasX(x), toCanvasY(y));
      else ctx.lineTo(toCanvasX(x), toCanvasY(y));
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draggable Handle Visual Cue
    if (isDraggable && currentMode === 'working') {
      const cx = (obs.vertices[0][0] + obs.vertices[1][0]) / 2;
      const cy = (obs.vertices[0][1] + obs.vertices[2][1]) / 2;
      ctx.fillStyle = '#d29922';
      ctx.font = 'bold 10px monospace';
      ctx.fillText('↔ DRAG', toCanvasX(cx) - 18, toCanvasY(cy) + 4);
    }
  });

  // Client-Side Drag Preview Ghost
  if (isDragging && Math.abs(previewTranslation - workingTranslation) > 1e-4) {
    const baseObs = manifest.broken_geometry.obstacles[0];
    if (baseObs) {
      ctx.strokeStyle = 'rgba(255, 215, 0, 0.8)';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      baseObs.vertices.forEach(([x, y], idx) => {
        const px = toCanvasX(x + previewTranslation);
        const py = toCanvasY(y);
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);

      const cx = (baseObs.vertices[0][0] + baseObs.vertices[1][0]) / 2 + previewTranslation;
      const cy = (baseObs.vertices[0][1] + baseObs.vertices[2][1]) / 2;
      ctx.fillStyle = 'rgba(255, 215, 0, 0.9)';
      ctx.font = 'bold 9px monospace';
      ctx.fillText('PREVIEW', toCanvasX(cx) - 20, toCanvasY(cy) - 10);
    }
  }

  // 6. Threats
  const scenario = getScenario();
  currentGeo.threats.forEach(threat => {
    const isVisible = currentFrame.visible_threat_ids.includes(threat.id);
    const isTarget = currentFrame.active_target_id === threat.id;
    const job = (scenario.threat_jobs || []).find(j => j.id === threat.id);
    const isNeutralized = job && currentFrame.tic >= (job.realized_service_complete_tic !== null ? job.realized_service_complete_tic : 9999);

    // Draw threat bounding box
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

    // Threat Anchor
    const ax = toCanvasX(threat.anchor[0]);
    const ay = toCanvasY(threat.anchor[1]);
    ctx.fillStyle = isNeutralized ? '#3fb950' : (isVisible ? '#f85149' : '#3b4b5e');
    ctx.beginPath();
    ctx.arc(ax, ay, 6, 0, Math.PI * 2);
    ctx.fill();

    // Label
    ctx.fillStyle = isNeutralized ? '#3fb950' : '#f0f6fc';
    ctx.font = 'bold 11px monospace';
    const displayTag = isNeutralized ? `✓ ${threat.label}` : threat.label;
    ctx.fillText(displayTag, ax - 24, ay - 12);
  });

  // 7. LOS Rays from Player
  const px = toCanvasX(currentFrame.player_pos[0]);
  const py = toCanvasY(currentFrame.player_pos[1]);

  currentFrame.los_rays.forEach(ray => {
    const tx = toCanvasX(ray.target_pos[0]);
    const ty = toCanvasY(ray.target_pos[1]);
    const job = (scenario.threat_jobs || []).find(j => j.id === ray.threat_id);
    const isNeutralized = job && currentFrame.tic >= (job.realized_service_complete_tic !== null ? job.realized_service_complete_tic : 9999);

    if (ray.is_visible && !isNeutralized) {
      ctx.strokeStyle = currentFrame.active_target_id === ray.threat_id ? '#3fb950' : 'rgba(88, 166, 255, 0.6)';
      ctx.lineWidth = currentFrame.active_target_id === ray.threat_id ? 2.5 : 1;
      ctx.setLineDash([]);
    } else {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
    }

    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(tx, ty);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // 8. Player Body and Aim Laser
  const isDead = currentFrame.controller_state === 'DEAD';
  const fwdAngleRad = (currentFrame.forward_heading_deg * Math.PI) / 180.0;
  const reticleAngleRad = (currentFrame.reticle_heading_deg * Math.PI) / 180.0;
  const fovRad = (90 * Math.PI) / 180.0;

  if (!isDead) {
    // View Cone
    ctx.fillStyle = 'rgba(88, 166, 255, 0.08)';
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.arc(px, py, 140, -reticleAngleRad - fovRad / 2, -reticleAngleRad + fovRad / 2);
    ctx.closePath();
    ctx.fill();

    // Reticle Laser Pointer
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

// Start application
window.addEventListener('DOMContentLoaded', init);
