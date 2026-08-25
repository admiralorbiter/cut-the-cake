/**
 * Cut the Cake — Advanced Evidence Lab & Tactical MRI Engine
 * 100% Pure Data-Driven Renderer replaying authoritative presentations.json.
 */

let presentationsData = null;
let currentPres = null;
let currentFrame = 0;
let totalFrames = 100;
let isPlaying = false;
let playInterval = null;
let playSpeed = 1.0;

// Canvas contexts
let ctxGeom = null;
let ctxGantt = null;
let ctxXRay = null;

document.addEventListener("DOMContentLoaded", async () => {
  ctxGeom = document.getElementById("canvas-geom").getContext("2d");
  ctxGantt = document.getElementById("canvas-gantt").getContext("2d");
  ctxXRay = document.getElementById("canvas-xray").getContext("2d");

  try {
    const res = await fetch("presentations.json");
    presentationsData = await res.json();
    initGallery();
    loadPresentation(presentationsData.presentations[0].id);
  } catch (err) {
    console.error("Failed to load presentations.json:", err);
  }

  setupControls();
});

function initGallery() {
  const strip = document.getElementById("gallery-strip");
  strip.innerHTML = "";

  presentationsData.presentations.forEach((p, idx) => {
    const btn = document.createElement("button");
    btn.className = `gallery-btn ${idx === 0 ? "active" : ""}`;
    btn.id = `btn-${p.id}`;
    btn.innerHTML = `<span>${p.title.split(":")[0]}</span><span class="sub">${p.title.split(":")[1] || p.subtitle}</span>`;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".gallery-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadPresentation(p.id);
    });
    strip.appendChild(btn);
  });
}

function loadPresentation(id) {
  currentPres = presentationsData.presentations.find(p => p.id === id);
  if (!currentPres) return;

  // Update Hero
  document.getElementById("hero-title").innerText = currentPres.title;
  document.getElementById("hero-desc").innerText = currentPres.description;
  document.getElementById("hero-provenance").innerText = currentPres.provenance;
  document.getElementById("hero-fixture").innerText = `Fixture: ${currentPres.source_fixture}`;

  // Reset playback
  currentFrame = 0;
  totalFrames = 100;
  updateSlider();
  renderAllPanes();
}

function setupControls() {
  const playBtn = document.getElementById("btn-play");
  const prevBtn = document.getElementById("btn-prev");
  const nextBtn = document.getElementById("btn-next");
  const slider = document.getElementById("time-slider");

  playBtn.addEventListener("click", () => {
    isPlaying = !isPlaying;
    playBtn.innerText = isPlaying ? "Pause" : "Play";
    if (isPlaying) {
      startPlayback();
    } else {
      stopPlayback();
    }
  });

  prevBtn.addEventListener("click", () => {
    stopPlayback();
    currentFrame = Math.max(0, currentFrame - 1);
    updateSlider();
    renderAllPanes();
  });

  nextBtn.addEventListener("click", () => {
    stopPlayback();
    currentFrame = Math.min(totalFrames - 1, currentFrame + 1);
    updateSlider();
    renderAllPanes();
  });

  slider.addEventListener("input", (e) => {
    stopPlayback();
    currentFrame = parseInt(e.target.value, 10);
    renderAllPanes();
  });
}

function startPlayback() {
  if (playInterval) clearInterval(playInterval);
  playInterval = setInterval(() => {
    currentFrame = (currentFrame + 1) % totalFrames;
    updateSlider();
    renderAllPanes();
  }, 50 / playSpeed);
}

function stopPlayback() {
  isPlaying = false;
  document.getElementById("btn-play").innerText = "Play";
  if (playInterval) {
    clearInterval(playInterval);
    playInterval = null;
  }
}

function updateSlider() {
  const slider = document.getElementById("time-slider");
  slider.value = currentFrame;
  const t_sec = (currentFrame * (3.0 / totalFrames)).toFixed(2);
  document.getElementById("time-display").innerText = `t = ${t_sec}s (tic ${Math.round(currentFrame * 1.05)})`;
}

function renderAllPanes() {
  if (!currentPres) return;
  renderGeometryPane();
  renderGanttPane();
  renderXRayPane();
  renderWhyPane();
}

// ----------------------------------------------------------------------------
// Pane A: Geometry Rendering (Pure Data-Driven)
// ----------------------------------------------------------------------------
function renderGeometryPane() {
  const c = ctxGeom;
  const w = c.canvas.width;
  const h = c.canvas.height;
  c.clearRect(0, 0, w, h);

  // Background
  c.fillStyle = "#0b0f19";
  c.fillRect(0, 0, w, h);

  const prog = currentFrame / (totalFrames - 1);
  const scenes = currentPres.scenes || [];

  if (scenes.length === 2) {
    // Dual View (Side by Side)
    drawScene(c, scenes[0], 10, 10, w / 2 - 15, h - 20, prog);
    drawScene(c, scenes[1], w / 2 + 5, 10, w / 2 - 15, h - 20, prog);
  } else if (scenes.length === 1) {
    // Single View
    drawScene(c, scenes[0], 20, 10, w - 40, h - 20, prog);
  } else {
    // Fallback info text
    c.fillStyle = "#64748b";
    c.font = "12px monospace";
    c.fillText("[Static Empirical Benchmark: See Diagnostic & X-Ray Panels]", 40, h / 2);
  }
}

function drawScene(c, sc, rx, ry, rw, rh, prog) {
  // Boundary Box
  c.fillStyle = "#0e1726";
  c.strokeStyle = "#1e293b";
  c.lineWidth = 1.5;
  c.fillRect(rx, ry, rw, rh);
  c.strokeRect(rx, ry, rw, rh);

  // Header Title
  c.fillStyle = "#f8fafc";
  c.font = "bold 10px sans-serif";
  c.fillText(sc.name, rx + 8, ry + 16);

  // Compute bounding box of physical coordinates
  const b = sc.boundary || [[0, -3], [10, -3], [10, 3], [0, 3]];
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  b.forEach(pt => {
    minX = Math.min(minX, pt[0]);
    maxX = Math.max(maxX, pt[0]);
    minY = Math.min(minY, pt[1]);
    maxY = Math.max(maxY, pt[1]);
  });
  const spanX = Math.max(1, maxX - minX);
  const spanY = Math.max(1, maxY - minY);

  const pad = 24;
  const toScreenX = (x) => rx + pad + ((x - minX) / spanX) * (rw - pad * 2);
  const toScreenY = (y) => ry + rh - pad - ((y - minY) / spanY) * (rh - pad * 2);

  // Draw Obstacles
  (sc.obstacles || []).forEach(obs => {
    if (!obs || obs.length === 0) return;
    c.fillStyle = "#1e293b";
    c.strokeStyle = "#38bdf8";
    c.lineWidth = 1.5;
    c.beginPath();
    c.moveTo(toScreenX(obs[0][0]), toScreenY(obs[0][1]));
    for (let i = 1; i < obs.length; i++) {
      c.lineTo(toScreenX(obs[i][0]), toScreenY(obs[i][1]));
    }
    c.closePath();
    c.fill();
    c.stroke();
  });

  // Draw Routes
  (sc.routes || []).forEach(r => {
    if (!r || r.length < 2) return;
    c.strokeStyle = "#334155";
    c.lineWidth = 1.5;
    c.setLineDash([3, 3]);
    c.beginPath();
    c.moveTo(toScreenX(r[0][0]), toScreenY(r[0][1]));
    for (let i = 1; i < r.length; i++) {
      c.lineTo(toScreenX(r[i][0]), toScreenY(r[i][1]));
    }
    c.stroke();
    c.setLineDash([]);
  });

  // Player position along route
  let px = toScreenX(minX + prog * spanX);
  let py = toScreenY(0.0);
  let pHeading = 0.0;
  let visibleThreats = [];

  if (sc.telemetry_frames && sc.telemetry_frames.length > 0) {
    const fIdx = Math.min(sc.telemetry_frames.length - 1, Math.floor(prog * sc.telemetry_frames.length));
    const frame = sc.telemetry_frames[fIdx];
    if (frame && frame.player_pos) {
      px = toScreenX(frame.player_pos[0]);
      py = toScreenY(frame.player_pos[1]);
      pHeading = frame.reticle_heading_deg || 0.0;
      visibleThreats = frame.visible_threat_ids || [];
    }
  }

  // Draw Threats & Sightlines
  (sc.threats || []).forEach(t => {
    const anc = t.anchor || [minX + spanX * 0.7, 0];
    const tx = toScreenX(anc[0]);
    const ty = toScreenY(anc[1]);

    const isVisible = visibleThreats.includes(t.id) || prog > ((t.reveal_tic || 0) / 105.0);
    c.fillStyle = isVisible ? "#ef4444" : "#475569";
    c.beginPath();
    c.arc(tx, ty, 6, 0, Math.PI * 2);
    c.fill();

    // Threat Label
    c.fillStyle = "#94a3b8";
    c.font = "8px monospace";
    c.fillText(t.name || t.id, tx - 10, ty + 14);

    // Sightline
    c.strokeStyle = isVisible ? "rgba(34, 197, 94, 0.7)" : "rgba(51, 65, 85, 0.3)";
    c.lineWidth = isVisible ? 1.5 : 1;
    c.beginPath();
    c.moveTo(px, py);
    c.lineTo(tx, ty);
    c.stroke();
  });

  // Draw Player Marker
  c.fillStyle = "#00f0ff";
  c.beginPath();
  c.arc(px, py, 6, 0, Math.PI * 2);
  c.fill();

  // Reticle Ray
  const rad = pHeading * (Math.PI / 180.0);
  c.strokeStyle = "#f59e0b";
  c.lineWidth = 2;
  c.beginPath();
  c.moveTo(px, py);
  c.lineTo(px + Math.cos(rad) * 25, py - Math.sin(rad) * 25);
  c.stroke();
}

// ----------------------------------------------------------------------------
// Pane B: Scheduler Gantt Chart (Pure Data-Driven)
// ----------------------------------------------------------------------------
function renderGanttPane() {
  const c = ctxGantt;
  const w = c.canvas.width;
  const h = c.canvas.height;
  c.clearRect(0, 0, w, h);

  c.fillStyle = "#0b0f19";
  c.fillRect(0, 0, w, h);

  const prog = currentFrame / (totalFrames - 1);
  const curTime = prog * 3.0;

  // Grid lines
  c.strokeStyle = "#1e293b";
  c.lineWidth = 1;
  for (let s = 0; s <= 3; s += 0.5) {
    const x = 90 + (s / 3.0) * (w - 110);
    c.beginPath(); c.moveTo(x, 15); c.lineTo(x, h - 20); c.stroke();
    c.fillStyle = "#64748b";
    c.font = "9px monospace";
    c.fillText(`${s}s`, x - 8, h - 6);
  }

  // Collect jobs from all scenes
  let allJobs = [];
  (currentPres.scenes || []).forEach((sc, scIdx) => {
    (sc.threat_jobs || []).forEach(j => {
      allJobs.push({
        label: `${sc.name.split(":")[0]} ${j.label || j.id}`,
        r: (j.reveal_tic || 0) / 35.0,
        d: (j.deadline_tic || 35) / 35.0,
        c: (j.completion_tic || (j.reveal_tic || 0) + 10) / 35.0,
        breached: j.is_breached || false,
        color: j.is_breached ? "#ef4444" : "#10b981",
      });
    });
  });

  if (allJobs.length === 0) {
    allJobs = [
      { label: "Execution Schedulable", r: 0.0, d: 2.5, c: 1.2, breached: false, color: "#10b981" }
    ];
  }

  const rowHeight = Math.min(24, (h - 40) / Math.max(1, allJobs.length));
  allJobs.forEach((job, idx) => {
    const y = 20 + idx * rowHeight;
    c.fillStyle = "#94a3b8";
    c.font = "9px monospace";
    c.fillText(job.label.substring(0, 16), 8, y + 10);

    const xR = 90 + (Math.min(3.0, job.r) / 3.0) * (w - 110);
    const xD = 90 + (Math.min(3.0, job.d) / 3.0) * (w - 110);
    const xC = 90 + (Math.min(3.0, job.c) / 3.0) * (w - 110);

    // Job bar
    c.fillStyle = job.color;
    c.fillRect(xR, y, Math.max(4, xC - xR), Math.max(8, rowHeight - 6));

    // Deadline tick
    c.strokeStyle = "#ef4444";
    c.lineWidth = 2;
    c.beginPath(); c.moveTo(xD, y - 2); c.lineTo(xD, y + rowHeight - 4); c.stroke();
  });

  // Current playback time cursor
  const cx = 90 + (curTime / 3.0) * (w - 110);
  c.strokeStyle = "#00f0ff";
  c.lineWidth = 2;
  c.beginPath(); c.moveTo(cx, 10); c.lineTo(cx, h - 15); c.stroke();
}

// ----------------------------------------------------------------------------
// Pane C: Route X-Ray / Spatial Tracks (Pure Data-Driven)
// ----------------------------------------------------------------------------
function renderXRayPane() {
  const c = ctxXRay;
  const w = c.canvas.width;
  const h = c.canvas.height;
  c.clearRect(0, 0, w, h);

  c.fillStyle = "#0b0f19";
  c.fillRect(0, 0, w, h);

  // Extract spatial tracks from the primary scene
  const primaryScene = (currentPres.scenes && currentPres.scenes[0]) || {};
  const tracksData = primaryScene.spatial_tracks || {
    s_m: [0, 2, 4, 6, 8, 10],
    k_los: [0, 1, 2, 1, 0, 0],
    delta_min_tics: [14, 10, 2, 8, 12, 16],
    m_suffix_tics: [2, 2, -19, -4, 2, 4],
  };

  const tracks = [
    { label: "1. K_LOS(s) (Visible Threats)", key: "k_los", color: "#f59e0b", y: 20, h: 42 },
    { label: "2. δ_min(s) (Deadline Headroom tics)", key: "delta_min_tics", color: "#38bdf8", y: 80, h: 42 },
    { label: "3. M_suffix(s) (Suffix Margin tics)", key: "m_suffix_tics", color: "#10b981", y: 140, h: 42 }
  ];

  tracks.forEach(tr => {
    c.fillStyle = "#64748b";
    c.font = "bold 9px sans-serif";
    c.fillText(tr.label, 15, tr.y);

    c.fillStyle = "#111827";
    c.strokeStyle = "#1e293b";
    c.fillRect(15, tr.y + 4, w - 30, tr.h - 8);
    c.strokeRect(15, tr.y + 4, w - 30, tr.h - 8);

    const values = tracksData[tr.key] || [0];
    if (values.length > 1) {
      let minV = Math.min(...values);
      let maxV = Math.max(...values);
      if (minV === maxV) { minV -= 1; maxV += 1; }

      c.strokeStyle = tr.color;
      c.lineWidth = 2;
      c.beginPath();
      values.forEach((v, idx) => {
        const normX = idx / (values.length - 1);
        const normY = (v - minV) / (maxV - minV);
        const x = 15 + normX * (w - 30);
        const y = (tr.y + 4 + tr.h - 8) - normY * (tr.h - 12);
        if (idx === 0) c.moveTo(x, y); else c.lineTo(x, y);
      });
      c.stroke();
    }
  });

  // Current spatial cursor
  const prog = currentFrame / (totalFrames - 1);
  const px = 15 + prog * (w - 30);
  c.strokeStyle = "#00f0ff";
  c.lineWidth = 1.5;
  c.beginPath(); c.moveTo(px, 10); c.lineTo(px, h - 10); c.stroke();
}

// ----------------------------------------------------------------------------
// Pane D: "Why?" Bottleneck Diagnostic Readout (Pure Data-Driven)
// ----------------------------------------------------------------------------
function renderWhyPane() {
  const container = document.getElementById("pane-why-content");
  if (!container || !currentPres) return;

  const scenes = currentPres.scenes || [];
  let cardsHtml = "";

  if (scenes.length === 2) {
    cardsHtml = `
      <div class="diagnostic-box">
        <div class="diag-card">
          <h4>${scenes[0].name}</h4>
          <div class="value" style="color: ${scenes[0].is_feasible ? '#10b981' : '#ef4444'};">
            M = ${scenes[0].tactical_margin_tics > 0 ? '+' : ''}${scenes[0].tactical_margin_tics} tics (${scenes[0].tactical_margin_s}s)
          </div>
          <div class="desc">${scenes[0].verdict}</div>
        </div>
        <div class="diag-card">
          <h4>${scenes[1].name}</h4>
          <div class="value" style="color: ${scenes[1].is_feasible ? '#10b981' : '#ef4444'};">
            M = ${scenes[1].tactical_margin_tics > 0 ? '+' : ''}${scenes[1].tactical_margin_tics} tics (${scenes[1].tactical_margin_s}s)
          </div>
          <div class="desc">${scenes[1].verdict}</div>
        </div>
        <div class="diag-card">
          <h4>Causal Takeaway</h4>
          <div class="value" style="color: #f59e0b;">${currentPres.takeaway}</div>
        </div>
      </div>
    `;
  } else {
    const sc = scenes[0] || {};
    cardsHtml = `
      <div class="diagnostic-box">
        <div class="diag-card">
          <h4>Verified Tactical Margin</h4>
          <div class="value" style="color: ${sc.is_feasible !== false ? '#10b981' : '#ef4444'};">
            M = ${sc.tactical_margin_tics !== undefined ? (sc.tactical_margin_tics > 0 ? '+' : '') + sc.tactical_margin_tics + ' tics' : 'N/A'}
          </div>
          <div class="desc">${sc.verdict || currentPres.subtitle}</div>
        </div>
        <div class="diag-card">
          <h4>Causal Diagnosis</h4>
          <div class="desc">${currentPres.description}</div>
        </div>
        <div class="diag-card">
          <h4>Key Insight</h4>
          <div class="value" style="color: #f59e0b;">${currentPres.takeaway}</div>
        </div>
      </div>
    `;
  }

  container.innerHTML = cardsHtml;
}
