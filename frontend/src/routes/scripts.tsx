import { createFileRoute } from "@tanstack/react-router";
import {
  FilePlus2,
  Play,
  Save,
  Layers,
  Terminal,
  Circle,
  ChevronRight,
  Copy,
  Check,
  Maximize2,
} from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiFetch, type Agent, type Script } from "@/lib/api";
import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/scripts")({
  head: () => ({
    meta: [
      { title: "Script Studio — Proteus" },
      { name: "description", content: "Author polymorphic forensic scripts in JQL — every deploy is uniquely polymorphed." },
      { property: "og:title", content: "Script Studio — Proteus" },
      { property: "og:description", content: "Build. Polymorph. Deploy." },
    ],
  }),
  component: ScriptsPage,
});

const DEFAULT_CODE = `# JQL — JOCKY Query Language
target: hosts where os == "windows"
stealth: on
polymorph: aes-256, xor-rot, dead-code-inject

scan memory {
  enum processes
  dump lsass if suspicious
  hash executables
}

scan registry {
  path HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
  diff since last_run
}

report -> relay.encrypted()
`;

function highlight(code: string): string {
  return code
    // Comments
    .replace(/(#.*)$/gm, '<span style="color:#687386;font-style:italic">$1</span>')
    // Keywords
    .replace(
      /\b(target|stealth|polymorph|scan|report|enum|dump|hash|path|diff|since|if|where)\b/g,
      '<span style="color:#3B9CFF;font-weight:600">$1</span>'
    )
    // Operators / arrows
    .replace(/(-&gt;|->)/g, '<span style="color:#7C5CFF;font-weight:700">-&gt;</span>')
    // Constants
    .replace(
      /\b(on|off|windows|linux|macos|aes-256|xor-rot|dead-code-inject)\b/g,
      '<span style="color:#FF7A3D">$1</span>'
    )
    // Strings
    .replace(/(["'])(.*?)\1/g, '<span style="color:#22C55E">$1$2$1</span>')
    // Braces
    .replace(/([{}])/g, '<span style="color:#A7B0C0">$1</span>')
    // Numbers
    .replace(/\b(\d+(\.\d+)?)\b/g, '<span style="color:#FF7A3D">$1</span>');
}

function ScriptsPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [progress, setProgress] = useState(0);
  const [deploying, setDeploying] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [scriptName, setScriptName] = useState("memory_sweep.jql");
  const [copied, setCopied] = useState(false);
  const [lineCount, setLineCount] = useState(DEFAULT_CODE.split("\n").length);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  useEffect(() => {
    apiFetch<Agent[]>("/agent/list").then((data) => {
      setAgents(data);
      setSelected(data.slice(0, 2).map((agent) => agent.agent_id));
    }).catch((error: Error) => toast.error(error.message));
  }, []);

  useEffect(() => {
    apiFetch<Script[]>("/script/list")
      .then(setScripts)
      .catch((error: Error) => toast.error(error.message));
  }, []);

  const deploy = async () => {
    if (deploying) return;
    setDeploying(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 90) { clearInterval(interval); return p; }
        return p + Math.random() * 12;
      });
    }, 180);
    try {
      await apiFetch("/script/deploy", {
        method: "POST",
        body: JSON.stringify({ name: scriptName, agent_ids: selected, code }),
      });
      clearInterval(interval);
      setProgress(100);
      toast.success(`Deployed to ${selected.length} agents.`);
    } catch (error) {
      clearInterval(interval);
      toast.error(error instanceof Error ? error.message : "Deployment failed");
    } finally {
      setDeploying(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setCode(val);
    setLineCount(val.split("\n").length);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = Array.from({ length: lineCount }, (_, i) => i + 1);

  return (
    <AppLayout
      title="Script Studio"
      subtitle="Compose forensic queries in JQL — every deploy is uniquely polymorphed per target host."
      actions={
        <>
          <Button variant="outline" className="border-border text-xs uppercase tracking-widest">
            <Save className="mr-2 h-4 w-4" />
            Save Draft
          </Button>
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber text-xs uppercase tracking-widest">
            <FilePlus2 className="mr-2 h-4 w-4" /> New Script
          </Button>
        </>
      }
    >
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-8">
        <div className="space-y-6">

          {/* ── Terminal Editor Card ── */}
          <div className="rounded-xl overflow-hidden border border-[#243044] shadow-[0_8px_40px_rgba(0,0,0,0.6)] bg-[#060A10]">

            {/* Window chrome bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#0A0E18] border-b border-[#1A2335]">
              {/* macOS dots */}
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#FF5F57] inline-block shadow-[0_0_6px_rgba(255,95,87,0.5)]" />
                <span className="w-3 h-3 rounded-full bg-[#FEBC2E] inline-block shadow-[0_0_6px_rgba(254,188,46,0.4)]" />
                <span className="w-3 h-3 rounded-full bg-[#28C840] inline-block shadow-[0_0_6px_rgba(40,200,64,0.4)]" />
              </div>

              {/* Centered filename tab */}
              <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-1 rounded-md bg-[#141E2D] border border-[#243044] text-[12px] font-mono text-[#A7B0C0]">
                <Terminal className="h-3.5 w-3.5 text-primary" />
                <span className="text-white/80">{scriptName}</span>
                <Badge className="bg-primary/10 text-primary border-primary/30 text-[9px] font-mono px-1.5 py-0 ml-1">JQL</Badge>
              </div>

              {/* Right actions */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="p-1.5 rounded hover:bg-white/5 text-[#687386] hover:text-white transition-colors"
                  title="Copy to clipboard"
                >
                  {copied
                    ? <Check className="h-3.5 w-3.5 text-green-400" />
                    : <Copy className="h-3.5 w-3.5" />
                  }
                </button>
                <button
                  type="button"
                  className="p-1.5 rounded hover:bg-white/5 text-[#687386] hover:text-white transition-colors"
                  title="Fullscreen"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Status bar below window chrome */}
            <div className="flex items-center gap-4 px-4 py-1.5 bg-[#080C14] border-b border-[#1A2335] text-[10px] font-mono text-[#687386]">
              <div className="flex items-center gap-1.5">
                <Circle className="h-2 w-2 fill-green-400 text-green-400" />
                <span>READY</span>
              </div>
              <span className="text-[#243044]">·</span>
              <span>PROTEUS JQL v2.4</span>
              <span className="text-[#243044]">·</span>
              <span>AES-256 + Polymorphic</span>
              <span className="ml-auto text-[#3B9CFF]">
                Ln {lineCount} · UTF-8
              </span>
            </div>

            {/* Editor body: line numbers + textarea */}
            <div className="flex relative min-h-[420px]" style={{ fontFamily: "'JetBrains Mono', 'Fira Code', ui-monospace, monospace" }}>
              {/* Line numbers gutter */}
              <div
                className="select-none shrink-0 text-right pr-4 pl-3 py-5 text-[12px] leading-6 text-[#364356] bg-[#060A10] border-r border-[#1A2335] min-w-[48px]"
                aria-hidden
              >
                {lines.map((n) => (
                  <div key={n} className="h-6">{n}</div>
                ))}
              </div>

              {/* Highlighted overlay (read-only, pointer-none) */}
              <pre
                aria-hidden
                className="pointer-events-none absolute left-[48px] right-0 top-0 bottom-0 whitespace-pre-wrap break-words p-5 pl-4 text-[13px] leading-6 text-[#A7B0C0] overflow-hidden"
                dangerouslySetInnerHTML={{ __html: highlight(code) + "\n" }}
              />

              {/* Actual editable textarea (text transparent, caret visible) */}
              <textarea
                ref={textareaRef}
                value={code}
                onChange={handleCodeChange}
                spellCheck={false}
                autoCorrect="off"
                autoCapitalize="off"
                className="relative flex-1 resize-none bg-transparent border-0 outline-none p-5 pl-4 text-[13px] leading-6 text-transparent caret-[#3B9CFF] font-[inherit] min-h-[420px]"
                style={{
                  caretColor: "#3B9CFF",
                  tabSize: 2,
                }}
              />
            </div>

            {/* Bottom info bar */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#0A0E18] border-t border-[#1A2335] text-[10px] font-mono text-[#687386]">
              <div className="flex items-center gap-3">
                <span>
                  Hash · <span className="text-primary">a7f4c9d1</span>
                </span>
                <span className="text-[#243044]">·</span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3 w-3 text-primary" />
                  Stealth: <span className="text-green-400 ml-1">ON</span>
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[#3B9CFF]">
                <ChevronRight className="h-3 w-3" />
                <span>JQL ready for polymorph injection</span>
              </div>
            </div>
          </div>

          {/* ── Script Metadata & Targets Panel ── */}
          <div className="panel p-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-widest text-[#A7B0C0]">Script Name</Label>
                <Input
                  value={scriptName}
                  onChange={(event) => setScriptName(event.target.value)}
                  className="bg-background border-border font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-widest text-[#A7B0C0]">Category</Label>
                <Input defaultValue="Memory · Persistence" className="bg-background border-border font-mono text-sm" />
              </div>
              <div className="md:col-span-2 space-y-2">
                <Label className="text-xs font-mono uppercase tracking-widest text-[#A7B0C0]">Description</Label>
                <Textarea
                  defaultValue="Enumerates running processes, hashes executables, and dumps LSASS if suspicious tokens are detected."
                  className="bg-background border-border text-sm"
                />
              </div>
            </div>

            <div className="mt-6">
              <div className="text-[11px] font-mono uppercase tracking-widest text-[#687386] mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block" />
                Target Agents ({selected.length} selected)
              </div>
              <div className="grid sm:grid-cols-2 gap-2">
                {agents.map((a) => (
                  <label
                    key={a.agent_id}
                    className="flex items-center gap-3 rounded-lg border border-border bg-background/40 p-3.5 cursor-pointer hover:border-primary/40 hover:bg-primary/5 transition-all"
                  >
                    <Checkbox
                      checked={selected.includes(a.agent_id)}
                      onCheckedChange={() => toggle(a.agent_id)}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-foreground truncate">{a.hostname ?? "Unknown host"}</div>
                      <div className="text-[11px] font-mono text-[#687386] truncate">{a.agent_id} · {a.os}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* ── Deploy Panel ── */}
          <div className="panel p-6 flex flex-col md:flex-row md:items-center gap-5 border-primary/20 bg-primary/[0.03]">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-foreground font-heading">Ready to deploy</div>
              <div className="text-xs text-[#A7B0C0] mt-0.5">
                {selected.length} targets · polymorphic hash rotates per host · AES-256 encrypted relay
              </div>
              {(deploying || progress === 100) && (
                <div className="mt-3 space-y-1">
                  <Progress value={progress} className="h-1" />
                  <div className="text-[11px] font-mono text-[#687386]">
                    {deploying
                      ? `Injecting… ${Math.round(progress)}%`
                      : `✓ Delivered · ${selected.length}/${selected.length} agents`}
                  </div>
                </div>
              )}
            </div>
            <Button
              onClick={deploy}
              disabled={deploying || selected.length === 0}
              className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber min-w-[180px] text-xs uppercase tracking-widest font-bold"
            >
              <Play className="mr-2 h-4 w-4 fill-current" />
              {deploying ? "Deploying…" : "Deploy Script"}
            </Button>
          </div>
        </div>

        {/* ── Sidebar: Template Library ── */}
        <aside className="panel p-5 self-start space-y-4">
          <div>
            <div className="text-xs font-mono font-bold uppercase tracking-[0.18em] text-foreground flex items-center gap-2 mb-1">
              <Terminal className="h-3.5 w-3.5 text-primary" />
              Templates
            </div>
            <div className="text-[11px] text-[#687386] font-mono">Battle-tested starting points</div>
          </div>

          <ul className="space-y-2">
            {scripts.length === 0 && (
              <li className="text-[11px] font-mono text-[#364356] italic px-1">No templates found on server.</li>
            )}
            {scripts.map((script) => (
              <li key={script.script_id}>
                <button className="w-full text-left rounded-lg border border-border bg-background/40 p-3 hover:border-primary/40 hover:bg-primary/5 transition-all group">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                      {script.name}
                    </div>
                    <Badge className="bg-panel border-border text-[9px] font-mono uppercase shrink-0">JQL</Badge>
                  </div>
                  <div className="text-[11px] font-mono text-[#687386] mt-1">
                    {new Date(script.created_at).toLocaleString()}
                  </div>
                </button>
              </li>
            ))}
          </ul>

          {/* Quick cheatsheet */}
          <div className="mt-4 pt-4 border-t border-border">
            <div className="text-[10px] font-mono uppercase tracking-widest text-[#687386] mb-2.5">JQL Reference</div>
            <div className="space-y-1.5 text-[11px] font-mono">
              {[
                { kw: "target:", desc: "host selector" },
                { kw: "stealth:", desc: "on | off" },
                { kw: "polymorph:", desc: "cipher list" },
                { kw: "scan memory", desc: "process sweep" },
                { kw: "scan registry", desc: "reg diff" },
                { kw: "report ->", desc: "encrypted relay" },
              ].map(({ kw, desc }) => (
                <div key={kw} className="flex items-baseline gap-2">
                  <span className="text-primary shrink-0">{kw}</span>
                  <span className="text-[#687386]">{desc}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </AppLayout>
  );
}
