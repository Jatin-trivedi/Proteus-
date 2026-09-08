import { useEffect, useRef } from "react";

const ORBIT_LABELS = [
  { label: "Polymorphic Engine", angle: 0 },
  { label: "Kernel Analysis", angle: 90 },
  { label: "CI/CD Obfuscation", angle: 180 },
  { label: "Stealth Execution", angle: 270 },
];

let _cachedImg: HTMLImageElement | null = null;

export function RotatingOrb() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const rotYRef = useRef(0);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let dpr = window.devicePixelRatio || 1;

    function resize() {
      if (!canvas) return;
      dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    if (!_cachedImg) {
      const img = new Image();
      img.src = "/proteus-logo-transparent.png";
      _cachedImg = img;
    }

    function draw(t: number) {
      if (!canvas || !ctx) return;
      const W = canvas.width / dpr;
      const H = canvas.height / dpr;
      const cx = W / 2;
      const cy = H / 2;
      // ── BIGGER: increased from 0.40 → 0.46 ──
      const R = Math.min(W, H) * 0.46;
      const rx = 14 * (Math.PI / 180);

      ctx.clearRect(0, 0, W, H);
      timeRef.current = t * 0.001;
      rotYRef.current += 0.45;
      const ry = (rotYRef.current * Math.PI) / 180;

      // ── Ambient glow halo ────────────────────────────────────────────
      const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 2);
      glow.addColorStop(0, "rgba(6,182,212,0.13)");
      glow.addColorStop(0.5, "rgba(6,182,212,0.06)");
      glow.addColorStop(1, "rgba(6,182,212,0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.ellipse(cx, cy, R * 2, R * 2, 0, 0, Math.PI * 2);
      ctx.fill();

      // ── Tilted orbit ring ────────────────────────────────────────────
      ctx.save();
      ctx.strokeStyle = "rgba(255,255,255,0.18)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(cx, cy, R, R * Math.cos(rx), 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // ── Trailing arc + glowing dot ───────────────────────────────────
      const dotAngle = ry;
      const dotX = cx + R * Math.cos(dotAngle);
      const dotY = cy + R * Math.sin(dotAngle) * Math.cos(rx);

      ctx.save();
      ctx.strokeStyle = "rgba(255,255,255,0.6)";
      ctx.lineWidth = 1.5;
      const arcLen = 0.75;
      ctx.beginPath();
      let first = true;
      for (let a = dotAngle - arcLen; a <= dotAngle; a += 0.015) {
        const px = cx + R * Math.cos(a);
        const py = cy + R * Math.sin(a) * Math.cos(rx);
        if (first) { ctx.moveTo(px, py); first = false; }
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
      ctx.restore();

      // dot glow
      const dg = ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, 8);
      dg.addColorStop(0, "rgba(255,255,255,1)");
      dg.addColorStop(0.4, "rgba(6,182,212,0.9)");
      dg.addColorStop(1, "rgba(6,182,212,0)");
      ctx.fillStyle = dg;
      ctx.beginPath();
      ctx.arc(dotX, dotY, 8, 0, Math.PI * 2);
      ctx.fill();

      // ── Glassmorphism disc ───────────────────────────────────────────
      const logoR = R * 0.74;
      const glasGrad = ctx.createRadialGradient(
        cx - logoR * 0.25, cy - logoR * 0.25, 0,
        cx, cy, logoR
      );
      glasGrad.addColorStop(0, "rgba(255,255,255,0.08)");
      glasGrad.addColorStop(0.5, "rgba(6,182,212,0.04)");
      glasGrad.addColorStop(1, "rgba(0,0,0,0.3)");
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, logoR, 0, Math.PI * 2);
      ctx.fillStyle = glasGrad;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.13)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();

      // ── 3-D perspective-warped logo ──────────────────────────────────
      const scaleX = Math.cos(ry);
      const skewY = Math.sin(ry) * Math.sin(rx);
      const imgSize = logoR * 1.35;

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, logoR - 2, 0, Math.PI * 2);
      ctx.clip();
      ctx.translate(cx, cy);
      ctx.transform(scaleX, -skewY, 0, 1, 0, 0);

      if (_cachedImg && _cachedImg.complete && _cachedImg.naturalWidth > 0) {
        ctx.drawImage(_cachedImg, -imgSize / 2, -imgSize / 2, imgSize, imgSize);

        const lightAngle = ((ry % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
        const isFront = lightAngle < Math.PI;
        const blend = isFront ? Math.sin(lightAngle) : 0;

        if (blend > 0.04) {
          ctx.globalCompositeOperation = "screen";
          ctx.globalAlpha = blend * 0.2;
          ctx.fillStyle = "#38bdf8";
          ctx.beginPath();
          ctx.arc(0, 0, imgSize / 2, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.globalCompositeOperation = "multiply";
          ctx.globalAlpha = 0.5;
          ctx.fillStyle = "#050a14";
          ctx.beginPath();
          ctx.arc(0, 0, imgSize / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 1;
      } else {
        // Fallback shield
        const sh = imgSize * 0.62;
        const sw = sh * 0.78;
        ctx.strokeStyle = "rgba(6,182,212,0.7)";
        ctx.lineWidth = 2.5;
        ctx.fillStyle = "rgba(6,182,212,0.1)";
        ctx.beginPath();
        ctx.moveTo(0, -sh / 2);
        ctx.lineTo(sw / 2, -sh * 0.15);
        ctx.lineTo(sw / 2, sh * 0.2);
        ctx.quadraticCurveTo(0, sh / 2, 0, sh / 2);
        ctx.quadraticCurveTo(-sw / 2, sh * 0.2, -sw / 2, sh * 0.2);
        ctx.lineTo(-sw / 2, -sh * 0.15);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
      ctx.restore();

      // ── Scanning sweep line ──────────────────────────────────────────
      const scanP = (Math.sin(timeRef.current * 0.9) + 1) / 2;
      const scanY = cy - logoR * 0.88 + scanP * logoR * 1.76;
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, logoR - 2, 0, Math.PI * 2);
      ctx.clip();
      const sg = ctx.createLinearGradient(cx - logoR, scanY, cx + logoR, scanY);
      sg.addColorStop(0, "rgba(6,182,212,0)");
      sg.addColorStop(0.5, "rgba(6,182,212,0.3)");
      sg.addColorStop(1, "rgba(6,182,212,0)");
      ctx.fillStyle = sg;
      ctx.fillRect(cx - logoR, scanY - 1.5, logoR * 2, 3);
      ctx.restore();

      // ── Orbiting labels with blur on inactive ones ───────────────────
      const fontSize = Math.max(12, Math.round(Math.min(W, H) * 0.034));

      // Compute z-depth for each label (sin value, -1 back → +1 front)
      const labelData = ORBIT_LABELS.map(({ label, angle: startAngle }) => {
        const a = ry + (startAngle * Math.PI) / 180;
        const zDepth = Math.sin(a); // -1 → +1
        const lx = cx + R * 1.22 * Math.cos(a);
        const ly = cy + R * 1.22 * Math.sin(a) * Math.cos(rx);
        return { label, a, zDepth, lx, ly };
      });

      // Find the index of the frontmost label
      const maxZ = Math.max(...labelData.map((d) => d.zDepth));
      const frontThreshold = 0.65; // how close to max to be "active"

      labelData.forEach(({ label, zDepth, lx, ly }) => {
        const isActive = zDepth >= maxZ - (1 - frontThreshold);
        // active label: full opacity, no blur, bright
        // inactive labels: blurred + faded
        const alpha = isActive ? 1 : 0.28 + ((zDepth + 1) / 2) * 0.18;
        const blurPx = isActive ? 0 : 5;

        ctx.save();
        ctx.font = `${isActive ? "600" : "400"} ${fontSize}px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.globalAlpha = alpha;

        if (blurPx > 0) {
          ctx.filter = `blur(${blurPx}px)`;
        }

        ctx.shadowColor = isActive ? "rgba(6,182,212,0.9)" : "rgba(6,182,212,0.2)";
        ctx.shadowBlur = isActive ? 18 : 4;
        ctx.fillStyle = isActive ? "#e2f8ff" : "#94a3b8";
        ctx.fillText(label, lx, ly);

        // Reset filter
        ctx.filter = "none";
        ctx.restore();
      });

      animRef.current = requestAnimationFrame(draw);
    }

    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      ro.disconnect();
    };
  }, []);

  return (
    <div className="relative w-full h-full flex items-center justify-center select-none">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 65% 55% at 50% 50%, rgba(6,182,212,0.09) 0%, transparent 70%)",
        }}
      />
      <canvas ref={canvasRef} className="w-full h-full" style={{ display: "block" }} />
    </div>
  );
}
