/**
 * JOCKY Manager — Three.js 3D Network Topology Background
 * Fixed canvas, z-index: -1, pointer-events: none
 * Renders a particle network defense grid with mouse parallax
 * Optimized: low geometry count, single RAF loop, GPU-only transforms
 */
(function () {
  'use strict';

  if (typeof THREE === 'undefined') return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;

  // ── Renderer ──────────────────────────────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x000000, 0);

  // ── Scene & Camera ────────────────────────────────────────────────────────
  const scene  = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 90;

  // ── Particle Node Config ──────────────────────────────────────────────────
  const NODE_COUNT = 180;
  const SPREAD     = 120;
  const LINK_DIST  = 26;
  const MAX_LINKS  = NODE_COUNT * 4;

  // Positions + velocities
  const positions  = new Float32Array(NODE_COUNT * 3);
  const velocities = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    positions[i * 3]     = (Math.random() - 0.5) * SPREAD;
    positions[i * 3 + 1] = (Math.random() - 0.5) * SPREAD;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 30;
    velocities.push(
      (Math.random() - 0.5) * 0.028,
      (Math.random() - 0.5) * 0.018,
      0
    );
  }

  // Node points
  const nodeGeo = new THREE.BufferGeometry();
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const nodeMat = new THREE.PointsMaterial({
    color: 0x06b6d4,
    size: 0.9,
    transparent: true,
    opacity: 0.65,
    depthWrite: false,
  });
  scene.add(new THREE.Points(nodeGeo, nodeMat));

  // Connection lines
  const linkPositions = new Float32Array(MAX_LINKS * 6);
  const linkColors    = new Float32Array(MAX_LINKS * 6);
  const linkGeo       = new THREE.BufferGeometry();
  linkGeo.setAttribute('position', new THREE.BufferAttribute(linkPositions, 3));
  linkGeo.setAttribute('color',    new THREE.BufferAttribute(linkColors,    3));
  const linkMat = new THREE.LineBasicMaterial({
    vertexColors: true,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
  });
  scene.add(new THREE.LineSegments(linkGeo, linkMat));

  // Accent ring (rotating hexagonal node indicator)
  const ringGeo = new THREE.RingGeometry(8, 8.3, 48);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x10b981,
    transparent: true,
    opacity: 0.08,
    side: THREE.DoubleSide,
  });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  scene.add(ring);

  // ── Mouse Parallax ────────────────────────────────────────────────────────
  let mouseX = 0, mouseY = 0;
  let targetRotX = 0, targetRotY = 0;

  document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth  - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  // ── Resize ────────────────────────────────────────────────────────────────
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // ── Animation Loop ────────────────────────────────────────────────────────
  const cyanColor    = new THREE.Color(0x06b6d4);
  const emeraldColor = new THREE.Color(0x10b981);

  let frameId = null;
  function animate() {
    frameId = requestAnimationFrame(animate);

    // Move nodes
    for (let i = 0; i < NODE_COUNT; i++) {
      positions[i * 3]     += velocities[i * 3];
      positions[i * 3 + 1] += velocities[i * 3 + 1];
      // Wrap edges
      if (positions[i * 3]     >  SPREAD / 2) positions[i * 3]     = -SPREAD / 2;
      if (positions[i * 3]     < -SPREAD / 2) positions[i * 3]     =  SPREAD / 2;
      if (positions[i * 3 + 1] >  SPREAD / 2) positions[i * 3 + 1] = -SPREAD / 2;
      if (positions[i * 3 + 1] < -SPREAD / 2) positions[i * 3 + 1] =  SPREAD / 2;
    }
    nodeGeo.attributes.position.needsUpdate = true;

    // Draw links
    let li = 0;
    for (let i = 0; i < NODE_COUNT && li < MAX_LINKS - 1; i++) {
      for (let j = i + 1; j < NODE_COUNT && li < MAX_LINKS - 1; j++) {
        const dx = positions[i * 3]     - positions[j * 3];
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < LINK_DIST) {
          const alpha = 1 - dist / LINK_DIST;
          const col = li % 3 === 0 ? emeraldColor : cyanColor;
          linkPositions[li * 6]     = positions[i * 3];
          linkPositions[li * 6 + 1] = positions[i * 3 + 1];
          linkPositions[li * 6 + 2] = positions[i * 3 + 2];
          linkPositions[li * 6 + 3] = positions[j * 3];
          linkPositions[li * 6 + 4] = positions[j * 3 + 1];
          linkPositions[li * 6 + 5] = positions[j * 3 + 2];
          linkColors[li * 6]     = col.r * alpha;
          linkColors[li * 6 + 1] = col.g * alpha;
          linkColors[li * 6 + 2] = col.b * alpha;
          linkColors[li * 6 + 3] = col.r * alpha;
          linkColors[li * 6 + 4] = col.g * alpha;
          linkColors[li * 6 + 5] = col.b * alpha;
          li++;
        }
      }
    }
    // Zero out unused slots
    for (let k = li; k < MAX_LINKS; k++) {
      for (let d = 0; d < 6; d++) { linkPositions[k * 6 + d] = 0; linkColors[k * 6 + d] = 0; }
    }
    linkGeo.setDrawRange(0, li * 2);
    linkGeo.attributes.position.needsUpdate = true;
    linkGeo.attributes.color.needsUpdate    = true;

    // Mouse parallax (smooth damp)
    targetRotY += (mouseX * 0.04 - targetRotY) * 0.03;
    targetRotX += (-mouseY * 0.025 - targetRotX) * 0.03;
    scene.rotation.y = targetRotY;
    scene.rotation.x = targetRotX;

    // Rotate accent ring
    ring.rotation.z += 0.002;

    renderer.render(scene, camera);
  }

  animate();

  // Pause when tab is hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(frameId);
    } else {
      animate();
    }
  });
})();
