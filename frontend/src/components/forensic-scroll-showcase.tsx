import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Shield,
  Radio,
  Cpu,
  Lock,
  Binary,
  Layers,
  Sparkles,
  Zap,
  CheckCircle2,
  FileCheck2,
  Network,
  Terminal,
  Activity,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const PILLARS = [
  {
    id: "01",
    tag: "STEALTH ENGINE",
    title: "Polymorphic Mutation & Zero Signature Footprint",
    desc: "Every deployed telemetry payload is compiled and randomized on the fly using our AST polymorphic engine, neutralizing static antivirus & EDR signature matches.",
    icon: Binary,
    stats: [
      { label: "Signature Variance", val: "100%" },
      { label: "Heuristic Evasion", val: "99.8%" },
    ],
    codeSnippet: `// Polymorphic IR Transformation
fn mutate_payload(stream: &mut ByteStream) {
  let entropy_key = crypto::random_256();
  obfuscator::shuffle_instruction_nodes(entropy_key);
  engine::jit_compile_native_arch();
}`,
  },
  {
    id: "02",
    tag: "AGENT ORCHESTRATION",
    title: "Multi-Arch Autonomous Endpoint Telemetry",
    desc: "Deploy low-latency agent binaries across Windows, Linux, and macOS ARM64/x86_64. Real-time heartbeat sync with encrypted Cloudflare edge relay grids.",
    icon: Network,
    stats: [
      { label: "Relay Latency", val: "< 18ms" },
      { label: "Arch Support", val: "Win / Lin / Mac" },
    ],
    codeSnippet: `// Agent Fleet Heartbeat Routine
type Agent struct {
  AgentID   string    \`json:"agent_id"\`
  Hostname  string    \`json:"hostname"\`
  OSArch    string    \`json:"arch"\` // arm64 / amd64
  Status    string    \`json:"status"\` // online
}`,
  },
  {
    id: "03",
    tag: "AUDIT & EVIDENCE",
    title: "Cryptographic Chain of Custody & Court-Ready Logs",
    desc: "Generate court-admissible forensic audit dossiers. Every registry key, process dump, and artifact is cryptographically hashed and sealed with zero-knowledge keys.",
    icon: FileCheck2,
    stats: [
      { label: "Standards", val: "ISO 27001 / SOC 2" },
      { label: "Integrity Hash", val: "SHA-256 Verified" },
    ],
    codeSnippet: `// Forensic Evidence Sealing
function sealEvidenceDossier(caseId, artifacts) {
  const hash = sha256(artifacts.serialize());
  return complianceVault.commitBlock({
    caseId,
    timestamp: Date.now(),
    digest: hash
  });
}`,
  },
];

export function ForensicScrollShowcase() {
  const containerRef = useRef<HTMLDivElement>(null);
  const leftColRef = useRef<HTMLDivElement>(null);
  const [activeIdx, setActiveIdx] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      // Create scroll-driven card transitions
      const cards = gsap.utils.toArray<HTMLElement>(".pillar-card");

      cards.forEach((card, i) => {
        ScrollTrigger.create({
          trigger: card,
          start: "top 60%",
          end: "bottom 40%",
          onEnter: () => setActiveIdx(i),
          onEnterBack: () => setActiveIdx(i),
        });

        gsap.fromTo(
          card,
          { opacity: 0.25, y: 40, scale: 0.96 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.8,
            ease: "power2.out",
            scrollTrigger: {
              trigger: card,
              start: "top 80%",
              end: "top 35%",
              scrub: 0.5,
            },
          }
        );
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const activePillar = (PILLARS[activeIdx] || PILLARS[0])!;

  return (
    <section ref={containerRef} className="relative w-full py-16 md:py-24 border-t border-b border-white/10 overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/3 left-1/4 w-[600px] h-[300px] bg-primary/5 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute bottom-10 right-1/4 w-[500px] h-[250px] bg-cyan-600/5 blur-[130px] pointer-events-none rounded-full" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-16 md:mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-mono uppercase tracking-widest text-primary mb-4">
            <Sparkles className="h-3 w-3" /> Core Forensic Architecture
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-white leading-[1.1]">
            Engineered for <span className="text-primary text-glow">Zero-Detection</span> & Courtroom Certainty
          </h2>
          <p className="mt-4 text-base text-muted-foreground leading-relaxed">
            Experience next-generation forensic orchestration built on dynamic mutation compilers, real-time edge relays, and compliance-sealed telemetry.
          </p>
        </div>

        {/* 2-Column Pinned Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-start">
          {/* Left Column: Sticky Telemetry Tracker */}
          <div ref={leftColRef} className="lg:col-span-5 lg:sticky lg:top-28 space-y-6">
            <div className="panel p-6 sm:p-8 border border-primary/25 glow-cyber relative overflow-hidden bg-[#0a0f1d]/90">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
                <div className="flex items-center gap-2 text-xs font-mono text-primary font-bold">
                  <Activity className="h-4 w-4 animate-pulse" />
                  <span>ARCHITECTURE TELEMETRY</span>
                </div>
                <Badge className="bg-primary/20 text-primary border-primary/30 font-mono text-[10px]">
                  STEP {activePillar.id} / 03
                </Badge>
              </div>

              <div className="space-y-4">
                <div className="text-[11px] font-mono uppercase tracking-widest text-primary font-bold">
                  {activePillar.tag}
                </div>
                <h3 className="text-xl sm:text-2xl font-black text-white leading-snug">
                  {activePillar.title}
                </h3>
                <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
                  {activePillar.desc}
                </p>
              </div>

              {/* Dynamic stats */}
              <div className="grid grid-cols-2 gap-3 mt-6 pt-6 border-t border-white/10">
                {activePillar.stats.map((s, idx) => (
                  <div key={idx} className="rounded-lg bg-black/40 border border-white/10 p-3">
                    <div className="text-[10px] uppercase font-mono text-zinc-400">{s.label}</div>
                    <div className="text-lg font-black text-primary font-mono mt-0.5">{s.val}</div>
                  </div>
                ))}
              </div>

              {/* Action */}
              <div className="mt-6 pt-4 flex items-center justify-between">
                <Button asChild size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-bold font-mono tracking-wider">
                  <Link to="/scripts">
                    EXPLORE SCRIPTS <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                  </Link>
                </Button>
                <span className="text-[10px] font-mono text-muted-foreground">SCROLL FOR DETAILS ↓</span>
              </div>
            </div>
          </div>

          {/* Right Column: Scrolling Cards */}
          <div className="lg:col-span-7 space-y-10 lg:space-y-16">
            {PILLARS.map((pillar, i) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.id}
                  className="pillar-card panel p-6 sm:p-8 border border-white/15 bg-panel/80 hover:border-primary/40 transition-all rounded-2xl relative"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-widest text-primary font-bold">
                          MODULE {pillar.id}
                        </span>
                        <h4 className="text-lg font-bold text-white leading-tight">
                          {pillar.tag}
                        </h4>
                      </div>
                    </div>
                    <Badge className="bg-white/5 border-white/15 text-zinc-400 font-mono text-[10px]">
                      ACTIVE
                    </Badge>
                  </div>

                  <p className="text-sm text-zinc-300 leading-relaxed mt-2">
                    {pillar.desc}
                  </p>

                  {/* Code snippet block */}
                  <div className="mt-5 rounded-xl bg-black/70 border border-white/10 p-4 font-mono text-xs overflow-x-auto text-zinc-300 leading-relaxed shadow-inner">
                    <pre className="text-cyan-400">
                      <code>{pillar.codeSnippet}</code>
                    </pre>
                  </div>

                  {/* Feature checklist */}
                  <div className="mt-5 grid sm:grid-cols-2 gap-2 text-xs text-zinc-400 font-mono">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3.5 w-3.5 text-success shrink-0" />
                      <span>Zero-signature compile pass</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-3.5 w-3.5 text-success shrink-0" />
                      <span>Hardware JIT acceleration</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export default ForensicScrollShowcase;
