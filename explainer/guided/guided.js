const NS='http://www.w3.org/2000/svg';
const DEG_PER_TIC=360/35;
const $=id=>document.getElementById(id);
const svgEl=(tag,attrs={})=>{const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));return n};

function renderAngleLab() {
  const d = +$('distance-slider').value;
  const dx = +$('slice-slider').value;
  const theta = Math.atan(dx / d) * 180 / Math.PI;

  $('distance-val').textContent = `${d.toFixed(2)} m`;
  $('slice-val').textContent = `${dx.toFixed(2)} m`;
  $('angle-val').textContent = `${theta.toFixed(1)}°`;

  const s = $('angle-svg');
  s.innerHTML = '';

  // 1. Defs: Shadows, Grids & Hatching
  const defs = svgEl('defs');
  defs.innerHTML = `
    <pattern id="angle-grid" width="16" height="16" patternUnits="userSpaceOnUse">
      <path d="M 16 0 L 0 0 0 16" fill="none" stroke="rgba(88, 166, 255, 0.05)" stroke-width="1"/>
    </pattern>
    <pattern id="wall-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(88, 166, 255, 0.25)" stroke-width="2" />
    </pattern>
    <filter id="corner-shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="3" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  `;
  s.append(defs);

  // Background & Grid
  s.append(svgEl('rect', { x: 5, y: 5, width: 510, height: 290, fill: '#0a0e14', stroke: '#30363d', rx: 6 }));
  s.append(svgEl('rect', { x: 5, y: 5, width: 510, height: 290, fill: 'url(#angle-grid)' }));

  // Geometry Constants
  const cornerX = 260;
  const cornerY = 210;
  const scale = 95; // pixels per meter

  const px1 = cornerX - d * scale;
  const py1 = cornerY;

  const px2 = px1;
  const py2 = cornerY - dx * scale;

  // Unoccluded room depths
  const targetX = cornerX + 160;
  const targetY = 70;

  // 2. Corner Obstacle Walls (L-Corner)
  // Vertical Wall
  const vWall = svgEl('rect', { x: cornerX, y: 20, width: 28, height: cornerY - 20, fill: '#161b22', stroke: '#58a6ff', 'stroke-width': 1.5, filter: 'url(#corner-shadow)', rx: 2 });
  s.append(vWall);
  const vHatch = svgEl('rect', { x: cornerX + 2, y: 22, width: 24, height: cornerY - 24, fill: 'url(#wall-hatch)', opacity: 0.45 });
  s.append(vHatch);

  // Horizontal Wall
  const hWall = svgEl('rect', { x: cornerX, y: cornerY, width: 245, height: 28, fill: '#161b22', stroke: '#58a6ff', 'stroke-width': 1.5, filter: 'url(#corner-shadow)', rx: 2 });
  s.append(hWall);
  const hHatch = svgEl('rect', { x: cornerX + 2, y: cornerY + 2, width: 241, height: 24, fill: 'url(#wall-hatch)', opacity: 0.45 });
  s.append(hHatch);

  // Wall bevel caps
  s.append(svgEl('line', { x1: cornerX, y1: 22, x2: cornerX + 28, y2: 22, stroke: 'rgba(136, 192, 255, 0.8)', 'stroke-width': 2 }));
  s.append(svgEl('line', { x1: cornerX + 28, y1: cornerY + 2, x2: cornerX + 245, y2: cornerY + 2, stroke: 'rgba(136, 192, 255, 0.8)', 'stroke-width': 2 }));

  // Corner pivot vertex pip
  s.append(svgEl('circle', { cx: cornerX, cy: cornerY, r: 4, fill: '#58a6ff', stroke: '#fff', 'stroke-width': 1.5 }));
  const cornerTag = svgEl('text', { x: cornerX + 35, y: cornerY - 8, fill: '#8fa1b4', 'font-size': 9, 'font-weight': 'bold' });
  cornerTag.textContent = 'CORNER PIVOT (0, 0)';
  s.append(cornerTag);

  // 3. Hidden Enemy Contact inside the Room
  const enemyRevealed = theta >= 20.0;
  const enemyBox = svgEl('rect', { x: targetX - 10, y: targetY - 10, width: 20, height: 20, fill: enemyRevealed ? '#f85149' : '#21262d', stroke: enemyRevealed ? '#fff' : '#484f58', 'stroke-width': enemyRevealed ? 2 : 1, rx: 4 });
  s.append(enemyBox);
  const enemyTxt = svgEl('text', { x: targetX, y: targetY + 4, fill: '#fff', 'font-size': 9, 'font-weight': 'bold', 'text-anchor': 'middle' });
  enemyTxt.textContent = 'T1';
  s.append(enemyTxt);

  const enemyStatus = svgEl('text', { x: targetX + 15, y: targetY + 4, fill: enemyRevealed ? '#f85149' : '#8fa1b4', 'font-size': 9, 'font-weight': 'bold' });
  enemyStatus.textContent = enemyRevealed ? 'EXPOSED IN SIGHTLINE!' : 'HIDDEN BY WALL';
  s.append(enemyStatus);

  // 4. Shaded Pie-Slice Wedge (Angular Exposure)
  const farDist = 320;
  const angRad = -theta * Math.PI / 180;
  const ray2X = px2 + Math.cos(angRad) * farDist;
  const ray2Y = py2 + Math.sin(angRad) * farDist;

  const pieWedge = svgEl('path', {
    d: `M ${cornerX} ${cornerY} L ${px1} ${py1} L ${px2} ${py2} L ${ray2X} ${ray2Y} Z`,
    fill: 'rgba(210, 153, 34, 0.12)',
    stroke: 'none'
  });
  s.append(pieWedge);

  // 5. Initial Sightline 1 (Grazing Baseline from px1)
  s.append(svgEl('line', { x1: px1, y1: py1, x2: cornerX, y2: cornerY, stroke: '#58a6ff', 'stroke-width': 2.5 }));
  s.append(svgEl('line', { x1: cornerX, y1: cornerY, x2: cornerX + 180, y2: cornerY, stroke: 'rgba(88, 166, 255, 0.35)', 'stroke-dasharray': '3,3', 'stroke-width': 1.5 }));

  // 6. Stepped Sightline 2 (Penetrating Sightline from px2)
  s.append(svgEl('line', { x1: px2, y1: py2, x2: cornerX, y2: cornerY, stroke: '#3fb950', 'stroke-width': 2.5 }));
  s.append(svgEl('line', { x1: cornerX, y1: cornerY, x2: ray2X, y2: ray2Y, stroke: '#3fb950', 'stroke-width': 2, 'stroke-dasharray': '4,2' }));

  // 7. Stand-off Distance Dimension Line (d)
  const dimY = cornerY + 38;
  s.append(svgEl('line', { x1: px1, y1: dimY, x2: cornerX, y2: dimY, stroke: '#58a6ff', 'stroke-width': 1.5 }));
  s.append(svgEl('line', { x1: px1, y1: dimY - 4, x2: px1, y2: dimY + 4, stroke: '#58a6ff', 'stroke-width': 1.5 }));
  s.append(svgEl('line', { x1: cornerX, y1: dimY - 4, x2: cornerX, y2: dimY + 4, stroke: '#58a6ff', 'stroke-width': 1.5 }));
  const dLabel = svgEl('text', { x: (px1 + cornerX) / 2, y: dimY + 12, fill: '#58a6ff', 'font-size': 9.5, 'font-weight': 'bold', 'text-anchor': 'middle' });
  dLabel.textContent = `Stand-off Distance d = ${d.toFixed(2)}m`;
  s.append(dLabel);

  // 8. Lateral Step Dimension Line (Δx)
  const dimX = px1 - 18;
  s.append(svgEl('line', { x1: dimX, y1: py1, x2: dimX, y2: py2, stroke: '#3fb950', 'stroke-width': 1.5 }));
  s.append(svgEl('line', { x1: dimX - 4, y1: py1, x2: dimX + 4, y2: py1, stroke: '#3fb950', 'stroke-width': 1.5 }));
  s.append(svgEl('line', { x1: dimX - 4, y1: py2, x2: dimX + 4, y2: py2, stroke: '#3fb950', 'stroke-width': 1.5 }));
  const dxLabel = svgEl('text', { x: dimX - 6, y: (py1 + py2) / 2 + 3, fill: '#3fb950', 'font-size': 9.5, 'font-weight': 'bold', 'text-anchor': 'end' });
  dxLabel.textContent = `Δx = ${dx.toFixed(2)}m`;
  s.append(dxLabel);

  // 9. Lateral step link (Dashed line between player 1 and 2)
  s.append(svgEl('line', { x1: px1, y1: py1, x2: px2, y2: py2, stroke: 'rgba(255, 255, 255, 0.4)', 'stroke-dasharray': '3,3', 'stroke-width': 1.5 }));

  // 10. Player Position Markers
  // Position 1 (Initial)
  s.append(svgEl('circle', { cx: px1, cy: py1, r: 8, fill: '#58a6ff', stroke: '#fff', 'stroke-width': 2 }));
  const p1Tag = svgEl('text', { x: px1, y: py1 + 18, fill: '#58a6ff', 'font-size': 8.5, 'font-weight': 'bold', 'text-anchor': 'middle' });
  p1Tag.textContent = 'P1';
  s.append(p1Tag);

  // Position 2 (Stepped)
  s.append(svgEl('circle', { cx: px2, cy: py2, r: 8, fill: '#3fb950', stroke: '#fff', 'stroke-width': 2 }));
  const p2Tag = svgEl('text', { x: px2, y: py2 - 12, fill: '#3fb950', 'font-size': 8.5, 'font-weight': 'bold', 'text-anchor': 'middle' });
  p2Tag.textContent = 'P2 (Stepped)';
  s.append(p2Tag);

  // 11. Angular Slice Arc (Δθ at Corner Pivot)
  const arcR = 45;
  const a1 = 0.0;
  const a2 = angRad;
  s.append(svgEl('path', {
    d: `M ${cornerX - arcR} ${cornerY} A ${arcR} ${arcR} 0 0 1 ${cornerX + Math.cos(Math.PI - a2) * arcR} ${cornerY - Math.sin(Math.PI - a2) * arcR}`,
    fill: 'none',
    stroke: '#d29922',
    'stroke-width': 2.5
  }));

  const arcBadge = svgEl('text', { x: cornerX - arcR - 25, y: cornerY - 14, fill: '#d29922', 'font-size': 11, 'font-weight': 'bold' });
  arcBadge.textContent = `Δθ = ${theta.toFixed(1)}°`;
  s.append(arcBadge);

  // 12. Top Title HUD inside SVG
  const hudTitle = svgEl('text', { x: 20, y: 30, fill: '#edf3f8', 'font-size': 14, 'font-weight': 800 });
  hudTitle.textContent = `New Angular Slice: ${theta.toFixed(1)}°`;
  s.append(hudTitle);

  const hudSubtitle = svgEl('text', { x: 20, y: 48, fill: d >= 1.5 ? '#3fb950' : (d <= 0.8 ? '#f85149' : '#d29922'), 'font-size': 10.5, 'font-weight': 'bold' });
  hudSubtitle.textContent = d >= 1.5
    ? '✓ LARGE STAND-OFF: Tight angular slice (Safe, precise pie-slicing)'
    : (d <= 0.8 ? '✗ HUGGING CORNER: Massive angular flash (High risk / over-peek)' : 'MODERATE STAND-OFF: Balanced angle exposure');
  s.append(hudSubtitle);
}

function renderCrosshair(){
  const a=+$('crosshair-slider').value,left=-70,right=60;
  $('crosshair-val').textContent=`${a>0?'+':''}${a}°`;
  $('left-cost').textContent=`${(Math.abs(left-a)/DEG_PER_TIC).toFixed(1)} tics`;
  $('right-cost').textContent=`${(Math.abs(right-a)/DEG_PER_TIC).toFixed(1)} tics`;
  const s=$('crosshair-svg');s.innerHTML='';const cx=260,cy=175,r=125;
  s.append(svgEl('path',{d:`M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${cx+r} ${cy}`,fill:'none',stroke:'#33465d','stroke-width':3}));
  [[left,'T1','#f85149'],[right,'T2','#f85149'],[a,'CROSSHAIR','#58a6ff']].forEach(([deg,label,color])=>{const rad=(90+deg)*Math.PI/180;const x=cx-r*Math.cos(rad),y=cy-r*Math.sin(rad);s.append(svgEl('circle',{cx:x,cy:y,r:label==='CROSSHAIR'?10:8,fill:color,stroke:'#fff'}));const t=svgEl('text',{x:x,y:y-15,fill:color,'text-anchor':'middle','font-size':11,'font-weight':700});t.textContent=label;s.append(t)});
  const t=svgEl('text',{x:260,y:218,fill:'#8fa1b4','text-anchor':'middle','font-size':12});t.textContent='Setup cost = angular correction ÷ aim speed';s.append(t);
}

function renderReveal(){
  const p=+$('reveal-slider').value/100;const s=$('reveal-svg');s.innerHTML='';
  const x=35+p*430,y=190,wallX=245,tx=405,ty=75,revealX=205;
  s.append(svgEl('rect',{x:wallX,y:15,width:28,height:150,fill:'#253244',stroke:'#59708c'}));
  s.append(svgEl('line',{x1:35,y1:y,x2:475,y2:y,stroke:'#33465d','stroke-dasharray':'5,4'}));
  s.append(svgEl('circle',{cx:x,cy:y,r:9,fill:'#58a6ff',stroke:'#fff','stroke-width':2}));
  s.append(svgEl('rect',{x:tx-9,y:ty-9,width:18,height:18,rx:3,fill:x>=revealX?'#f85149':'#202b38',stroke:x>=revealX?'#fff':'#4b5b6c'}));
  s.append(svgEl('line',{x1:wallX,y1:165,x2:tx,y2:ty,stroke:'#8fa1b4','stroke-dasharray':'4,4'}));
  if(x>=revealX)s.append(svgEl('line',{x1:x,y1:y,x2:tx,y2:ty,stroke:'#f85149','stroke-width':2}));
  s.append(svgEl('line',{x1:revealX,y1:175,x2:revealX,y2:205,stroke:'#d29922','stroke-width':3}));
  const label=svgEl('text',{x:revealX,y:224,fill:'#d29922','text-anchor':'middle','font-size':11,'font-weight':700});label.textContent='rⱼ: sightline opens';s.append(label);
  $('reveal-status').textContent=x<revealX?'Threat hidden':'Released: deadline clock running';
}

// Teaching fixture: T2 is urgent and near center, T3 follows on the right, T1 is a later left-side deadline.
// This is intentionally illustrative rather than a frozen research fixture; its role is to let the viewer discover order dependence.
const orderJobs={T1:{angle:-55,deadline:50},T2:{angle:5,deadline:16},T3:{angle:65,deadline:30}};
let selected=[];
function evalOrder(order){let cur=0,angle=0,maxLate=-999;order.forEach(id=>{const j=orderJobs[id];cur+=Math.ceil(Math.abs(j.angle-angle)/DEG_PER_TIC)+6+4;maxLate=Math.max(maxLate,cur-j.deadline);angle=j.angle});return maxLate}
function refreshOrder(){
  $('order-current').textContent=selected.length?selected.join(' → '):'—';
  document.querySelectorAll('#order-buttons button').forEach(b=>b.classList.toggle('selected',selected.includes(b.dataset.id)));
  if(selected.length===3){const l=evalOrder(selected);$('order-lateness').textContent=`${l>=0?'+':''}${l} tics · ${l<=0?'CLEARABLE':'UNSERVICEABLE'}`}else $('order-lateness').textContent='—';
}
function initOrder(){const wrap=$('order-buttons');['T1','T2','T3'].forEach(id=>{const b=document.createElement('button');b.textContent=id;b.dataset.id=id;b.onclick=()=>{if(!selected.includes(id)){selected.push(id);refreshOrder()}};wrap.appendChild(b)});$('order-reset').onclick=()=>{selected=[];refreshOrder()};$('order-best').onclick=()=>{const perms=[['T1','T2','T3'],['T1','T3','T2'],['T2','T1','T3'],['T2','T3','T1'],['T3','T1','T2'],['T3','T2','T1']];selected=perms.sort((a,b)=>evalOrder(a)-evalOrder(b))[0];refreshOrder()};refreshOrder()}

$('distance-slider').addEventListener('input',renderAngleLab);$('slice-slider').addEventListener('input',renderAngleLab);$('crosshair-slider').addEventListener('input',renderCrosshair);$('reveal-slider').addEventListener('input',renderReveal);
renderAngleLab();renderCrosshair();renderReveal();initOrder();
