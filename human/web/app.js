/**
 * Tactical Clearability — Human FPS Experimental Instrument (Three.js WebGL)
 * 
 * Architecture:
 * 1. Global continuous 60/120/144 Hz render loop (always renders scene & camera).
 * 2. 35 Hz discrete experimental logic clock + high-res telemetry logging.
 * 3. True independent route locomotion (p(t) = gamma(t)) unaffected by mouse aim.
 * 4. Gated weapon service: acquisition cone (±12 deg) + Left Click held for 100 ms.
 * 5. Pre-session empirical calibration: Reaction Latency (A) and Aim Slew (omega).
 * 6. In-canvas trial flow: CLICK TO READY -> 3-2-1-GO -> Encounter -> 1-7 Ratings -> JSON Export.
 */

// =============================================================================
// STATE & CONSTANTS
// =============================================================================
let TRIAL_SPEC = null;
let renderer, scene, camera;
let isPointerLocked = false;

// Player camera state
let playerYaw = 0.0;    // Radians
let playerPitch = 0.0;  // Radians
const MOUSE_SENSITIVITY = 0.0022;

// Input tracking
let isMouseDown = false;
let highResTelemetry = [];
let modelTicTelemetry = [];

// Session execution state
let currentSession = {
  sessionId: '',
  participantId: 'jon',
  mode: 'vertical_slice',
  calibration: {
    reactionLatencyMs: 150.0,
    aimVelocityDegS: 360.0,
    reactionTrials: [],
    slewTrials: []
  },
  trials: []
};

let currentTrialState = {
  active: false,
  startTime: 0,
  lastModelTic: -1,
  arenaSpec: null,
  targets: []
};

let currentArenaMeshes = [];

// =============================================================================
// INITIALIZATION & TRIAL SPEC LOADER
// =============================================================================
window.addEventListener('DOMContentLoaded', async () => {
  if (window.TRIAL_SPEC) {
    TRIAL_SPEC = window.TRIAL_SPEC;
    console.log('[Instrument] Loaded TrialSpec v2.0 from window object:', TRIAL_SPEC);
  } else {
    try {
      const res = await fetch('data/trial_spec_v1.json');
      TRIAL_SPEC = await res.json();
      console.log('[Instrument] Loaded TrialSpec v2.0 successfully:', TRIAL_SPEC);
    } catch (err) {
      console.error('[Instrument] Failed to load TrialSpec:', err);
      alert('Failed to load trial_spec_v1.json. Ensure files are served via HTTP or local server.');
      return;
    }
  }

  initThreeJS();
  initPointerLock();
  initUIHandlers();

  // Build default preview arena so the canvas is immediately rich and visible
  buildArena3D(TRIAL_SPEC.vertical_slice_encounter);
});

function initThreeJS() {
  const container = document.getElementById('viewport-container');
  const canvas = document.getElementById('webgl-canvas');

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2.0));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070b10);
  scene.fog = new THREE.FogExp2(0x070b10, 0.015);

  // Standardized Camera: 90 deg Horizontal FOV
  const aspect = window.innerWidth / window.innerHeight;
  camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 100);
  camera.position.set(0, 1.70, 0);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
  scene.add(ambientLight);

  const dirLight = new THREE.DirectionalLight(0xffffff, 0.95);
  dirLight.position.set(10, 20, 15);
  scene.add(dirLight);

  const dirLight2 = new THREE.DirectionalLight(0x58a6ff, 0.45);
  dirLight2.position.set(-10, 12, -12);
  scene.add(dirLight2);

  window.addEventListener('resize', onWindowResize);

  // Start continuous render loop
  requestAnimationFrame(globalRenderLoop);
}

function onWindowResize() {
  if (!camera || !renderer) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

// Global Continuous Render Loop (Always rendering at display refresh rate)
function globalRenderLoop() {
  requestAnimationFrame(globalRenderLoop);

  if (currentTrialState.active) {
    updateActiveTrial();
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

// =============================================================================
// POINTER LOCK & MOUSE AIM
// =============================================================================
function initPointerLock() {
  const canvas = document.getElementById('webgl-canvas');

  document.addEventListener('pointerlockchange', () => {
    isPointerLocked = (document.pointerLockElement === canvas);
    console.log('[PointerLock] State changed:', isPointerLocked);
  });

  document.addEventListener('mousemove', (e) => {
    if (!isPointerLocked) return;

    playerYaw -= e.movementX * MOUSE_SENSITIVITY;
    playerPitch -= e.movementY * MOUSE_SENSITIVITY;

    // Clamp pitch to [-45 deg, +45 deg]
    const maxPitch = 45 * Math.PI / 180;
    playerPitch = Math.max(-maxPitch, Math.min(maxPitch, playerPitch));

    updateCameraRotation();

    if (currentTrialState.active) {
      highResTelemetry.push({
        timestampMs: performance.now(),
        type: 'mouse_move',
        yawDeg: playerYaw * 180 / Math.PI,
        pitchDeg: playerPitch * 180 / Math.PI
      });
    }
  });

  document.addEventListener('mousedown', (e) => {
    if (e.button === 0) {
      isMouseDown = true;
      if (currentTrialState.active) {
        highResTelemetry.push({
          timestampMs: performance.now(),
          type: 'mouse_down'
        });
      }
    }
  });

  document.addEventListener('mouseup', (e) => {
    if (e.button === 0) {
      isMouseDown = false;
      if (currentTrialState.active) {
        highResTelemetry.push({
          timestampMs: performance.now(),
          type: 'mouse_up'
        });
      }
    }
  });
}

function updateCameraRotation() {
  const euler = new THREE.Euler(0, 0, 0, 'YXZ');
  euler.x = playerPitch;
  euler.y = playerYaw;
  camera.quaternion.setFromEuler(euler);
}

function requestPointerLock() {
  const canvas = document.getElementById('webgl-canvas');
  canvas.requestPointerLock();
}

// =============================================================================
// 3D GEOMETRY BUILDER (Aim Lab / SUPERHOT Aesthetic)
// =============================================================================
function buildArena3D(moduleSpec) {
  currentArenaMeshes.forEach(m => scene.remove(m));
  currentArenaMeshes = [];

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.6, metalness: 0.1 });
  const wallEdgeMat = new THREE.LineBasicMaterial({ color: 0x58a6ff, linewidth: 2 });
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x0c131d, roughness: 0.8, metalness: 0.1 });

  // 1. Floor Plane & Grid
  const floorGeo = new THREE.PlaneGeometry(20, 24);
  const floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotation.x = -Math.PI / 2;
  floorMesh.position.set(0, 0, -4);
  scene.add(floorMesh);
  currentArenaMeshes.push(floorMesh);

  const gridHelper = new THREE.GridHelper(24, 24, 0x58a6ff, 0x1e293b);
  gridHelper.position.set(0, 0.01, -4);
  scene.add(gridHelper);
  currentArenaMeshes.push(gridHelper);

  // 2. Extrude Obstacle Polygons
  const wallHeight = TRIAL_SPEC.physics_constants.wall_height_m;

  moduleSpec.obstacles.forEach(obsPts => {
    const shape = new THREE.Shape();
    shape.moveTo(obsPts[0].y, -obsPts[0].x);
    for (let i = 1; i < obsPts.length; i++) {
      shape.lineTo(obsPts[i].y, -obsPts[i].x);
    }
    shape.closePath();

    const extrudeSettings = { depth: wallHeight, bevelEnabled: false };
    const obsGeo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    obsGeo.rotateX(-Math.PI / 2);

    const obsMesh = new THREE.Mesh(obsGeo, wallMat);
    obsMesh.position.set(0, 0, 0);
    scene.add(obsMesh);
    currentArenaMeshes.push(obsMesh);

    const edges = new THREE.EdgesGeometry(obsGeo);
    const line = new THREE.LineSegments(edges, wallEdgeMat);
    line.position.set(0, 0, 0);
    scene.add(line);
    currentArenaMeshes.push(line);
  });

  // 3. Perimeter Boundary Walls
  const leftWallGeo = new THREE.BoxGeometry(0.2, wallHeight, 16);
  const leftWall = new THREE.Mesh(leftWallGeo, wallMat);
  leftWall.position.set(-2.5, wallHeight / 2, -4);
  scene.add(leftWall);
  currentArenaMeshes.push(leftWall);

  const rightWallGeo = new THREE.BoxGeometry(0.2, wallHeight, 16);
  const rightWall = new THREE.Mesh(rightWallGeo, wallMat);
  rightWall.position.set(2.5, wallHeight / 2, -4);
  scene.add(rightWall);
  currentArenaMeshes.push(rightWall);

  [leftWall, rightWall].forEach(w => {
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(w.geometry), wallEdgeMat);
    edge.position.copy(w.position);
    scene.add(edge);
    currentArenaMeshes.push(edge);
  });

  // 4. Target Dummies
  const targets = [];
  moduleSpec.threats.forEach(t => {
    const group = new THREE.Group();

    // Body Cylinder
    const bodyGeo = new THREE.CylinderGeometry(0.22, 0.24, 0.90, 24);
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5, metalness: 0.1 });
    const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    bodyMesh.position.y = 0.45;
    group.add(bodyMesh);

    // Head Sphere
    const headGeo = new THREE.SphereGeometry(0.20, 24, 24);
    const headMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.5, metalness: 0.1 });
    const headMesh = new THREE.Mesh(headGeo, headMat);
    headMesh.position.y = 1.05;
    group.add(headMesh);

    // Target Lock Ring
    const ringGeo = new THREE.RingGeometry(0.32, 0.38, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x58a6ff, side: THREE.DoubleSide });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.y = 1.05;
    group.add(ringMesh);

    // Map Coordinates
    const worldX = t.anchor.y;
    const worldZ = -t.anchor.x;
    group.position.set(worldX, 0, worldZ);

    scene.add(group);
    currentArenaMeshes.push(group);

    targets.push({
      id: t.id,
      group,
      bodyMesh,
      headMesh,
      ringMesh,
      spec: t,
      worldX,
      worldZ,
      worldY: 1.05,
      isRevealed: false,
      isServiced: false,
      serviceProgressS: 0.0,
      requiredServiceS: t.service_duration_s,
      deadlineS: t.deadline_ms / 1000.0,
      revealS: t.reveal_ms / 1000.0
    });
  });

  return targets;
}

// =============================================================================
// ROUTE INTERPOLATION & OCCLUSION
// =============================================================================
function getRoutePosition(waypoints, s) {
  if (!waypoints || waypoints.length === 0) return { x: 0, z: 0 };
  if (waypoints.length === 1) return { x: waypoints[0].y, z: -waypoints[0].x };

  const lens = [];
  let total = 0.0;
  for (let i = 0; i < waypoints.length - 1; i++) {
    const dx = waypoints[i + 1].x - waypoints[i].x;
    const dy = waypoints[i + 1].y - waypoints[i].y;
    const d = Math.hypot(dx, dy);
    lens.push(d);
    total += d;
  }

  const clampedS = Math.max(0, Math.min(total, s));
  let accum = 0.0;
  for (let i = 0; i < waypoints.length - 1; i++) {
    if (accum + lens[i] >= clampedS) {
      const rem = clampedS - accum;
      const r = lens[i] > 0 ? rem / lens[i] : 0;
      const px = waypoints[i].x + (waypoints[i + 1].x - waypoints[i].x) * r;
      const py = waypoints[i].y + (waypoints[i + 1].y - waypoints[i].y) * r;
      return { x: py, z: -px };
    }
    accum += lens[i];
  }
  const last = waypoints[waypoints.length - 1];
  return { x: last.y, z: -last.x };
}

function checkTargetOcclusion(playerPos, target, obstaclePolygons) {
  const p1 = { x: -playerPos.z, y: playerPos.x };
  const p2 = { x: target.spec.anchor.x, y: target.spec.anchor.y };

  for (const poly of obstaclePolygons) {
    for (let i = 0; i < poly.length; i++) {
      const s1 = poly[i];
      const s2 = poly[(i + 1) % poly.length];
      if (segmentsIntersect(p1, p2, s1, s2)) {
        return true;
      }
    }
  }
  return false;
}

function segmentsIntersect(a, b, c, d) {
  function ccw(p1, p2, p3) {
    return (p3.y - p1.y) * (p2.x - p1.x) > (p2.y - p1.y) * (p3.x - p1.x);
  }
  return (ccw(a, c, d) !== ccw(b, c, d)) && (ccw(a, b, c) !== ccw(a, b, d));
}

// =============================================================================
// ACTIVE TRIAL UPDATE (Called by globalRenderLoop)
// =============================================================================
function updateActiveTrial() {
  const state = currentTrialState;
  const now = performance.now();
  const elapsedTimeS = (now - state.startTime) / 1000.0;
  
  document.getElementById('hud-time-display').textContent = `${elapsedTimeS.toFixed(2)}s`;

  const vMove = TRIAL_SPEC.physics_constants.v_move_mps;
  const eyeHeight = TRIAL_SPEC.physics_constants.player_eye_height_m;
  const waypoints = state.arenaSpec.route.waypoints;

  // Autonomous forward position gamma(t)
  const currentDist = vMove * elapsedTimeS;
  const currentPos = getRoutePosition(waypoints, currentDist);
  camera.position.set(currentPos.x, eyeHeight, currentPos.z);

  // 35 Hz Model Clock
  const currentModelTic = Math.floor(elapsedTimeS * 35.0);
  if (currentModelTic > state.lastModelTic) {
    state.lastModelTic = currentModelTic;
    modelTicTelemetry.push({
      tic: currentModelTic,
      timeS: elapsedTimeS,
      posX: currentPos.x,
      posZ: currentPos.z,
      yawDeg: playerYaw * 180 / Math.PI,
      isMouseDown
    });
  }

  let activeLockTarget = null;

  state.targets.forEach(t => {
    if (t.isServiced) return;

    const isOccluded = checkTargetOcclusion(camera.position, t, state.arenaSpec.obstacles);
    
    if (!isOccluded && !t.isRevealed) {
      t.isRevealed = true;
      t.revealActualS = elapsedTimeS;
      state.trialRecord.threatsRevealed[t.id] = elapsedTimeS;

      // Glow Red / Amber
      t.bodyMesh.material.color.setHex(0xff3333);
      t.bodyMesh.material.emissive = new THREE.Color(0xaa1111);
      t.headMesh.material.color.setHex(0xffaa22);
      t.headMesh.material.emissive = new THREE.Color(0x553311);

      // Direct pre-aim error
      const dx = t.worldX - camera.position.x;
      const dz = t.worldZ - camera.position.z;
      const targetBearingYaw = Math.atan2(-dx, -dz);
      const errDeg = Math.abs(angleDiffDeg(playerYaw * 180 / Math.PI, targetBearingYaw * 180 / Math.PI));
      state.trialRecord.revealAimErrorsDeg[t.id] = round2(errDeg);
    }

    // Deadline check
    if (t.isRevealed && !t.isServiced) {
      const timeSinceReveal = elapsedTimeS - t.revealActualS;
      if (timeSinceReveal >= t.spec.due_window_s) {
        state.trialRecord.playerSurvived = false;
        state.trialRecord.deathReason = `Deadline breach on ${t.id}`;
        state.trialRecord.deathTimeS = elapsedTimeS;
        finishCurrentTrial();
        return;
      }
    }

    // Crosshair alignment & hold-to-service
    if (t.isRevealed && !t.isServiced) {
      const dx = t.worldX - camera.position.x;
      const dz = t.worldZ - camera.position.z;
      const targetBearingYaw = Math.atan2(-dx, -dz);
      const angDiff = Math.abs(angleDiffDeg(playerYaw * 180 / Math.PI, targetBearingYaw * 180 / Math.PI));

      if (angDiff <= TRIAL_SPEC.physics_constants.aim_tolerance_deg) {
        activeLockTarget = t;

        if (isMouseDown) {
          t.serviceProgressS += 1.0 / 60.0;
          const fillPct = Math.min(100, (t.serviceProgressS / t.requiredServiceS) * 100);

          document.getElementById('hud-service-bar-container').style.display = 'flex';
          document.getElementById('service-target-label').textContent = `SERVICING ${t.id}`;
          document.getElementById('service-fill').style.width = `${fillPct}%`;

          if (t.serviceProgressS >= t.requiredServiceS) {
            t.isServiced = true;
            state.trialRecord.threatsServiced[t.id] = elapsedTimeS;
            t.group.visible = false;
            document.getElementById('hud-service-bar-container').style.display = 'none';
          }
        }
      }
    }
  });

  const chRing = document.getElementById('ch-lock-ring');
  if (activeLockTarget) {
    chRing.classList.add('locked');
  } else {
    chRing.classList.remove('locked');
    if (!isMouseDown) {
      document.getElementById('hud-service-bar-container').style.display = 'none';
    }
  }

  const allServiced = state.targets.every(t => t.isServiced);
  const totalTraversalTime = state.arenaSpec.route.total_length_m / vMove;
  if (allServiced || elapsedTimeS >= totalTraversalTime + 0.5) {
    finishCurrentTrial();
  }
}

function finishCurrentTrial() {
  if (!currentTrialState.active) return;
  currentTrialState.active = false;

  const elapsedTimeS = (performance.now() - currentTrialState.startTime) / 1000.0;
  currentTrialState.trialRecord.totalClearTimeS = elapsedTimeS;

  document.getElementById('hud-top-bar').style.display = 'none';
  document.getElementById('hud-service-bar-container').style.display = 'none';

  if (document.exitPointerLock) document.exitPointerLock();

  if (currentTrialState.resolveCallback) {
    promptRatings(currentTrialState.trialRecord, currentTrialState.isPractice).then((rec) => {
      currentTrialState.resolveCallback(rec);
    });
  }
}

// =============================================================================
// TRIAL RUNNER
// =============================================================================
async function runTrialSequence(arenaSpec, stageName, isPractice = false) {
  return new Promise((resolve) => {
    const targets = buildArena3D(arenaSpec);
    const waypoints = arenaSpec.route.waypoints;
    const eyeHeight = TRIAL_SPEC.physics_constants.player_eye_height_m;

    // Reset camera position to start of route
    const startPos = getRoutePosition(waypoints, 0);
    camera.position.set(startPos.x, eyeHeight, startPos.z);
    playerYaw = 0.0;
    playerPitch = 0.0;
    updateCameraRotation();

    // Show ready prompt
    const promptModal = document.getElementById('ready-prompt');
    const promptTitle = document.getElementById('prompt-title');
    const promptDesc = document.getElementById('prompt-desc');
    const promptStage = document.getElementById('prompt-stage-tag');
    const btnLock = document.getElementById('btn-lock-pointer');

    promptStage.textContent = stageName.toUpperCase();
    promptTitle.textContent = arenaSpec.name;
    promptDesc.textContent = isPractice
      ? "PRACTICE RUN: Focus on corner slicing, centering, and holding Left Click to eliminate targets."
      : "EXPERIMENTAL TRIAL: Move through the encounter. Aim and hold Left Click to neutralize threats before deadlines.";
    
    promptModal.style.display = 'flex';

    btnLock.onclick = async () => {
      requestPointerLock();
      promptModal.style.display = 'none';

      // 2. Countdown sequence (2.0s preview)
      const countdownOverlay = document.getElementById('countdown-overlay');
      const countdownText = document.getElementById('countdown-text');
      countdownOverlay.style.display = 'flex';

      const countdownSteps = ['3', '2', '1', 'GO!'];
      for (const step of countdownSteps) {
        countdownText.textContent = step;
        await sleep(500);
      }
      countdownOverlay.style.display = 'none';

      // 3. Activate Trial
      document.getElementById('hud-top-bar').style.display = 'flex';
      document.getElementById('hud-phase-name').textContent = stageName;
      document.getElementById('hud-trial-name').textContent = arenaSpec.name;

      const trialRecord = {
        arenaId: arenaSpec.module_id,
        isPractice,
        startTimeUtc: new Date().toISOString(),
        playerSurvived: true,
        deathReason: null,
        deathTimeS: null,
        totalClearTimeS: null,
        threatsServiced: {},
        threatsRevealed: {},
        revealAimErrorsDeg: {},
        ratings: { readability: null, fairness: null }
      };

      currentTrialState = {
        active: true,
        startTime: performance.now(),
        lastModelTic: -1,
        arenaSpec,
        targets,
        isPractice,
        trialRecord,
        resolveCallback: resolve
      };
    };
  });
}

function promptRatings(trialRecord, isPractice) {
  return new Promise((resolve) => {
    const ratingModal = document.getElementById('rating-modal');
    const btnSubmit = document.getElementById('btn-submit-ratings');

    let selectedReadability = null;
    let selectedFairness = null;

    document.querySelectorAll('.btn-rate').forEach(b => b.classList.remove('selected'));
    btnSubmit.disabled = true;

    document.querySelectorAll('#row-readability .btn-rate').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('#row-readability .btn-rate').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedReadability = parseInt(btn.dataset.val);
        checkSubmitReady();
      };
    });

    document.querySelectorAll('#row-fairness .btn-rate').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('#row-fairness .btn-rate').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedFairness = parseInt(btn.dataset.val);
        checkSubmitReady();
      };
    });

    function checkSubmitReady() {
      if (selectedReadability !== null && selectedFairness !== null) {
        btnSubmit.disabled = false;
      }
    }

    btnSubmit.onclick = () => {
      trialRecord.ratings.readability = selectedReadability;
      trialRecord.ratings.fairness = selectedFairness;
      ratingModal.style.display = 'none';
      resolve(trialRecord);
    };

    ratingModal.style.display = 'flex';
  });
}

// =============================================================================
// PRE-SESSION SENSORIMOTOR CALIBRATION
// =============================================================================
async function runAcquisitionCalibration() {
  const protocol = TRIAL_SPEC.calibration_protocol.reaction_stage;
  const promptModal = document.getElementById('ready-prompt');
  document.getElementById('prompt-stage-tag').textContent = 'CALIBRATION STAGE 1 / 2';
  document.getElementById('prompt-title').textContent = protocol.name;
  document.getElementById('prompt-desc').textContent = protocol.instructions;
  promptModal.style.display = 'flex';

  await new Promise(r => { document.getElementById('btn-lock-pointer').onclick = r; });
  requestPointerLock();
  promptModal.style.display = 'none';

  // Build calibration arena (neutral room with floor grid)
  currentArenaMeshes.forEach(m => scene.remove(m));
  currentArenaMeshes = [];

  const floorGeo = new THREE.PlaneGeometry(16, 16);
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x0c131d, roughness: 0.8 });
  const floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotation.x = -Math.PI / 2;
  scene.add(floorMesh);
  currentArenaMeshes.push(floorMesh);

  const grid = new THREE.GridHelper(16, 16, 0x58a6ff, 0x1e293b);
  grid.position.y = 0.01;
  scene.add(grid);
  currentArenaMeshes.push(grid);

  const latencies = [];
  document.getElementById('hud-top-bar').style.display = 'flex';

  for (let i = 0; i < protocol.n_trials; i++) {
    document.getElementById('hud-phase-name').textContent = 'REACTION CALIBRATION';
    document.getElementById('hud-trial-name').textContent = `Onset Tap ${i + 1} / ${protocol.n_trials}`;

    camera.position.set(0, 1.7, 0);
    playerYaw = 0; playerPitch = 0; updateCameraRotation();

    const delayMs = 800 + Math.random() * 1200;
    await sleep(delayMs);

    const offsetDeg = protocol.angular_offsets_deg[i % protocol.angular_offsets_deg.length];
    const offsetRad = offsetDeg * Math.PI / 180;
    const targetDist = 4.0;

    const tx = -Math.sin(offsetRad) * targetDist;
    const tz = -Math.cos(offsetRad) * targetDist;

    const targetGeo = new THREE.SphereGeometry(0.24, 24, 24);
    const targetMat = new THREE.MeshBasicMaterial({ color: 0xffaa22 });
    const targetMesh = new THREE.Mesh(targetGeo, targetMat);
    targetMesh.position.set(tx, 1.7, tz);
    scene.add(targetMesh);

    const onsetTime = performance.now();
    let clicked = false;

    await new Promise((resolveTap) => {
      function checkClick(e) {
        if (e.button === 0 && !clicked) {
          clicked = true;
          const latencyMs = performance.now() - onsetTime;
          latencies.push(latencyMs);
          document.removeEventListener('mousedown', checkClick);
          scene.remove(targetMesh);
          resolveTap();
        }
      }
      document.addEventListener('mousedown', checkClick);
    });

    await sleep(300);
  }

  if (document.exitPointerLock) document.exitPointerLock();
  document.getElementById('hud-top-bar').style.display = 'none';

  latencies.sort((a, b) => a - b);
  const medianLatencyMs = latencies[Math.floor(latencies.length / 2)];
  console.log('[Calibration] Measured A_player latencies:', latencies, 'Median:', medianLatencyMs);

  return medianLatencyMs;
}

// =============================================================================
// MAIN SESSION DISPATCHER
// =============================================================================
async function startExperimentalSession() {
  const participantId = document.getElementById('input-participant').value.trim() || 'jon';
  const sessionType = document.getElementById('select-session-type').value;

  currentSession.participantId = participantId;
  currentSession.sessionId = `web_pilot_${participantId}_${Date.now()}`;
  currentSession.mode = sessionType;

  document.getElementById('ui-overlay').style.display = 'none';

  if (sessionType === 'vertical_slice' || sessionType === 'calibration_only') {
    const measuredA = await runAcquisitionCalibration();
    currentSession.calibration.reactionLatencyMs = round1(measuredA);
  }

  if (sessionType === 'calibration_only') {
    showSessionReport();
    return;
  }

  if (sessionType === 'vertical_slice' || sessionType === 'practice_only') {
    for (let i = 0; i < TRIAL_SPEC.practice_arenas.length; i++) {
      const pArena = TRIAL_SPEC.practice_arenas[i];
      const pRecord = await runTrialSequence(pArena, `PRACTICE ${i + 1}`, true);
      currentSession.trials.push(pRecord);
    }
  }

  if (sessionType === 'practice_only') {
    showSessionReport();
    return;
  }

  if (sessionType === 'vertical_slice' || sessionType === 'stim06_only') {
    const stim06 = TRIAL_SPEC.vertical_slice_encounter;
    const stimRecord = await runTrialSequence(stim06, 'BLOCK 1 (ENCOUNTER 01)', false);
    currentSession.trials.push(stimRecord);
  }

  showSessionReport();
}

function showSessionReport() {
  document.getElementById('ui-overlay').style.display = 'flex';
  document.getElementById('card-welcome').style.display = 'none';
  const reportCard = document.getElementById('card-report');
  reportCard.style.display = 'flex';

  const metricsGrid = document.getElementById('metrics-summary');
  const calibA = currentSession.calibration.reactionLatencyMs;
  const trialsCount = currentSession.trials.length;
  const survivedCount = currentSession.trials.filter(t => t.playerSurvived).length;

  metricsGrid.innerHTML = `
    <div class="metric-box">
      <span class="metric-lbl">Participant</span>
      <span class="metric-val">${currentSession.participantId}</span>
    </div>
    <div class="metric-box">
      <span class="metric-lbl">Calibrated Latency (A)</span>
      <span class="metric-val">${calibA} ms</span>
    </div>
    <div class="metric-box">
      <span class="metric-lbl">Encounters Completed</span>
      <span class="metric-val">${survivedCount} / ${trialsCount} Survived</span>
    </div>
  `;

  const stimTrial = currentSession.trials.find(t => t.arenaId === 'STIM_06_K3_ModestPivot');
  const parityBox = document.getElementById('parity-verdict-box');

  if (stimTrial) {
    const canonSpec = TRIAL_SPEC.vertical_slice_encounter.canonical_schedule;
    parityBox.innerHTML = `
      <h3>Flagship Encounter Parity: STIM_06 Double Baffle Pivot</h3>
      <p><strong>Theoretical Source Model:</strong> M_reveal = ${canonSpec.m_reveal_tics} tics (${canonSpec.m_reveal_ms}ms, Unserviceable) | Critical Lead ℓ* = ${canonSpec.ell_star_tics} tics (${canonSpec.ell_star_ms}ms)</p>
      <p><strong>Human Result:</strong> ${stimTrial.playerSurvived ? '<span class="parity-tag-pass">SURVIVED ✓</span>' : '<span style="color:#f85149; font-weight:800;">DEADLINE BREACH ✗</span>'} | Clear Time: ${stimTrial.totalClearTimeS ? stimTrial.totalClearTimeS.toFixed(2) + 's' : 'N/A'}</p>
      <p><strong>Subjective Ratings:</strong> Readability = ${stimTrial.ratings.readability}/7 | Fairness = ${stimTrial.ratings.fairness}/7</p>
      <p><strong>Measured Reveal Aim Errors:</strong> ${JSON.stringify(stimTrial.revealAimErrorsDeg)}</p>
    `;
  } else {
    parityBox.innerHTML = `<p>Calibration completed successfully. Ready for empirical stimulus runs.</p>`;
  }

  document.getElementById('btn-download-json').onclick = downloadTelemetryJSON;
  document.getElementById('btn-restart-session').onclick = () => {
    location.reload();
  };
}

function downloadTelemetryJSON() {
  const exportPayload = {
    schema_version: '2.0.0',
    created_utc: new Date().toISOString(),
    session: currentSession,
    model_tic_telemetry: modelTicTelemetry,
    high_res_events: highResTelemetry
  };

  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentSession.sessionId}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function initUIHandlers() {
  document.getElementById('btn-start-session').onclick = startExperimentalSession;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function angleDiffDeg(a, b) {
  let diff = (a - b) % 360;
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;
  return diff;
}

function round1(v) { return Math.round(v * 10) / 10; }
function round2(v) { return Math.round(v * 100) / 100; }
