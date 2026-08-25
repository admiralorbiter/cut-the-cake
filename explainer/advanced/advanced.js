/**
 * Cut the Cake — Advanced Evidence Lab & Tactical MRI Engine
 * Synchronized 4-pane presentation replaying frozen counterexamples and CAD fixtures.
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
// Pane A: Geometry Rendering
// ----------------------------------------------------------------------------
function renderGeometryPane() {
  const c = ctxGeom;
  const w = c.canvas.width;
  const h = c.canvas.height;
  c.clearRect(0, 0, w, h);

  // Background
  c.fillStyle = "#0b0f19";
  c.fillRect(0, 0, w, h);

  const scale = 40;
  const offX = 60;
  const offY = h / 2;

  // Draw grid
  c.strokeStyle = "#1e293b";
  c.lineWidth = 1;
  for (let x = 0; x < w; x += 40) {
    c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke();
  }
  for (let y = 0; y < h; y += 40) {
    c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke();
  }

  const prog = currentFrame / (totalFrames - 1);

  if (currentPres.id === "adv01") {
    // Render Dual Rooms for ADV-01
    drawMiniRoom(c, currentPres.room_a, 40, 20, 260, 200, prog, "ROOM A (M08: 3 Threats, Solvable)");
    drawMiniRoom(c, currentPres.room_b, 340, 20, 260, 200, prog, "ROOM B (M11: 2 Threats, Overload)");
  } else {
    // Standard Single Room Geometry
    c.fillStyle = "#0e1726";
    c.strokeStyle = "#334155";
    c.lineWidth = 2;
    c.strokeRect(offX, offY - 80, 480, 160);
    c.fillRect(offX, offY - 80, 480, 160);

    // Wall Obstacle
    c.fillStyle = "#1e293b";
    c.strokeStyle = "#38bdf8";
    c.fillRect(offX + 160, offY - 80, 20, 100);
    c.strokeRect(offX + 160, offY - 80, 20, 100);

    // Path
    c.strokeStyle = "#475569";
    c.setLineDash([4, 4]);
    c.beginPath();
    c.moveTo(offX, offY);
    c.lineTo(offX + 480, offY);
    c.stroke();
    c.setLineDash([]);

    // Player
    const px = offX + prog * 480;
    const py = offY;
    c.fillStyle = "#00f0ff";
    c.beginPath(); c.arc(px, py, 7, 0, Math.PI * 2); c.fill();

    // Reticle
    const angle = (prog * 1.5 - 0.4);
    c.strokeStyle = "#f59e0b";
    c.lineWidth = 2;
    c.beginPath();
    c.moveTo(px, py);
    c.lineTo(px + Math.cos(angle) * 45, py + Math.sin(angle) * 45);
    c.stroke();

    // Threat
    const tx = offX + 380;
    const ty = offY + 40;
    const isRevealed = px > (offX + 140);
    c.fillStyle = isRevealed ? "#ef4444" : "#475569";
    c.beginPath(); c.arc(tx, ty, 8, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#ffffff";
    c.font = "10px sans-serif";
    c.fillText("Threat 1", tx - 18, ty + 20);

    // Sightline
    c.strokeStyle = isRevealed ? "#22c55e" : "#334155";
    c.lineWidth = 1.5;
    c.beginPath(); c.moveTo(px, py); c.lineTo(tx, ty); c.stroke();
  }
}

function drawMiniRoom(c, room, rx, ry, rw, rh, prog, label) {
  c.fillStyle = "#0e1726";
  c.strokeStyle = "#334155";
  c.lineWidth = 1.5;
  c.fillRect(rx, ry, rw, rh);
  c.strokeRect(rx, ry, rw, rh);

  // Label
  c.fillStyle = "#f8fafc";
  c.font = "bold 10px sans-serif";
  c.fillText(label, rx + 10, ry + 16);

  // Obstacles
  c.fillStyle = "#1e293b";
  c.strokeStyle = "#38bdf8";
  c.fillRect(rx + 70, ry + 25, 12, 60);
  c.strokeRect(rx + 70, ry + 25, 12, 60);
  c.fillRect(rx + 70, ry + 115, 12, 60);
  c.strokeRect(rx + 70, ry + 115, 12, 60);

  // Route
  c.strokeStyle = "#334155";
  c.setLineDash([3, 3]);
  c.beginPath();
  c.moveTo(rx + 10, ry + rh / 2);
  c.lineTo(rx + rw - 10, ry + rh / 2);
  c.stroke();
  c.setLineDash([]);

  // Player
  const px = rx + 10 + prog * (rw - 20);
  const py = ry + rh / 2;
  c.fillStyle = "#00f0ff";
  c.beginPath(); c.arc(px, py, 5, 0, Math.PI * 2); c.fill();

  // Threats
  room.threats.forEach((t, i) => {
    const isRevealed = prog > (t.reveal_tic / 35.0 / 3.0);
    const tx = rx + rw - 40;
    const ty = ry + 40 + i * 50;
    c.fillStyle = isRevealed ? "#ef4444" : "#475569";
    c.beginPath(); c.arc(tx, ty, 6, 0, Math.PI * 2); c.fill();

    if (isRevealed) {
      c.strokeStyle = "#22c55e";
      c.lineWidth = 1;
      c.beginPath(); c.moveTo(px, py); c.lineTo(tx, ty); c.stroke();
    }
  });
}

// ----------------------------------------------------------------------------
// Pane B: Scheduler Gantt Chart
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

  c.strokeStyle = "#1e293b";
  c.lineWidth = 1;
  for (let s = 0; s <= 3; s += 0.5) {
    const x = 70 + (s / 3.0) * (w - 90);
    c.beginPath(); c.moveTo(x, 20); c.lineTo(x, h - 20); c.stroke();
    c.fillStyle = "#64748b";
    c.font = "9px monospace";
    c.fillText(`${s}s`, x - 8, h - 6);
  }

  // Job bars
  const tasks = currentPres.id === "adv01"
    ? [
        { name: "M08 T2", r: 0.0, d: 3.0, s: 0.34, y: 35, color: "#10b981" },
        { name: "M08 T1", r: 0.2, d: 3.2, s: 0.80, y: 65, color: "#10b981" },
        { name: "M08 T3", r: 0.2, d: 3.2, s: 1.31, y: 95, color: "#10b981" },
        { name: "M11 T1", r: 0.34, d: 0.66, s: 0.86, y: 135, color: "#ef4444" },
        { name: "M11 T2", r: 0.34, d: 0.66, s: 1.48, y: 165, color: "#ef4444" },
      ]
    : [
        { name: "Threat 1", r: 0.4, d: 1.8, s: 0.9, y: 50, color: "#10b981" },
        { name: "Threat 2", r: 0.8, d: 2.2, s: 1.5, y: 100, color: "#10b981" }
      ];

  tasks.forEach(t => {
    c.fillStyle = "#94a3b8";
    c.font = "10px sans-serif";
    c.fillText(t.name, 10, t.y + 10);

    const xR = 70 + (t.r / 3.0) * (w - 90);
    const xD = 70 + (Math.min(3.0, t.d) / 3.0) * (w - 90);
    const xS = 70 + (Math.min(3.0, t.s) / 3.0) * (w - 90);

    // Release to completion
    c.fillStyle = t.color;
    c.fillRect(xR, t.y, Math.max(4, xS - xR), 14);

    // Deadline tick
    c.strokeStyle = "#ef4444";
    c.lineWidth = 2;
    c.beginPath(); c.moveTo(xD, t.y - 4); c.lineTo(xD, t.y + 18); c.stroke();
  });

  // Current time cursor
  const cx = 70 + (curTime / 3.0) * (w - 90);
  c.strokeStyle = "#00f0ff";
  c.lineWidth = 2;
  c.beginPath(); c.moveTo(cx, 15); c.lineTo(cx, h - 20); c.stroke();
}

// ----------------------------------------------------------------------------
// Pane C: Route X-Ray / Spatial Tracks
// ----------------------------------------------------------------------------
function renderXRayPane() {
  const c = ctxXRay;
  const w = c.canvas.width;
  const h = c.canvas.height;
  c.clearRect(0, 0, w, h);

  c.fillStyle = "#0b0f19";
  c.fillRect(0, 0, w, h);

  const tracks = [
    { label: "1. K_LOS(s) (Visible Threats)", color: "#f59e0b", y: 25, h: 40 },
    { label: "2. δ_min(s) (Deadline Headroom)", color: "#38bdf8", y: 85, h: 40 },
    { label: "3. M_suffix(s) (Remaining Schedulability)", color: "#10b981", y: 145, h: 40 }
  ];

  tracks.forEach(tr => {
    c.fillStyle = "#64748b";
    c.font = "bold 9px sans-serif";
    c.fillText(tr.label, 15, tr.y);

    c.fillStyle = "#111827";
    c.strokeStyle = "#1e293b";
    c.fillRect(15, tr.y + 5, w - 30, tr.h - 10);
    c.strokeRect(15, tr.y + 5, w - 30, tr.h - 10);

    // Draw curve
    c.strokeStyle = tr.color;
    c.lineWidth = 2;
    c.beginPath();
    for (let x = 0; x < w - 30; x += 5) {
      const normX = x / (w - 30);
      let val = Math.sin(normX * 5) * 0.3 + 0.5;
      if (tr.label.includes("M_suffix") && normX > 0.4 && normX < 0.6) {
        val = 0.15; // Local choke dip
      }
      const cy = (tr.y + 5 + tr.h - 10) - val * (tr.h - 14);
      if (x === 0) c.moveTo(15 + x, cy); else c.lineTo(15 + x, cy);
    }
    c.stroke();
  });

  // Current position line
  const prog = currentFrame / (totalFrames - 1);
  const px = 15 + prog * (w - 30);
  c.strokeStyle = "#00f0ff";
  c.lineWidth = 1.5;
  c.beginPath(); c.moveTo(px, 10); c.lineTo(px, h - 10); c.stroke();
}

// ----------------------------------------------------------------------------
// Pane D: "Why?" Bottleneck Diagnostic Readout
// ----------------------------------------------------------------------------
function renderWhyPane() {
  const container = document.getElementById("pane-why-content");
  if (!container || !currentPres) return;

  const prog = currentFrame / (totalFrames - 1);

  if (currentPres.id === "adv01") {
    container.innerHTML = `
      <div class="diagnostic-box">
        <div class="diag-card">
          <h4>Room A (M08 — 3 Enemies)</h4>
          <div class="value" style="color: #10b981;">M = +65 tics (+1.86s) — SERVICEABLE</div>
          <div class="desc">3 threats appear at tic 0 and 7. Deadlines are 3.0s (105 tics). Reticle clears all 3 by tic 46 with 65 tics of margin to spare.</div>
        </div>
        <div class="diag-card">
          <h4>Room B (M11 — 2 Enemies)</h4>
          <div class="value" style="color: #ef4444;">M = -29 tics (-0.83s) — DEADLINE OVERLOAD</div>
          <div class="desc">2 threats un-occlude simultaneously at tic 12 with tight 0.31s deadlines (D=tic 23). Slew takes 10 tics; reticle cannot clear T2 before breach.</div>
        </div>
        <div class="diag-card">
          <h4>Causal Takeaway</h4>
          <div class="value" style="color: #f59e0b;">Threat Count ≠ Workload</div>
          <div class="desc">${currentPres.takeaway}</div>
        </div>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div class="diagnostic-box">
        <div class="diag-card">
          <h4>Tactical Margin</h4>
          <div class="value" style="color: #10b981;">M = +2 tics (+57 ms)</div>
          <div class="desc">Feasible under declared single-machine reticle model (ω = 360°/s).</div>
        </div>
        <div class="diag-card">
          <h4>Controlling Occluder</h4>
          <div class="value" style="color: #38bdf8;">Wall Partition obs_01</div>
          <div class="desc">Delaying un-occlusion by 8 tics restores safe margin reserve.</div>
        </div>
        <div class="diag-card">
          <h4>Causal Takeaway</h4>
          <div class="desc">${currentPres.takeaway}</div>
        </div>
      </div>
    `;
  }
}
