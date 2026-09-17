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
  ArrowDownUp,
  Check,
  ChevronDown,
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
import { toast } from "sonner";
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
      { property: "og:title", content: "Proteus — Forensic Intelligence" },
      {
        property: "og:description",
        content: "Deep forensic system analysis through polymorphic execution.",
      },
    ],
  }),
  component: Dashboard,
});

/* ================================================================== */
/* Interactive Obfuscation & Deployment Glass Card                    */
/* ================================================================== */
function ObfuscationDispatchCard() {
  const [scriptName, setScriptName] = useState<string>("recon_beacon.go");
  const [targetArch, setTargetArch] = useState<"x86_64" | "arm64" | "win64">("x86_64");
  const [isDeploying, setIsDeploying] = useState(false);

  const handleDeploy = () => {
    setIsDeploying(true);
    setTimeout(() => {
      setIsDeploying(false);
      toast.success("Polymorphic Artifact Compiled", {
        description: `Deployed mutated ${scriptName} (${targetArch}) to grid with 0% signature rate.`,
      });
    }, 800);
  };

  return (
    <div className="w-full max-w-[340px] rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] p-5 sm:p-6 backdrop-blur-[20px] shadow-[0_20px_60px_rgba(0,0,0,0.45)] text-left relative z-20">
      {/* Top Input Block: SOURCE SCRIPT */}
      <div className="space-y-1.5 mb-2.5">
        <label className="text-[10px] font-mono tracking-wider text-[#9B9E9A] font-semibold uppercase">
          SOURCE SCRIPT
        </label>
        <div className="flex items-center justify-between gap-2">
          <input
            type="text"
            value={scriptName}
            onChange={(e) => setScriptName(e.target.value)}
            className="text-lg sm:text-xl font-mono font-bold text-[#F5F7F2] bg-transparent border-none outline-none w-full focus:ring-0 p-0"
            placeholder="script_name.go"
          />
          <div className="flex items-center gap-1.5 bg-white/[0.06] border border-white/[0.08] rounded-full px-2.5 py-1 shrink-0">
            <span className="text-[11px] font-semibold text-[#A855F7] font-mono">Go / LLVM</span>
          </div>
        </div>
      </div>

      {/* Permutation Mutation Divider */}
      <div className="relative my-3 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/[0.08]" />
        </div>
        <button
          type="button"
          onClick={() => {
            const nextArch = targetArch === "x86_64" ? "win64" : targetArch === "win64" ? "arm64" : "x86_64";
            setTargetArch(nextArch);
            toast.info(`Target Architecture: ${nextArch}`);
          }}
          className="relative h-7 w-7 rounded-full bg-[#1C1F24] border border-white/[0.12] flex items-center justify-center text-[#9B9E9A] hover:text-[#F5F7F2] hover:border-[#A855F7] hover:scale-110 active:scale-95 transition-all shadow-md cursor-pointer"
          title="Switch Target Architecture"
        >
          <ArrowDownUp className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Output Block: MUTATED ARTIFACT */}
      <div className="space-y-1.5 mb-4">
        <label className="text-[10px] font-mono tracking-wider text-[#9B9E9A] font-semibold uppercase">
          MUTATED ARTIFACT
        </label>
        <div className="flex items-center justify-between gap-2">
          <div className="text-base sm:text-lg font-mono font-bold text-[#F5F7F2] truncate">
            artifact_{targetArch}.bin
          </div>
          <div className="flex items-center gap-1.5 bg-white/[0.06] border border-white/[0.08] rounded-full px-2.5 py-1 shrink-0">
            <span className="text-[11px] font-mono font-semibold text-[#F5F7F2]">{targetArch}</span>
          </div>
        </div>
      </div>

      {/* Status & Entropy */}
      <div className="flex items-center justify-between text-[11px] font-mono text-[#9B9E9A] mb-5 pt-1.5 border-t border-white/[0.06]">
        <span>Entropy: 7.94 / 8.0</span>
        <span className="text-[#A855F7] font-semibold flex items-center gap-1">
          Zero Detection <Check className="h-3 w-3" />
        </span>
      </div>

      {/* Full Width Ultraviolet Submit Button */}
      <button
        type="button"
        onClick={handleDeploy}
        disabled={isDeploying}
        className="w-full py-3.5 px-5 rounded-full bg-[#A855F7] text-[#08090C] font-bold text-xs uppercase tracking-wider hover:bg-[#C084FC] hover:shadow-[0_0_35px_rgba(168,85,247,0.45)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg"
      >
        <span>{isDeploying ? "Mutating Binary..." : "Deploy to Fleet"}</span>
        <ArrowRight className="h-4 w-4 stroke-[2.5]" />
      </button>
    </div>
  );
}



/* ================================================================== */
/* Main Dashboard Page Component                                      */
/* ================================================================== */
function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState<string>();

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

    // Staggered entrance animation
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
          {/* Wallpaper Image */}
          <img
            src="/home-bg.png"
            alt="Ultraviolet Globe Network Wallpaper"
            className="w-full h-full object-cover object-[center_60%] scale-105 opacity-90 brightness-105 contrast-105"
          />
          {/* Atmospheric Gradient Overlays */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#08090C]/50 via-[#08090C]/20 to-[#08090C]/90" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_75%_45%_at_50%_0%,rgba(168,85,247,0.15)_0%,transparent_65%)]" />
        </div>
      }
    >
      {/* ======================================================== */}
      {/* 1. HERO SECTION                                          */}
      {/* ======================================================== */}
      <section
        ref={heroRef}
        className="relative pt-4 sm:pt-8 md:pt-12 pb-12 flex flex-col items-center justify-center text-center overflow-hidden"
      >
        {/* Top Pill Tag */}
        <div className="hero-badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#15171C]/70 border border-white/[0.08] text-xs font-mono tracking-widest text-[#F5F7F2] mb-6 md:mb-8 backdrop-blur-md shadow-md">
          <span className="h-2 w-2 rounded-full bg-[#A855F7] pulse-dot" />
          <span className="font-semibold uppercase text-[#A855F7]">NEXT-GENERATION FORENSIC FRAMEWORK</span>
        </div>

        {/* Main Hero Heading */}
        <h1
          ref={titleRef}
          className="text-6xl sm:text-8xl md:text-9xl lg:text-[9.5rem] font-black text-transparent bg-clip-text bg-gradient-to-b from-[#FFFFFF] via-[#F5F7F2] to-[#A855F7] drop-shadow-[0_0_60px_rgba(168,85,247,0.40)] font-heading uppercase tracking-[0.22em] select-none leading-none mb-6 md:mb-8"
        >
          JOCKY
        </h1>

        {/* Subtitle */}
        <p
          ref={subtitleRef}
          className="max-w-3xl text-base sm:text-lg md:text-xl leading-relaxed text-[#F1F5F9] font-medium px-4 sm:px-8 mb-8 md:mb-10 font-sans tracking-normal drop-shadow-[0_2px_16px_rgba(0,0,0,0.9)]"
        >
          A proprietary programming language framework engineered to exceed detection boundaries — enabling deep forensic system analysis through polymorphic execution, kernel-level subversion, and CI/CD-driven obfuscation.
        </p>

        {/* CTA Buttons */}
        <div
          ref={buttonsRef}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full max-w-md px-4 mb-10 z-30"
        >
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto h-12 px-7 rounded-full bg-[#A855F7] text-[#08090C] hover:bg-[#C084FC] font-bold text-xs uppercase tracking-widest transition-all duration-300 shadow-[0_0_35px_rgba(168,85,247,0.40)] hover:scale-105 active:scale-95 flex items-center justify-center gap-2 border border-[#A855F7]/40"
          >
            <Link to="/scripts">
              <Play className="h-4 w-4 fill-current" />
              <span>LAUNCH SCRIPT STUDIO</span>
            </Link>
          </Button>

          <Button
            asChild
            size="lg"
            variant="outline"
            className="w-full sm:w-auto h-12 px-7 rounded-full border-white/[0.08] bg-white/[0.06] hover:bg-white/10 text-xs font-bold text-[#F5F7F2] uppercase tracking-widest transition-all duration-300 backdrop-blur-md hover:scale-105 active:scale-95 flex items-center justify-center gap-2 shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
          >
            <Link to="/results">
              <FileText className="h-4 w-4 text-[#A855F7]" />
              <span>INSPECT FORENSICS LOG</span>
            </Link>
          </Button>
        </div>

        {/* 4 Architecture Metric Markers Under CTA */}
        <div className="w-full max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-4 text-left mb-12">
          <div className="p-4 rounded-2xl bg-[#15171C]/75 border border-white/[0.08] backdrop-blur-md shadow-md">
            <div className="text-[10px] uppercase font-mono text-[#9B9E9A]">OBFUSCATION PASS</div>
            <div className="text-sm sm:text-base font-bold text-[#F5F7F2] font-mono mt-1 flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-[#A855F7]" /> Polymorphic JIT
            </div>
          </div>
          <div className="p-4 rounded-2xl bg-[#15171C]/75 border border-white/[0.08] backdrop-blur-md shadow-md">
            <div className="text-[10px] uppercase font-mono text-[#9B9E9A]">AGENT FLEET SYNC</div>
            <div className="text-sm sm:text-base font-bold text-[#F5F7F2] font-mono mt-1 flex items-center gap-1.5">
              <Wifi className="h-3.5 w-3.5 text-[#A855F7]" /> {online} / {agents.length} Online
            </div>
          </div>
          <div className="p-4 rounded-2xl bg-[#15171C]/75 border border-white/[0.08] backdrop-blur-md shadow-md">
            <div className="text-[10px] uppercase font-mono text-[#9B9E9A]">AUDIT DOSSIERS</div>
            <div className="text-sm sm:text-base font-bold text-[#F5F7F2] font-mono mt-1 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-yellow-400" /> Court-Ready
            </div>
          </div>
          <div className="p-4 rounded-2xl bg-[#15171C]/75 border border-white/[0.08] backdrop-blur-md shadow-md">
            <div className="text-[10px] uppercase font-mono text-[#9B9E9A]">SECURITY STANDARD</div>
            <div className="text-sm sm:text-base font-bold text-[#F5F7F2] font-mono mt-1 flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-[#A855F7]" /> ISO 27001 / SOC 2
            </div>
          </div>
        </div>

        {/* Obfuscation & Dispatch Console */}
        <div className="w-full max-w-7xl px-2 sm:px-4 relative mb-6 flex justify-center">
          <ObfuscationDispatchCard />
        </div>
      </section>

      {/* ======================================================== */}
      {/* 2. BACKGROUND & DETECTION PARADIGM SECTION                */}
      {/* ======================================================== */}
      <section className="relative w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-start">
          {/* Left Column: Background & Narrative */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div>
              {/* Pre-header badge */}
              <div className="flex items-center gap-2.5 text-xs font-mono font-bold tracking-[0.2em] text-[#A855F7] uppercase mb-4">
                <span className="w-5 h-[2px] bg-[#A855F7] rounded-full inline-block shadow-[0_0_8px_rgba(168,85,247,0.7)]" />
                <span>BACKGROUND</span>
              </div>

              {/* Main Heading */}
              <h2 className="text-3xl sm:text-4xl lg:text-4xl font-bold tracking-tight text-[#F5F7F2] mb-6 leading-[1.2]">
                The Detection Paradigm Is Broken
              </h2>

              {/* Narrative Paragraphs */}
              <div className="space-y-4 text-sm sm:text-base text-[#9B9E9A] font-normal leading-relaxed">
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
                "AV Bypass",
                "CI/CD Pipeline",
                "Polymorphic Engine",
                "BYOVD",
                "In-Memory Exec",
                "Domain Fronting",
                "SOCKS5",
                "Kernel Subversion",
              ].map((tag) => (
                <span
                  key={tag}
                  className="px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold border border-white/[0.08] bg-[#15171C]/75 text-[#F5F7F2] hover:border-[#A855F7]/40 hover:text-[#A855F7] transition-all duration-300 shadow-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Right Column: 4 Stat Cards */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="p-6 rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] hover:border-[#A855F7]/30 transition-all duration-300 backdrop-blur-md shadow-[0_20px_60px_rgba(0,0,0,0.45)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-[#A855F7] tracking-tight mb-1.5">
                0%
              </div>
              <p className="text-xs sm:text-sm text-[#9B9E9A] leading-relaxed">
                Static signature match rate against PROTEUS-compiled artifacts
              </p>
            </div>

            <div className="p-6 rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] hover:border-[#A855F7]/30 transition-all duration-300 backdrop-blur-md shadow-[0_20px_60px_rgba(0,0,0,0.45)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-[#A855F7] tracking-tight mb-1.5">
                ∞
              </div>
              <p className="text-xs sm:text-sm text-[#9B9E9A] leading-relaxed">
                Unique binary permutations per CI/CD deployment cycle
              </p>
            </div>

            <div className="p-6 rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] hover:border-[#A855F7]/30 transition-all duration-300 backdrop-blur-md shadow-[0_20px_60px_rgba(0,0,0,0.45)]">
              <div className="text-3xl sm:text-4xl font-black font-mono text-[#A855F7] tracking-tight mb-1.5">
                4+
              </div>
              <p className="text-xs sm:text-sm text-[#9B9E9A] leading-relaxed">
                Distinct in-memory execution vectors supported simultaneously
              </p>
            </div>

            <div className="p-6 rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] hover:border-[#A855F7]/30 transition-all duration-300 backdrop-blur-md shadow-[0_20px_60px_rgba(0,0,0,0.45)]">
              <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono font-medium bg-[#A855F7]/10 border border-[#A855F7]/40 text-[#A855F7] mb-3">
                LLVM Frontend
              </div>
              <p className="text-xs sm:text-sm text-[#9B9E9A] leading-relaxed">
                Language-independent IR alters basic control-flow graphs, token generation, and binary structures — rendering signature-based detection ineffective at compile time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* 3. CORE MODULES / FRAMEWORK CAPABILITIES                 */}
      {/* ======================================================== */}
      <section className="relative w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6">
        <div className="mb-10 sm:mb-12">
          <div className="flex items-center gap-2.5 text-xs font-mono font-bold tracking-[0.2em] text-[#A855F7] uppercase mb-3">
            <span className="w-5 h-[2px] bg-[#A855F7] rounded-full inline-block shadow-[0_0_8px_rgba(168,85,247,0.7)]" />
            <span>CORE MODULES</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F7F2] mb-3">
            Framework Capabilities
          </h2>
          <p className="text-sm sm:text-base text-[#9B9E9A] max-w-2xl leading-relaxed">
            Six integrated pillars that combine to form a complete detection-resistant forensic analysis platform.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Layers,
              title: "Language-Independent IR",
              desc: "A custom LLVM frontend that alters control-flow graphs, token generation, and binary structures at compile time. Renders signature-based detection ineffective before binary deployment.",
              tag: "LLVM • CFG-Mutation • IR",
            },
            {
              icon: Cpu,
              title: "Polymorphic CI/CD Pipeline",
              desc: "Every deployment iteration automatically passes through integrated obfuscators, variable encryption routines, and polymorphic engines. Each instance has unique hashes and altered import tables.",
              tag: "CI/CD • Polymorphism • Obfuscation",
            },
            {
              icon: Monitor,
              title: "In-Memory Execution",
              desc: "Multiple fileless execution techniques running entirely within the memory space of trusted processes. Supports process hollowing, reflective DLL injection, and direct syscalls.",
              tag: "Fileless • DLL-Injection • Syscalls",
            },
            {
              icon: Shield,
              title: "Kernel-Level Subversion (BYOVD)",
              desc: "Detects and leverages legitimate or vulnerable third-party drivers to disable EDR callbacks and manipulate kernel structures directly — blinding security agents in user and kernel space.",
              tag: "BYOVD • EDR-Bypass • Ring0",
            },
            {
              icon: Activity,
              title: "Multi-Vector Obfuscation",
              desc: "Deep variable encryption, dead code injection, control flow flattening, and dynamic string decryption ensure disassemblers and decompilers produce fragmented, indecipherable control flows.",
              tag: "Encryption • Flattening • Junk Code",
            },
            {
              icon: Lock,
              title: "Anti-Forensic Evasion",
              desc: "Real-time detection of sandbox environments, debugger presence, hypervisors, and security hooks with automatic self-purging and zero artifact remnants left on the victim host.",
              tag: "Anti-Debug • Anti-VM • Self-Purge",
            },
          ].map((card, i) => (
            <div
              key={i}
              className="p-7 rounded-[20px] bg-[#15171C]/85 border border-white/[0.08] hover:border-[#A855F7]/40 transition-all duration-300 backdrop-blur-md flex flex-col justify-between group shadow-[0_20px_60px_rgba(0,0,0,0.45)] hover:-translate-y-1"
            >
              <div>
                <div className="w-12 h-12 rounded-2xl bg-[#A855F7]/10 border border-[#A855F7]/30 flex items-center justify-center text-[#A855F7] mb-6 group-hover:scale-110 transition-transform shadow-sm">
                  <card.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg sm:text-xl font-bold text-[#F5F7F2] mb-3 group-hover:text-[#A855F7] transition-colors">
                  {card.title}
                </h3>
                <p className="text-sm text-[#9B9E9A] leading-relaxed mb-6 font-normal">
                  {card.desc}
                </p>
              </div>
              <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-[#A855F7] font-mono text-[11px] tracking-wide self-start mt-auto">
                {card.tag}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ======================================================== */}
      {/* 4. LIVE TELEMETRY & SYSTEM METRICS STRIP                 */}
      {/* ======================================================== */}
      <section className="space-y-6 pt-4 pb-12 max-w-7xl mx-auto px-4 sm:px-6">
        {/* Status Strip */}
        <div className="panel p-5 flex flex-wrap items-center gap-4 bg-[#15171C]/85 border-white/[0.08] rounded-[18px]">
          <div className="flex items-center gap-2">
            <StatusDot status="online" />
            <span className="text-sm font-semibold text-[#F5F7F2]">All Systems Operational</span>
          </div>
          {error && <div className="text-sm text-destructive font-mono">{error}</div>}
          <div className="h-4 w-px bg-white/[0.08]" />
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-[#A855F7]" />
            <span className="text-[#9B9E9A]">Stealth Obfuscation</span>
            <Badge className="bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30 font-mono text-[10px]">
              ACTIVE
            </Badge>
          </div>
          <div className="h-4 w-px bg-white/[0.08] hidden md:block" />
          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-[#9B9E9A]">
            <span>Polymorphic Engine:</span>
            <span className="text-[#A855F7] font-bold">a7f4c9…</span>
            <ChevronRight className="h-3 w-3" />
            <span className="text-[#A855F7] font-bold">9e1b3d…</span>
          </div>
          <div className="ml-auto text-xs font-mono text-[#9B9E9A]">
            Session Duration · <span className="text-[#F5F7F2] font-bold">42h 11m</span>
          </div>
        </div>

        {/* 4 Core Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
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
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 sm:gap-8">
          {/* Chart */}
          <div className="panel p-6 xl:col-span-2 bg-[#15171C]/85 border-white/[0.08] rounded-[18px]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-[#F5F7F2]">Activity Telemetry — 24h</h3>
                <p className="text-xs text-[#9B9E9A]">Operations and alerts per interval</p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#A855F7]" />
                  Ops
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-cyan-400" />
                  Alerts
                </span>
              </div>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activity}>
                  <defs>
                    <linearGradient id="gOps" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#A855F7" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="#A855F7" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gAlerts" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#22D3EE" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#22D3EE" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                  <XAxis dataKey="h" stroke="#666A66" fontSize={11} fontStyle="normal" />
                  <YAxis stroke="#666A66" fontSize={11} fontStyle="normal" />
                  <Tooltip
                    contentStyle={{
                      background: "#15171C",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 12,
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="ops"
                    stroke="#A855F7"
                    fill="url(#gOps)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="alerts"
                    stroke="#22D3EE"
                    fill="url(#gAlerts)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Latest Findings */}
          <div className="panel p-6 bg-[#15171C]/85 border-white/[0.08] rounded-[18px]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-[#F5F7F2]">Latest Findings</h3>
                <p className="text-xs text-[#9B9E9A]">Newest alerts across the fleet</p>
              </div>
              <Link to="/results" className="text-xs text-[#A855F7] font-mono hover:underline">
                View all →
              </Link>
            </div>
            <ul className="divide-y divide-white/[0.08]">
              {results.slice(0, 5).map((result) => (
                <li key={result.result_id} className="py-3.5 flex items-start gap-3">
                  <span className="shrink-0 rounded-full border px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-wider text-[#A855F7] border-[#A855F7]/30 bg-[#A855F7]/10">
                    RESULT
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-[#F5F7F2] truncate">
                      Finding #{result.result_id.substring(0, 8)}
                    </div>
                    <div className="text-[11px] font-mono text-[#9B9E9A] truncate">
                      Agent {result.agent_id} · Script {result.script_id}
                    </div>
                  </div>
                  <div className="text-[10px] font-mono text-[#666A66] whitespace-nowrap">
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
      </section>
    </AppLayout>
  );
}

export default Dashboard;
