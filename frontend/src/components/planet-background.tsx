import { useEffect, useRef } from "react";

interface Point3D {
  x: number;
  y: number;
  z: number;
  baseSize: number;
  colorType: "core" | "grid" | "ring" | "beacon";
  pulseOffset: number;
}

export function PlanetBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId = 0;
    let width = 0;
    let height = 0;
    let dpr = window.devicePixelRatio || 1;

    // Rotation angles
    let rotationY = 0;
    const axialTiltZ = -23.5 * (Math.PI / 180); // Earth-like 23.5 degree axial tilt
    const pitchX = 16 * (Math.PI / 180); // Camera elevation pitch

    // Mouse parallax
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    // Build 3D points
    const points: Point3D[] = [];

    // 1. Fibonacci Sphere Dots (Organic uniform distribution)
    const numSphereDots = 1400;
    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    for (let i = 0; i < numSphereDots; i++) {
      const theta = (2 * Math.PI * i) / goldenRatio;
      const phi = Math.acos(1 - (2 * (i + 0.5)) / numSphereDots);
      const x = Math.sin(phi) * Math.cos(theta);
      const y = Math.cos(phi);
      const z = Math.sin(phi) * Math.sin(theta);

      points.push({
        x,
        y,
        z,
        baseSize: Math.random() * 1.2 + 1.2,
        colorType: "core",
        pulseOffset: Math.random() * Math.PI * 2,
      });
    }

    // 2. Latitude Ring Dots (Planetary parallel grid lines)
    const latitudes = [-65, -45, -25, 0, 25, 45, 65];
    latitudes.forEach((lat) => {
      const latRad = (lat * Math.PI) / 180;
      const y = Math.sin(latRad);
      const r = Math.cos(latRad);
      const dotsOnRing = Math.floor(65 * r);
      for (let j = 0; j < dotsOnRing; j++) {
        const angle = (j / dotsOnRing) * Math.PI * 2;
        points.push({
          x: r * Math.cos(angle),
          y,
          z: r * Math.sin(angle),
          baseSize: lat === 0 ? 2.0 : 1.4, // Equator is slightly more defined
          colorType: "grid",
          pulseOffset: angle * 2,
        });
      }
    });

    // 3. Outer Planetary Ring Dots (Saturn-like orbital dust disk)
    const ringDots = 420;
    for (let k = 0; k < ringDots; k++) {
      const angle = (k / ringDots) * Math.PI * 2 + (Math.random() - 0.5) * 0.05;
      const ringRadius = 1.38 + Math.random() * 0.48; // between 1.38 and 1.86 sphere radii
      const yOffset = (Math.random() - 0.5) * 0.04;
      points.push({
        x: ringRadius * Math.cos(angle),
        y: yOffset,
        z: ringRadius * Math.sin(angle),
        baseSize: Math.random() * 1.4 + 0.8,
        colorType: "ring",
        pulseOffset: k * 0.1,
      });
    }

    // 4. Special Beacon Nodes (Glowing surveillance telemetry points)
    for (let b = 0; b < 12; b++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      points.push({
        x: Math.sin(phi) * Math.cos(theta),
        y: Math.cos(phi),
        z: Math.sin(phi) * Math.sin(theta),
        baseSize: 3.2,
        colorType: "beacon",
        pulseOffset: b * 1.5,
      });
    }

    // Distant background star particles
    const stars: { x: number; y: number; s: number; a: number; speed: number }[] = [];
    for (let s = 0; s < 70; s++) {
      stars.push({
        x: Math.random(),
        y: Math.random(),
        s: Math.random() * 1.5 + 0.5,
        a: Math.random() * 0.5 + 0.2,
        speed: Math.random() * 0.0002 + 0.0001,
      });
    }

    function handleResize() {
      if (!canvas) return;
      width = window.innerWidth;
      height = window.innerHeight;
      dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    }

    function handleMouseMove(e: MouseEvent) {
      targetMouseX = (e.clientX / window.innerWidth - 0.5) * 0.3;
      targetMouseY = (e.clientY / window.innerHeight - 0.5) * 0.3;
    }

    handleResize();
    window.addEventListener("resize", handleResize);
    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    let lastTime = performance.now();

    function render(currentTime: number) {
      if (!canvas || !ctx) return;
      const dt = Math.min((currentTime - lastTime) / 1000, 0.1);
      lastTime = currentTime;

      // Mouse smoothing
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Continuous planetary axial rotation
      rotationY += dt * 0.22; // ~0.22 rad/sec smooth spin

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      // Deep space background gradient
      const bgGrad = ctx.createRadialGradient(
        width * 0.5,
        height * 0.4,
        0,
        width * 0.5,
        height * 0.5,
        Math.max(width, height)
      );
      bgGrad.addColorStop(0, "#080c14");
      bgGrad.addColorStop(0.6, "#05070c");
      bgGrad.addColorStop(1, "#030408");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Draw faint background stars
      for (const star of stars) {
        star.a += Math.sin(currentTime * 0.002 + star.x * 100) * 0.003;
        ctx.fillStyle = `rgba(180, 210, 255, ${Math.max(0.1, Math.min(0.6, star.a))})`;
        ctx.beginPath();
        ctx.arc(star.x * width, star.y * height, star.s, 0, Math.PI * 2);
        ctx.fill();
      }

      // Responsive planet center & radius
      const isWide = width >= 1024;
      const centerX = isWide ? width * 0.66 : width * 0.5;
      const centerY = isWide ? height * 0.52 : height * 0.48;
      const radius = Math.min(width, height) * (isWide ? 0.36 : 0.32);

      // Planet Atmospheric Backlight Glow
      const glowGrad = ctx.createRadialGradient(
        centerX,
        centerY,
        radius * 0.4,
        centerX,
        centerY,
        radius * 1.55
      );
      glowGrad.addColorStop(0, "rgba(59, 156, 255, 0.16)");
      glowGrad.addColorStop(0.45, "rgba(0, 229, 255, 0.07)");
      glowGrad.addColorStop(0.75, "rgba(14, 165, 233, 0.02)");
      glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius * 1.55, 0, Math.PI * 2);
      ctx.fill();

      // Rotation & tilt matrix precomputations
      const cosY = Math.cos(rotationY);
      const sinY = Math.sin(rotationY);

      const tiltZ = axialTiltZ + mouseX * 0.2;
      const cosZ = Math.cos(tiltZ);
      const sinZ = Math.sin(tiltZ);

      const tiltX = pitchX + mouseY * 0.2;
      const cosX = Math.cos(tiltX);
      const sinX = Math.sin(tiltX);

      // Camera focal distance
      const fov = 2.4;

      // Project & collect dots
      interface RenderDot {
        screenX: number;
        screenY: number;
        z: number;
        size: number;
        opacity: number;
        color: string;
        isBeacon: boolean;
        pulse: number;
      }

      const renderList: RenderDot[] = [];

      for (const pt of points) {

        // 1. Rotate around planet Y-axis (spin)
        const x1 = pt.x * cosY + pt.z * sinY;
        const y1 = pt.y;
        const z1 = -pt.x * sinY + pt.z * cosY;

        // 2. Axial Tilt around Z-axis
        const x2 = x1 * cosZ - y1 * sinZ;
        const y2 = x1 * sinZ + y1 * cosZ;
        const z2 = z1;

        // 3. Viewing Pitch around X-axis
        const x3 = x2;
        const y3 = y2 * cosX - z2 * sinX;
        const z3 = y2 * sinX + z2 * cosX;

        // 4. Perspective projection
        const persp = fov / (fov - z3 * 0.5);
        const screenX = centerX + x3 * radius * persp;
        const screenY = centerY + y3 * radius * persp;

        // Depth & visibility
        const isFront = z3 > -0.05;
        const depthNormalized = (z3 + 1.2) / 2.4; // 0 (far back) to 1 (front)

        // Pulse time for beacons and subtle breathing
        const pulse = Math.sin(currentTime * 0.003 + pt.pulseOffset);

        let size = pt.baseSize * persp;
        let opacity = 0;
        let color = "";

        if (pt.colorType === "beacon") {
          opacity = isFront ? 0.95 + pulse * 0.05 : 0.2;
          size = (pt.baseSize + pulse * 1.0) * persp;
          color = "#00E5FF";
        } else if (pt.colorType === "ring") {
          opacity = Math.max(0.1, Math.min(0.85, depthNormalized * 0.75 + 0.1));
          color = isFront ? "#7DD3FC" : "#38BDF8";
          size = pt.baseSize * persp * 0.9;
        } else if (pt.colorType === "grid") {
          opacity = isFront
            ? 0.55 + depthNormalized * 0.4
            : 0.12 + Math.max(0, depthNormalized) * 0.15;
          color = isFront ? "#38BDF8" : "#1E3A8A";
          size = pt.baseSize * persp;
        } else {
          // Core Fibonacci dots
          opacity = isFront
            ? 0.45 + depthNormalized * 0.55
            : 0.1 + Math.max(0, depthNormalized) * 0.18;
          color = isFront
            ? depthNormalized > 0.7
              ? "#FFFFFF"
              : "#60A5FA"
            : "#1E293B";
          size = pt.baseSize * persp;
        }

        renderList.push({
          screenX,
          screenY,
          z: z3,
          size: Math.max(0.5, size),
          opacity: Math.max(0.05, Math.min(1, opacity)),
          color,
          isBeacon: pt.colorType === "beacon",
          pulse,
        });
      }

      // Sort by Z for realistic depth layering
      renderList.sort((a, b) => a.z - b.z);

      // Draw all projected dots
      for (const dot of renderList) {
        ctx.globalAlpha = dot.opacity;
        ctx.fillStyle = dot.color;

        if (dot.isBeacon && dot.z > 0) {
          // Glowing beacon halo
          ctx.shadowColor = "#00E5FF";
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(dot.screenX, dot.screenY, dot.size + 1, 0, Math.PI * 2);
          ctx.fill();

          // Outer beacon radar pulse ring
          ctx.strokeStyle = "rgba(0, 229, 255, 0.45)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(dot.screenX, dot.screenY, dot.size * 2.8, 0, Math.PI * 2);
          ctx.stroke();
          ctx.shadowBlur = 0;
        } else {
          ctx.beginPath();
          ctx.arc(dot.screenX, dot.screenY, dot.size, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.globalAlpha = 1;

      // Subtle atmospheric edge rim light (crescent limb glow)
      const rimGrad = ctx.createLinearGradient(
        centerX - radius,
        centerY - radius,
        centerX + radius,
        centerY + radius
      );
      rimGrad.addColorStop(0, "rgba(59, 156, 255, 0.18)");
      rimGrad.addColorStop(0.5, "rgba(59, 156, 255, 0.04)");
      rimGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.strokeStyle = rimGrad;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius + 1, 0, Math.PI * 2);
      ctx.stroke();

      // Axis pole indicator lines (tilted rotating axis)
      const poleLen = radius * 1.25;
      const topPoleX = centerX - Math.sin(tiltZ) * poleLen;
      const topPoleY = centerY - Math.cos(tiltZ) * poleLen;
      const btmPoleX = centerX + Math.sin(tiltZ) * poleLen;
      const btmPoleY = centerY + Math.cos(tiltZ) * poleLen;

      const axisGrad = ctx.createLinearGradient(topPoleX, topPoleY, btmPoleX, btmPoleY);
      axisGrad.addColorStop(0, "rgba(0, 229, 255, 0.45)");
      axisGrad.addColorStop(0.2, "rgba(0, 229, 255, 0.08)");
      axisGrad.addColorStop(0.8, "rgba(0, 229, 255, 0.08)");
      axisGrad.addColorStop(1, "rgba(0, 229, 255, 0.35)");

      ctx.strokeStyle = axisGrad;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(topPoleX, topPoleY);
      ctx.lineTo(btmPoleX, btmPoleY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Pole beacon tops
      ctx.fillStyle = "#00E5FF";
      ctx.shadowColor = "#00E5FF";
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(topPoleX, topPoleY, 2.5, 0, Math.PI * 2);
      ctx.arc(btmPoleX, btmPoleY, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.restore();

      animId = requestAnimationFrame(render);
    }

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden select-none"
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
      {/* Soft bottom edge fade for footer */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#030408]/80 to-transparent pointer-events-none" />
    </div>
  );
}
