import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Bot,
  Wifi,
  Radio,
  AlertTriangle,
  Play,
  FilePlus2,
  BarChart3,
  Shield,
  ChevronRight,
  ArrowRight,
  Sparkles,
  Terminal,
  FileText,
  Binary,
  Activity,
  CheckCircle2,
  Lock,
  Zap,
  Layers,
  Cpu,
  Monitor,
  Globe,
} from "lucide-react";
import { AppLayout, StatusDot } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch, type Agent, type Deployment, type Result } from "@/lib/api";
import { useEffect, useState, useRef } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { ProteusIcon } from "@/components/proteus-logo";

import gsap from "gsap";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Proteus — Next-Gen Forensic & Compliance Intelligence" },
      {
        name: "description",
        content:
          "A proprietary programming language framework engineered to exceed detection boundaries — enabling deep forensic system analysis through polymorphic execution and CI/CD-driven obfuscation.",
      },
      { property: "og:title", content: "Proteus — Forensic Framework" },
      {
        property: "og:description",
        content: "Deep forensic system analysis through polymorphic execution.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState<string>();
  const [activeDeepDiveTab, setActiveDeepDiveTab] = useState<
    "ir" | "polymorphism" | "memory" | "byovd" | "network"
  >("ir");

  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const buttonsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load live telemetry from backend
    Promise.all([
      apiFetch<Agent[]>("/agent/list"),
      apiFetch<Deployment[]>("/script/deployments"),
      apiFetch<Result[]>("/result/list"),
    ])
      .then(([agentData, deploymentData, resultData]) => {
        setAgents(agentData);
        setDeployments(deploymentData);
        setResults(resultData);
      })
      .catch((err: Error) => setError(err.message));

    // Staggered Cybercrest-style entrance animation
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
      tl.fromTo(
        ".hero-badge",
        { opacity: 0, y: -20, scale: 0.95 },
        { opacity: 1, y: 0, scale: 1, duration: 0.8, delay: 0.1 }
      )
        .fromTo(
          titleRef.current,
          { opacity: 0, y: 30, letterSpacing: "0.05em" },
          { opacity: 1, y: 0, letterSpacing: "0.22em", duration: 1 },
          "-=0.5"
        )
        .fromTo(
          subtitleRef.current,
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, duration: 0.8 },
          "-=0.6"
        )
        .fromTo(
          buttonsRef.current,
          { opacity: 0, y: 25 },
          { opacity: 1, y: 0, duration: 0.8 },
          "-=0.5"
        );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  const activity = results
    .slice(0, 12)
    .reverse()
    .map((result, index) => ({
      h: new Date(result.submitted_at).toLocaleTimeString([], {
        hour: "2-digit",
        hour12: false,
      }),
      ops: deployments.filter(
        (deployment) => deployment.deployed_at <= result.submitted_at
      ).length,
      alerts: index + 1,
    }));

  const online = agents.filter((agent) => agent.status === "online").length;
  const active = deployments.filter((deployment) =>
    ["pending", "in_progress", "obfuscated"].includes(deployment.status)
  ).length;

  return (
    <AppLayout
      title=""
      subtitle=""
      actions={null}
      fullscreenBackground={
        <div className="fixed inset-0 w-screen h-screen -z-10 overflow-hidden pointer-events-none">
          <video
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            poster="/hero-poster.jpg"
            className="w-full h-full object-cover scale-105 opacity-40 brightness-95 contrast-125"
          >
            <source src="/hero-bg.mp4" type="video/mp4" />
          </video>
          {/* Subtle dark gradient overlays covering the entire display */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#0A0E1A]/65 via-[#0A0E1A]/75 to-[#0A0E1A]/90" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,156,255,0.14)_0%,transparent_75%)]" />
        </div>
      }
    >
      {/* ======================================================== */}
      {/* 1. HERO SECTION */}
      {/* ======================================================== */}
      <section
        ref={heroRef}
        className="relative -mt-10 md:-mt-14 pb-16 md:pb-24 pt-12 md:pt-20 flex flex-col items-center justify-center text-center overflow-hidden"
      >
        {/* Ambient background blobs */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] md:w-[900px] h-[350px] md:h-[450px] bg-primary/10 blur-[140px] pointer-events-none rounded-full" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[200px] bg-primary/15 blur-[120px] pointer-events-none rounded-full" />

        {/* Top Pill Tag */}
        <div className="hero-badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/30 text-xs md:text-sm font-mono tracking-widest text-primary shadow-[0_0_25px_rgba(59,156,255,0.25)] mb-8 md:mb-10 backdrop-blur-md">
          <span className="h-2 w-2 rounded-full bg-primary pulse-dot" />
          <span className="font-semibold uppercase text-primary">NEXT-GENERATION FORENSIC FRAMEWORK</span>
        </div>

        {/* Brand Title */}
        <h1
          ref={titleRef}
          className="text-6xl sm:text-8xl md:text-9xl lg:text-[9.5rem] font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-white/90 to-[#3B9CFF]/75 drop-shadow-[0_0_60px_rgba(59,156,255,0.45)] font-heading uppercase tracking-[0.22em] select-none leading-none mb-6 md:mb-8"
        >
          JOCKY
        </h1>

        {/* Subtitle / Tagline */}
        <p
          ref={subtitleRef}
          className="max-w-5xl text-base sm:text-lg md:text-xl leading-relaxed text-zinc-200/95 font-normal px-4 sm:px-8 mb-10 md:mb-12 font-sans tracking-wide"
        >
          A proprietary programming language framework engineered to exceed detection boundaries — enabling deep forensic system analysis through polymorphic execution, kernel-level subversion, and CI/CD-driven obfuscation.
        </p>

        {/* CTA Buttons */}
        <div
          ref={buttonsRef}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full max-w-md px-4"
        >
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto h-12 px-7 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-xs uppercase tracking-widest transition-all duration-300 shadow-[0_0_30px_rgba(59,156,255,0.5)] hover:scale-105 active:scale-95 flex items-center justify-center gap-2 border border-primary/40"
          >
            <Link to="/scripts">
              <Play className="h-4 w-4 fill-current" />
              <span>Launch Script Studio</span>
            </Link>
          </Button>

          <Button
            asChild
            size="lg"
            variant="outline"
            className="w-full sm:w-auto h-12 px-7 rounded-full border-white/20 bg-white/[0.04] hover:bg-white/[0.1] text-xs font-bold text-zinc-200 hover:text-white uppercase tracking-widest transition-all duration-300 backdrop-blur-md hover:scale-105 active:scale-95 flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,0,0,0.5)]"
          >
            <Link to="/results">
              <FileText className="h-4 w-4 text-primary" />
              <span>Inspect Forensics Log</span>
            </Link>
          </Button>
        </div>

        {/* Architecture Metric Markers */}
        <div className="mt-14 md:mt-16 pt-8 border-t border-white/10 w-full max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-[10px] uppercase font-mono text-zinc-400">Obfuscation Pass</div>
            <div className="text-base font-bold text-white font-mono mt-0.5 flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-primary" /> Polymorphic JIT
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-[10px] uppercase font-mono text-zinc-400">Agent Fleet Sync</div>
            <div className="text-base font-bold text-white font-mono mt-0.5 flex items-center gap-1.5">
              <Wifi className="h-3.5 w-3.5 text-success" /> {online} / {agents.length} Online
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-[10px] uppercase font-mono text-zinc-400">Audit Dossiers</div>
            <div className="text-base font-bold text-white font-mono mt-0.5 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-yellow-400" /> Court-Ready
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="text-[10px] uppercase font-mono text-zinc-400">Security Standard</div>
            <div className="text-base font-bold text-white font-mono mt-0.5 flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-primary" /> ISO 27001 / SOC 2
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 2. BACKGROUND & DETECTION PARADIGM SECTION */}
      {/* ======================================================== */}
      <section className="relative w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-start">
          {/* Left Column: Background & Narrative */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div>
              {/* Pre-header badge with dash */}
              <div className="flex items-center gap-2.5 text-xs font-mono font-bold tracking-[0.2em] text-primary uppercase mb-4">
                <span className="w-5 h-[2px] bg-primary rounded-full inline-block shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                <span>BACKGROUND</span>
              </div>

              {/* Main Heading */}
              <h2 className="text-3xl sm:text-4xl lg:text-4xl font-bold tracking-tight text-white mb-6 leading-[1.2]">
                The Detection Paradigm Is Broken
              </h2>

              {/* Narrative Paragraphs */}
              <div className="space-y-4 text-sm sm:text-base text-zinc-300/90 font-normal leading-relaxed">
                <p>
                  Modern antivirus solutions restrict proprietary software through behavioral heuristics, static signature matching, standard compiler artifacts (MSVC/GCC), typical API call sequences, and kernel-level monitoring — intercepting activities at multiple layers.
                </p>
                <p>
                  A significant paradigm shift emerges when programmers adopt sophisticated CI/CD practices. Each deployment iteration automatically passes through integrated obfuscators, encryption routines, and polymorphic engines — ensuring every instance possesses unique hashes, modified entry points, and altered import tables.
                </p>
                <p>
                  PROTEUS was built to operate precisely at this frontier: leveraging a language-independent intermediate representation that alters control-flow graphs, token generation, and binary structures to render signature-based detection ineffective.
                </p>
              </div>
            </div>

            {/* Pill Tags Matrix */}
            <div className="pt-4 flex flex-wrap gap-2.5 items-center">
              {[
                { label: "AV Bypass", tone: "emerald" },
                { label: "CI/CD Pipeline", tone: "emerald" },
                { label: "Polymorphic Engine", tone: "indigo" },
                { label: "BYOVD", tone: "indigo" },
                { label: "In-Memory Exec", tone: "emerald" },
                { label: "Domain Fronting", tone: "emerald" },
                { label: "SOCKS5", tone: "indigo" },
                { label: "Kernel Subversion", tone: "emerald" },
              ].map((tag) => (
                <span
                  key={tag.label}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold transition-all duration-300 border ${
                    tag.tone === "emerald"
                      ? "border-primary/30 bg-primary/10 text-primary hover:border-primary hover:bg-primary/15 shadow-[0_0_12px_rgba(59,156,255,0.1)]"
                      : "border-accent/30 bg-accent/10 text-accent hover:border-accent hover:bg-accent/15 shadow-[0_0_12px_rgba(124,92,255,0.1)]"
                  }`}
                >
                  {tag.label}
                </span>
              ))}
            </div>
          </div>

          {/* Right Column: 4 Stat / Feature Cards */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            {/* Card 1: 0% */}
            <div className="p-6 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/30 transition-all duration-300 backdrop-blur-md relative overflow-hidden group shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-primary tracking-tight mb-1.5 group-hover:text-glow">
                0%
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                Static signature match rate against PROTEUS-compiled artifacts
              </p>
            </div>

            {/* Card 2: Infinity */}
            <div className="p-6 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/30 transition-all duration-300 backdrop-blur-md relative overflow-hidden group shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-primary tracking-tight mb-1.5 group-hover:text-glow">
                ∞
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                Unique binary permutations per CI/CD deployment cycle
              </p>
            </div>

            {/* Card 3: 4+ */}
            <div className="p-6 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/30 transition-all duration-300 backdrop-blur-md relative overflow-hidden group shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-primary tracking-tight mb-1.5 group-hover:text-glow">
                4+
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                Distinct in-memory execution vectors supported simultaneously
              </p>
            </div>

            {/* Card 4: LLVM Frontend Badge Card */}
            <div className="p-6 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/30 transition-all duration-300 backdrop-blur-md relative overflow-hidden group shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
              <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono font-medium bg-primary/10 border border-primary/40 text-primary mb-3 shadow-[0_0_10px_rgba(59,156,255,0.2)]">
                LLVM Frontend
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                Language-independent IR alters basic control-flow graphs, token generation, and binary structures — rendering signature-based detection ineffective at the compiler level.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 3. CORE MODULES / FRAMEWORK CAPABILITIES */}
      {/* ======================================================== */}
      <section className="relative w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6">
        {/* Section Header */}
        <div className="mb-10 sm:mb-12">
          <div className="flex items-center gap-2.5 text-xs font-mono font-bold tracking-[0.2em] text-primary uppercase mb-3">
            <span className="w-5 h-[2px] bg-primary rounded-full inline-block shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
            <span>CORE MODULES</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-3">
            Framework Capabilities
          </h2>
          <p className="text-sm sm:text-base text-zinc-400 max-w-2xl leading-relaxed">
            Six integrated pillars that combine to form a complete detection-resistant forensic analysis platform.
          </p>
        </div>

        {/* 6 Grid Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Layers className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                Language-Independent IR
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                A custom LLVM frontend that alters control-flow graphs, token generation, and binary structures at compile time. Renders all signature-based detection completely ineffective before the binary is ever deployed.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              LLVM • CFG-Mutation • IR
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                Polymorphic CI/CD Pipeline
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                Every deployment iteration passes through integrated obfuscators, variable-encryption routines, and polymorphic engines. Each instance has unique hashes, modified entry points, and altered import tables.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              CI/CD • Polymorphism • Obfuscation
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Monitor className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                In-Memory Execution
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                Multiple fileless execution techniques running entirely within memory space of trusted processes. Supports process hollowing, reflective DLL injection, API unhooking, direct system calls, and thread hijacking.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              Fileless • DLL-Injection • Syscalls
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                Kernel-Level Subversion (BYOVD)
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                Detects and leverages legitimate or vulnerable third-party drivers to disable EDR callbacks and manipulate kernel structures directly — blinding security agents in both user and kernel space simultaneously.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              BYOVD • EDR-Bypass • Ring0
            </div>
          </div>

          {/* Card 5 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Activity className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                Multi-Vector Obfuscation
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                Combines custom encryption, anti-debugging stubs, timing-based evasion, and environment fingerprinting to produce a layered obfuscation stack that defeats static analysis and dynamic sandboxing.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              Encryption • Anti-Debug • Sandbox-Evasion
            </div>
          </div>

          {/* Card 6 */}
          <div className="p-7 rounded-2xl bg-card/90 border border-white/[0.08] hover:border-primary/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_32px_rgba(59,156,255,0.12)] hover:-translate-y-1">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300 shadow-[0_0_15px_rgba(59,156,255,0.2)]">
                <Globe className="h-6 w-6" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-white mb-3 group-hover:text-primary/80 transition-colors">
                Central Management Interface
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mb-6 font-normal">
                Simultaneously manages multiple system analysis targets. All traffic is routed through trusted CDN infrastructure using domain fronting or legitimate cloud APIs — invisible to network inspection tools.
              </p>
            </div>
            <div className="inline-flex items-center px-3 py-1.5 rounded-lg bg-black/40 border border-primary/20 text-primary font-mono text-[11px] tracking-wide self-start mt-auto">
              CDN • Domain-Fronting • SOCKS5
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 4. TECHNICAL REFERENCE / DEEP DIVE SECTION */}
      {/* ======================================================== */}
      <section className="relative w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6">
        {/* Section Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2.5 text-xs font-mono font-bold tracking-[0.2em] text-primary uppercase mb-3">
            <span className="w-5 h-[2px] bg-primary rounded-full inline-block shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
            <span>TECHNICAL REFERENCE</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-3">
            Deep Dive
          </h2>
          <p className="text-sm sm:text-base text-zinc-400 max-w-2xl leading-relaxed">
            Detailed breakdown of each technical pillar — how it works and what it achieves.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex items-center gap-6 border-b border-white/10 mb-8 overflow-x-auto no-scrollbar">
          {[
            { id: "ir", label: "IR & Compiler" },
            { id: "polymorphism", label: "Polymorphism" },
            { id: "memory", label: "In-Memory" },
            { id: "byovd", label: "BYOVD" },
            { id: "network", label: "Network" },
          ].map((tab) => {
            const isActive = activeDeepDiveTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() =>
                  setActiveDeepDiveTab(
                    tab.id as "ir" | "polymorphism" | "memory" | "byovd" | "network"
                  )
                }
                className={`pb-3.5 text-sm font-mono tracking-wide transition-all cursor-pointer relative whitespace-nowrap ${
                  isActive
                    ? "text-primary font-bold"
                    : "text-zinc-400 hover:text-zinc-200 font-medium"
                }`}
              >
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary shadow-[0_0_10px_rgba(16,185,129,0.8)] rounded-full" />
                )}
              </button>
            );
          })}
        </div>

        {/* Main Tab Content Card */}
        <div className="rounded-2xl bg-card/90 border border-white/[0.08] p-6 sm:p-8 lg:p-10 backdrop-blur-md shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-stretch">
            {/* Left Column: Descriptions & Bullets */}
            <div className="lg:col-span-6 flex flex-col justify-center space-y-6">
              {activeDeepDiveTab === "ir" && (
                <>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    Language-Independent IR (LLVM Frontend)
                  </h3>
                  <p className="text-sm sm:text-base text-zinc-300/90 leading-relaxed">
                    PROTEUS uses a custom LLVM frontend that intercepts the compilation pipeline at the intermediate representation stage — before any standard optimization passes or code generation. This allows systematic mutation of control-flow graphs and token streams.
                  </p>
                  <ul className="space-y-3 pt-2">
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Custom lexer and parser targeting PROTEUS syntax → LLVM IR lowering</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Automated CFG mutation pass: basic block reordering, opaque predicate injection</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Token stream randomization defeats source-level pattern matching</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Binary structure alteration renders all static signatures obsolete per build</span>
                    </li>
                  </ul>
                </>
              )}

              {activeDeepDiveTab === "polymorphism" && (
                <>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    Polymorphic CI/CD Pipeline
                  </h3>
                  <p className="text-sm sm:text-base text-zinc-300/90 leading-relaxed">
                    Rather than manually packing a binary, PROTEUS scripts pass through an automated delivery pipeline. Every iteration is unique — defeating file-reputation databases and hash-based detection without any manual intervention.
                  </p>
                  <ul className="space-y-3 pt-2">
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Per-build variable renaming, string encryption, and dead-code injection</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Import table shuffling and export address table patching</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Continuous hash uniqueness guaranteed across all deployment nodes</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Integrated with standard CI runners (GitHub Actions, GitLab CI)</span>
                    </li>
                  </ul>
                </>
              )}

              {activeDeepDiveTab === "memory" && (
                <>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    In-Memory Execution (Fileless)
                  </h3>
                  <p className="text-sm sm:text-base text-zinc-300/90 leading-relaxed">
                    PROTEUS executes secondary scripts entirely within the memory space of trusted host processes — no disk writes, no file system artifacts, no traditional AV scan surface.
                  </p>
                  <ul className="space-y-3 pt-2">
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Process Hollowing</span>
                        <span className="text-zinc-400"> — hollows a legitimate process and injects payload into its memory space</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Reflective DLL Injection</span>
                        <span className="text-zinc-400"> — maps a DLL from buffer in memory without using LoadLibrary</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">API Unhooking</span>
                        <span className="text-zinc-400"> — restores hooked NTDLL functions to original bytes at runtime</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Direct Syscalls</span>
                        <span className="text-zinc-400"> — bypasses usermode hooks by invoking syscall stubs directly</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Thread Hijacking</span>
                        <span className="text-zinc-400"> — redirects execution of an existing thread to payload entry</span>
                      </div>
                    </li>
                  </ul>
                </>
              )}

              {activeDeepDiveTab === "byovd" && (
                <>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    Kernel-Level Subversion (BYOVD)
                  </h3>
                  <p className="text-sm sm:text-base text-zinc-300/90 leading-relaxed">
                    BYOVD (Bring Your Own Vulnerable Driver) techniques allow PROTEUS to operate at Ring-0, disabling EDR callbacks and manipulating kernel structures to blind all security agents in the environment.
                  </p>
                  <ul className="space-y-3 pt-2">
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Automated enumeration of known-vulnerable signed drivers on target system</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Silent driver loading via undocumented NT kernel APIs</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>EDR PatchGuard bypass and ObRegisterCallbacks removal</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Kernel DKOM (Direct Kernel Object Manipulation) for process hiding</span>
                    </li>
                  </ul>
                </>
              )}

              {activeDeepDiveTab === "network" && (
                <>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    Covert Network Transport
                  </h3>
                  <p className="text-sm sm:text-base text-zinc-300/90 leading-relaxed">
                    All command-and-control traffic between the management interface and client endpoints is routed through trusted cloud infrastructure — appearing as legitimate CDN or API traffic to all network inspection tools.
                  </p>
                  <ul className="space-y-3 pt-2">
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Domain Fronting</span>
                        <span className="text-zinc-400"> — route through CDN hostnames to mask true C2 destination</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">Cloud API Tunneling</span>
                        <span className="text-zinc-400"> — embed traffic within legitimate cloud service API calls</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <div>
                        <span className="font-bold text-white">SOCKS5 Proxy</span>
                        <span className="text-zinc-400"> — establish persistent tunnels over encrypted channels</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-zinc-300">
                      <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5 shadow-[0_0_8px_rgba(59,156,255,0.7)]" />
                      <span>Traffic volume and timing shaping to defeat behavioral network detection</span>
                    </li>
                  </ul>
                </>
              )}
            </div>

            {/* Right Column: Code Mockup Window */}
            <div className="lg:col-span-6 flex flex-col">
              <div className="rounded-xl bg-card border border-white/[0.08] overflow-hidden flex flex-col h-full shadow-2xl">
                {/* Window Top Bar */}
                <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/80 inline-block" />
                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80 inline-block" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
                  </div>
                  <span className="font-mono text-[11px] text-primary/90 tracking-wider">
                    {activeDeepDiveTab === "ir" && "PROTEUS • IR Pass"}
                    {activeDeepDiveTab === "polymorphism" && "PROTEUS • Pipeline DSL"}
                    {activeDeepDiveTab === "memory" && "PROTEUS • Memory Module"}
                    {activeDeepDiveTab === "byovd" && "PROTEUS • Kernel Module"}
                    {activeDeepDiveTab === "network" && "PROTEUS • Network Module"}
                  </span>
                </div>

                {/* Code Window Content */}
                <div className="p-5 font-mono text-xs sm:text-[13px] leading-relaxed overflow-x-auto text-zinc-300 flex-1 flex flex-col justify-center">
                  {activeDeepDiveTab === "ir" && (
                    <div className="space-y-1">
                      <p className="text-zinc-500 italic mb-2">// PROTEUS IR -- CFG mutation pass example</p>
                      <p><span className="text-primary font-semibold">pass</span> <span className="text-primary font-semibold">cfg_mutate</span>(module: <span className="text-cyan-300">Module</span>) &#123;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">for</span> func <span className="text-primary font-semibold">in</span> module.<span className="text-primary">functions</span>() &#123;</p>
                      <p className="pl-8"><span className="text-primary font-semibold">let</span> blocks = func.<span className="text-primary">basic_blocks</span>();</p>
                      <p className="pl-8"><span className="text-primary font-semibold">for</span> bb <span className="text-primary font-semibold">in</span> blocks &#123;</p>
                      <p className="pl-12"><span className="text-primary">inject_opaque_pred</span>(bb, seed: <span className="text-primary">rand_u64</span>());</p>
                      <p className="pl-12"><span className="text-primary">reorder_instr</span>(bb, strategy: <span className="text-amber-300">"phi-safe"</span>);</p>
                      <p className="pl-8">&#125;</p>
                      <p className="pl-8">func.<span className="text-primary">mutate_entry</span>(entropy: <span className="text-primary">env_seed</span>());</p>
                      <p className="pl-4">&#125;</p>
                      <p>&#125;</p>
                    </div>
                  )}

                  {activeDeepDiveTab === "polymorphism" && (
                    <div className="space-y-1">
                      <p className="text-zinc-500 italic mb-2">// Polymorphic pipeline descriptor</p>
                      <p><span className="text-primary font-semibold">pipeline</span> <span className="text-primary font-semibold">deploy_agent</span> &#123;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">stage</span>(<span className="text-amber-300">"compile"</span>):</p>
                      <p className="pl-8"><span className="text-primary">proteus_build</span>(target: <span className="text-amber-300">"x86_64-windows"</span>)</p>
                      <p className="pl-4"><span className="text-primary font-semibold">stage</span>(<span className="text-amber-300">"obfuscate"</span>):</p>
                      <p className="pl-8"><span className="text-primary">encrypt_strings</span>(key: <span className="text-primary">derive_key</span>(env.<span className="text-amber-300">"BUILD_SEED"</span>))</p>
                      <p className="pl-8"><span className="text-primary">rename_symbols</span>(strategy: <span className="text-amber-300">"markov-chain"</span>)</p>
                      <p className="pl-8"><span className="text-primary">inject_dead_code</span>(blocks: <span className="text-purple-400">12</span>)</p>
                      <p className="pl-4"><span className="text-primary font-semibold">stage</span>(<span className="text-amber-300">"validate"</span>):</p>
                      <p className="pl-8"><span className="text-primary">assert_unique_hash</span>()</p>
                      <p className="pl-8"><span className="text-primary">assert_no_static_sig</span>(db: <span className="text-amber-300">"yara-rules-latest"</span>)</p>
                      <p>&#125;</p>
                    </div>
                  )}

                  {activeDeepDiveTab === "memory" && (
                    <div className="space-y-1">
                      <p className="text-zinc-500 italic mb-2">// Reflective loader -- PROTEUS stdlib</p>
                      <p><span className="text-primary font-semibold">use</span> proteus::mem::&#123;<span className="text-primary">alloc_rwx</span>, <span className="text-primary">write_payload</span>&#125;;</p>
                      <p><span className="text-primary font-semibold">use</span> proteus::process::&#123;<span className="text-primary">find_trusted</span>&#125;;</p>
                      <br />
                      <p><span className="text-primary font-semibold">fn</span> <span className="text-primary font-semibold">reflective_exec</span>(payload: &amp;[<span className="text-cyan-300">u8</span>]) &#123;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> host = <span className="text-primary">find_trusted</span>(name: <span className="text-amber-300">"svchost.exe"</span>);</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> region = host.<span className="text-primary">alloc_rwx</span>(size: payload.<span className="text-primary">len</span>());</p>
                      <p className="pl-4"><span className="text-primary">write_payload</span>(dst: region, src: payload);</p>
                      <p className="pl-4"><span className="text-primary">resolve_imports_peb</span>(region);</p>
                      <p className="pl-4"><span className="text-primary">transfer_execution</span>(entry: region);</p>
                      <p>&#125;</p>
                    </div>
                  )}

                  {activeDeepDiveTab === "byovd" && (
                    <div className="space-y-1">
                      <p className="text-zinc-500 italic mb-2">// BYOVD -- EDR callback removal</p>
                      <p><span className="text-primary font-semibold">use</span> proteus::kernel::&#123;<span className="text-primary">find_vulnerable_drv</span>, <span className="text-primary">load_ring0</span>&#125;;</p>
                      <br />
                      <p><span className="text-primary font-semibold">fn</span> <span className="text-primary font-semibold">disable_edr</span>() &#123;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> drv = <span className="text-primary">find_vulnerable_drv</span>()</p>
                      <p className="pl-8">.<span className="text-primary">expect</span>(<span className="text-amber-300">"No vulnerable driver found"</span>);</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> ctx = <span className="text-primary">load_ring0</span>(driver: drv);</p>
                      <p className="pl-4"><span className="text-primary font-semibold">for</span> cb <span className="text-primary font-semibold">in</span> ctx.<span className="text-primary">enumerate_callbacks</span>() &#123;</p>
                      <p className="pl-8"><span className="text-primary font-semibold">if</span> cb.<span className="text-primary">is_edr_origin</span>() &#123;</p>
                      <p className="pl-12">ctx.<span className="text-primary">patch_callback</span>(addr: cb.addr, value: <span className="text-purple-400">0x0</span>);</p>
                      <p className="pl-8">&#125;</p>
                      <p className="pl-4">&#125;</p>
                      <p>&#125;</p>
                    </div>
                  )}

                  {activeDeepDiveTab === "network" && (
                    <div className="space-y-1">
                      <p className="text-zinc-500 italic mb-2">// Domain fronting transport</p>
                      <p><span className="text-primary font-semibold">use</span> proteus::net::&#123;<span className="text-cyan-300">HttpClient</span>&#125;;</p>
                      <br />
                      <p><span className="text-primary font-semibold">fn</span> <span className="text-primary font-semibold">c2_connect</span>(real_host: &amp;<span className="text-cyan-300">str</span>, front: &amp;<span className="text-cyan-300">str</span>) &#123;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> client = <span className="text-cyan-300">HttpClient</span> &#123;</p>
                      <p className="pl-8">sni: front,        <span className="text-zinc-500 italic">// TLS SNI: trusted CDN</span></p>
                      <p className="pl-8">host: real_host,   <span className="text-zinc-500 italic">// HTTP Host: real C2</span></p>
                      <p className="pl-8">tls: <span className="text-amber-300">"TLS1.3"</span>,</p>
                      <p className="pl-4">&#125;;</p>
                      <p className="pl-4"><span className="text-primary font-semibold">let</span> tunnel = client.<span className="text-primary">open_socks5</span>(</p>
                      <p className="pl-8">bind: <span className="text-amber-300">"127.0.0.1:1080"</span>,</p>
                      <p className="pl-8">auth: <span className="text-primary">derive_creds</span>(env.<span className="text-amber-300">"SESSION_KEY"</span>),</p>
                      <p className="pl-4">);</p>
                      <p className="pl-4">tunnel.<span className="text-primary">shape_traffic</span>(jitter_ms: <span className="text-purple-400">250</span>);</p>
                      <p>&#125;</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 5. LIVE SYSTEM TELEMETRY & METRICS STRIP */}
      {/* ======================================================== */}
      <div className="space-y-6">
        {/* Status Strip */}
        <div className="panel p-5 flex flex-wrap items-center gap-4 bg-panel/80 border-white/10">
          <div className="flex items-center gap-2">
            <StatusDot status="online" />
            <span className="text-sm font-semibold text-foreground">All Systems Operational</span>
          </div>
          {error && <div className="text-sm text-destructive font-mono">{error}</div>}
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-primary" />
            <span className="text-foreground">Stealth Obfuscation</span>
            <Badge className="bg-success/15 text-success border-success/30 font-mono text-[10px]">
              ACTIVE
            </Badge>
          </div>
          <div className="h-4 w-px bg-white/10 hidden md:block" />
          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-muted-foreground">
            <span>Polymorphic Engine:</span>
            <span className="text-primary font-bold">a7f4c9…</span>
            <ChevronRight className="h-3 w-3" />
            <span className="text-primary font-bold">9e1b3d…</span>
          </div>
          <div className="ml-auto text-xs font-mono text-muted-foreground">
            Session Duration · <span className="text-foreground font-bold">42h 11m</span>
          </div>
        </div>

        {/* 4 Core Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          <MetricCard
            title="Total Agents"
            value={agents.length}
            delta="Reporting to grid"
            icon={Bot}
            tone="cyber"
          />
          <MetricCard
            title="Agents Online"
            value={online}
            delta="Live heartbeats"
            icon={Wifi}
            tone="success"
          />
          <MetricCard
            title="Active Operations"
            value={active}
            delta="Pending & running"
            icon={Radio}
            tone="warning"
          />
          <MetricCard
            title="Open Findings"
            value={results.length}
            delta="Encrypted telemetry"
            icon={AlertTriangle}
            tone="destructive"
          />
        </div>

        {/* Activity Chart & Findings Feed */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Chart */}
          <div className="panel p-6 xl:col-span-2 bg-panel/80 border-white/10">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Activity Telemetry — 24h</h3>
                <p className="text-xs text-muted-foreground">Operations and alerts per interval</p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-primary" />
                  Ops
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-destructive" />
                  Alerts
                </span>
              </div>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activity}>
                  <defs>
                    <linearGradient id="gOps" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gAlerts" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                  <XAxis dataKey="h" stroke="#94a3b8" fontSize={11} fontStyle="normal" />
                  <YAxis stroke="#94a3b8" fontSize={11} fontStyle="normal" />
                  <Tooltip
                    contentStyle={{
                      background: "#0a0f1d",
                      border: "1px solid rgba(255,255,255,0.15)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="ops"
                    stroke="#06b6d4"
                    fill="url(#gOps)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="alerts"
                    stroke="#ef4444"
                    fill="url(#gAlerts)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Latest Findings */}
          <div className="panel p-6 bg-panel/80 border-white/10">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Latest Findings</h3>
                <p className="text-xs text-muted-foreground">Newest alerts across the fleet</p>
              </div>
              <Link to="/results" className="text-xs text-primary font-mono hover:underline">
                View all →
              </Link>
            </div>
            <ul className="divide-y divide-white/10">
              {results.slice(0, 6).map((result) => (
                <li key={result.result_id} className="py-3.5 flex items-start gap-3">
                  <span className="shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-primary border-primary/30 bg-primary/10">
                    RESULT
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-foreground truncate">
                      Finding #{result.result_id.substring(0, 8)}
                    </div>
                    <div className="text-[11px] font-mono text-muted-foreground truncate">
                      Agent {result.agent_id} · Script {result.script_id}
                    </div>
                  </div>
                  <div className="text-[10px] font-mono text-muted-foreground whitespace-nowrap">
                    {new Date(result.submitted_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default Dashboard;
