import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface Point3D {
  x: number;
  y: number;
  z: number;
  baseSize: number;
  colorType: "core" | "grid" | "ring" | "beacon";
  pulseOffset: number;
}

export interface PlanetBackgroundProps {
  className?: string;
  opacity?: number;
  blur?: number;
}

export function PlanetBackground({
  className,
  opacity = 0.46,
  blur = 3.5,
}: PlanetBackgroundProps = {}) {
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
      bgGrad.addColorStop(0, "#15171C");
      bgGrad.addColorStop(0.55, "#0D0F14");
      bgGrad.addColorStop(1, "#08090C");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Draw faint background stars
      for (const star of stars) {
        star.a += Math.sin(currentTime * 0.002 + star.x * 100) * 0.003;
        ctx.fillStyle = `rgba(245, 247, 242, ${Math.max(0.1, Math.min(0.6, star.a))})`;
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
      glowGrad.addColorStop(0, "rgba(184, 244, 90, 0.22)");
      glowGrad.addColorStop(0.45, "rgba(200, 255, 101, 0.10)");
      glowGrad.addColorStop(0.75, "rgba(73, 107, 36, 0.04)");
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

      // Project and render all 3D points
      interface ProjectedPoint {
        screenX: number;
        screenY: number;
        z: number;
        size: number;
        opacity: number;
        color: string;
        isBeacon: boolean;
        pulse: number;
      }
      const renderList: ProjectedPoint[] = [];

      for (const pt of points) {
        // 1. Rotation around Y axis
        const x1 = pt.x * cosY + pt.z * sinY;
        const y1 = pt.y;
        const z1 = -pt.x * sinY + pt.z * cosY;

        // 2. Axial tilt around Z axis
        const x2 = x1 * cosZ - y1 * sinZ;
        const y2 = x1 * sinZ + y1 * cosZ;
        const z2 = z1;

        // 3. Camera pitch around X axis
        const x3 = x2;
        const y3 = y2 * cosX - z2 * sinX;
        const z3 = y2 * sinX + z2 * cosX;

        // Perspective projection
        const persp = 1 / (1 - z3 * 0.25);
        const screenX = centerX + x3 * radius * persp;
        const screenY = centerY + y3 * radius * persp;

        // Depth shading & visibility (front vs back)
        const isFront = z3 > -0.15;
        const depthNormalized = (z3 + 1) / 2; // 0 to 1
        const opacity = isFront
          ? Math.pow(depthNormalized, 1.2) * 0.95 + 0.15
          : Math.pow(Math.max(0, depthNormalized), 2.5) * 0.15;

        // Pulse animation for beacons
        const pulse = Math.sin(currentTime * 0.003 + pt.pulseOffset) * 0.5 + 0.5;

        // Color & sizing
        let color = "#B8F45A";
        let size = pt.baseSize;

        if (pt.colorType === "beacon") {
          color = "#C8FF65";
          size = (pt.baseSize + pulse * 1.5) * persp;
        } else if (pt.colorType === "grid") {
          color = isFront ? "#B8F45A" : "#496B24";
          size = pt.baseSize * persp;
        } else if (pt.colorType === "ring") {
          color = isFront ? "#F5F7F2" : "#666A66";
          size = pt.baseSize * persp;
        } else {
          // Core sphere dots
          color = isFront
            ? depthNormalized > 0.7
              ? "#F5F7F2"
              : "#B8F45A"
            : "#1C1F24";
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
          ctx.shadowColor = "#B8F45A";
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(dot.screenX, dot.screenY, dot.size + 1, 0, Math.PI * 2);
          ctx.fill();

          // Outer beacon radar pulse ring
          ctx.strokeStyle = "rgba(184, 244, 90, 0.45)";
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
      rimGrad.addColorStop(0, "rgba(184, 244, 90, 0.18)");
      rimGrad.addColorStop(0.5, "rgba(184, 244, 90, 0.04)");
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
      axisGrad.addColorStop(0, "rgba(184, 244, 90, 0.45)");
      axisGrad.addColorStop(0.2, "rgba(184, 244, 90, 0.08)");
      axisGrad.addColorStop(0.8, "rgba(184, 244, 90, 0.08)");
      axisGrad.addColorStop(1, "rgba(184, 244, 90, 0.35)");

      ctx.strokeStyle = axisGrad;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(topPoleX, topPoleY);
      ctx.lineTo(btmPoleX, btmPoleY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Pole beacon tops
      ctx.fillStyle = "#B8F45A";
      ctx.shadowColor = "#B8F45A";
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
      className={cn(
        "fixed inset-0 pointer-events-none -z-10 overflow-hidden select-none bg-[#08090C]",
        className
      )}
    >
      <div
        className="w-full h-full transform-gpu scale-105 will-change-transform"
        style={{
          opacity,
          filter: `blur(${blur}px)`,
          WebkitFilter: `blur(${blur}px)`,
        }}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />
      </div>
      {/* Soft atmospheric ambient glow overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_20%,rgba(184,244,90,0.06)_0%,transparent_75%)] pointer-events-none" />
      {/* Soft bottom edge fade for footer */}
      <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#08090C] via-[#08090C]/80 to-transparent pointer-events-none" />
    </div>
  );
}
